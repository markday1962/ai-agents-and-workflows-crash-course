import sys

import ollama
import requests
from bs4 import BeautifulSoup


def ollama_prompt(prompt: str, model: str = "gemma3:1b") -> str:
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            # Ollama's default context is small and silently truncates long prompts
            options={"num_ctx": 32768},
        )
        return response["message"]["content"]
    except (ollama.ResponseError, ConnectionError) as e:
        print(f"Error calling Ollama: {e}")
        return ""


def get_website_html(url: str) -> str:
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
        Extract only the meaningful content of the following web page text.
        Do not include headers, footers, ads or navigation links.
        <text>
        {text}
        </text>
    """

    return ollama_prompt(prompt)


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

    return ollama_prompt(prompt)


def save_markdown_to_file(markdown_text: str, filename: str = "blog_post.md"):
    with open(filename, "w", encoding="utf8") as f:
        f.write(markdown_text)
    print(f"\nBlog post saved to: {filename}")


def main():
    website_url = input("Input a website URL: ").strip()
    if not website_url:
        print("No website URL entered, Exiting.")
        sys.exit(1)

    print(f"Fetching HTML from {website_url}")
    website_html = get_website_html(website_url)

    if not website_html:
        print(f"Unable to retrieve HTML content from {website_url}, Exiting.")
        sys.exit(1)

    core_content = extract_website_core_content(website_html)
    if not core_content:
        print("Unable to extract content from the website, Exiting.")
        sys.exit(1)

    blog_markdown = create_blog_post(core_content)
    if not blog_markdown:
        print("Unable to create the blog post, Exiting.")
        sys.exit(1)

    print(f"Result:\n{blog_markdown}")
    save_markdown_to_file(blog_markdown)


if __name__ == "__main__":
    main()
