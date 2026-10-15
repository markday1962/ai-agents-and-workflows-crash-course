import base64
import sys

import keyring
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# Pages with less visible text than this don't give the models enough to
# work with, so they invent the post instead
MIN_WEBSITE_TEXT_LENGTH = 500

# Retrieve openai api key from the macOS Keychain
OPENAI_API_KEY = keyring.get_password("openai", "api_key")
if OPENAI_API_KEY is None:
    raise RuntimeError("No OpenAI key in keychain. Run: keyring set openai api_key")

# Openai client
client = OpenAI(api_key=OPENAI_API_KEY)


def get_website_text(url: str) -> str:
    # Default to https if the url has no scheme
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching the URL {url}: {e}")
        return ""

    # Strip scripts, styles and inline svgs, then keep only the visible text
    # so the page fits the model's context
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "svg"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def extract_website_core_content(text: str) -> str:
    prompt = f"""
        You are a professional content extractor.
        Extract only the meaningful content of the following website text.
        Do not include headers, footers, ads, navigation links or scripts.
        <text>
        {text}
        </text>
    """
    response = client.responses.create(
        model="gpt-4o",
        input=prompt,
    )

    return response.output_text


def create_blog_post(content: str) -> str:
    prompt = f"""
        You are a professional blog writer.
        Write a well structured blog post in markdown based on the following
        text content.

        <source>
        {content}
        </source>

        The blog post should include:
        - A clear and engaging title.
        - A short introduction.
        - 3-5 bullet points of key insights
        - A conclusion that wraps up the topic

        Use markdown formatting appropriately
        (e.g. # For title, ## for subheadings, * for bullet points)
    """
    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
    )

    return response.output_text


def save_markdown_to_file(markdown_text: str, filename: str = "blog_post.md"):
    with open(filename, "w", encoding="utf8") as f:
        f.write(markdown_text)
    print(f"\n Blog post saved to: {filename}")


def summarise_for_thumbnail(article: str) -> str:
    prompt = f"""
        Summarise the following blog post in one or two sentences for an
        image generator. Describe the objects, materials and setting the
        post is about, not the people. Only use details from the post.
        <post>
        {article}
        </post>
    """
    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
    )

    return response.output_text.strip()


def generate_thumbnail_image(article: str, filename: str = "thumbnail.png"):
    # Use the post's markdown title as the subject; the full post is too long
    # and the model tends to draw its text into the image
    title = next(
        (line[2:].strip() for line in article.splitlines() if line.startswith("# ")),
        article[:200],
    )
    summary = summarise_for_thumbnail(article)

    print("Generating thumbnail image...")
    response = client.images.generate(
        model="gpt-image-1",
        prompt=(
            f"A thumbnail image for a blog post titled: {title}. "
            f"The post is about: {summary} "
            "Do not include any people, text or lettering in the image."
        ),
        size="1024x1024",
        n=1,
    )

    # gpt-image models return the image as base64 rather than a url
    image_data = base64.b64decode(response.data[0].b64_json)
    with open(filename, "wb") as f:
        f.write(image_data)

    print(f"Thumbnail image saved to: {filename}")


def main():
    website_url = input("Input a website URL: ").strip()
    if not website_url:
        print("No website URL entered, Exiting.")
        sys.exit(1)

    print(f"Fetching text from {website_url}")
    website_text = get_website_text(website_url)

    if not website_text:
        print(f"Unable to retrieve text content from {website_url}, Exiting.")
        sys.exit(1)

    if len(website_text) < MIN_WEBSITE_TEXT_LENGTH:
        print(
            f"Only {len(website_text)} characters of text found on {website_url}, "
            "not enough to write a blog post from. Try a page with more text, Exiting."
        )
        sys.exit(1)

    core_content = extract_website_core_content(website_text)
    blog_markdown = create_blog_post(core_content)
    save_markdown_to_file(blog_markdown)
    generate_thumbnail_image(blog_markdown)


if __name__ == "__main__":
    main()
