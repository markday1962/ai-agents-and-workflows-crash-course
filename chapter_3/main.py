import sys

from openai import OpenAI
import keyring
import requests

## Retrieve openai api key from the macOS Keychain
OPENAI_API_KEY = keyring.get_password("openai", "api_key")
if OPENAI_API_KEY is None:
    raise RuntimeError("No OpenAI key in keychain. Run: keyring set openai api_key")

## Openai client
client = OpenAI(api_key=OPENAI_API_KEY)


def get_website_html(url: str) -> str:
    ## Default to https if the url has no scheme
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching the URL {url}: {e}")
        return ""

def run_agent(text: str) -> str:
    prompt = f"""
        You are a helpful assistant that summarises the content of a web page.
        Please summarise the main content of the following HTML:
        <text>
        {text}
        </text>
    """
    response = client.responses.create(
        model="gpt-4o",
        input=prompt,
    )

    return response.output_text


if __name__ == "__main__":
    website_url = input("Input a website URL: ").strip()
    if not website_url:
        print("No website URL entered, Exiting.")
        sys.exit(1)

    print(f"Fetching HTML from {website_url}")
    html = get_website_html(website_url)

    print(html)

    if not html:
        print(f"Unable to retrieve HTML content from {website_url}, Exiting.")
        sys.exit(1)

    result = run_agent(html)
    print("Result: \n", result)
