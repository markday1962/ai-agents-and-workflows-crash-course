import requests
import keyring

## Retrieve openai api key from the macOS Keychain
OPENAI_API_KEY = keyring.get_password("openai", "api_key")
if OPENAI_API_KEY is None:
    raise RuntimeError("No OpenAI key in keychain. Run: keyring set openai api_key")

## We load this first
url = "https://api.openai.com/v1/responses"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}",
}


def summarise_text(text: str) -> str:
    prompt = f"""
        You are a helpful assistant that summarises text from a tweet.
        Please summarise the following:
        <text>
        {text}
        </text>
    """
    payload = {"model": "gpt-4o", "input": prompt}

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()

    ## Find the message item (reasoning models put a reasoning item first)
    for item in response.json()["output"]:
        if item["type"] == "message":
            return item["content"][0]["text"]
    raise RuntimeError("No message in response")


if __name__ == "__main__":
    usr_input = input("Enter text you want to summarise: ")
    summary = summarise_text(usr_input)
    print("Summary: \n", summary)
