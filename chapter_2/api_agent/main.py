from openai import OpenAI
import keyring

## Retrieve openai api key from the macOS Keychain
OPENAI_API_KEY = keyring.get_password("openai", "api_key")
if OPENAI_API_KEY is None:
    raise RuntimeError("No OpenAI key in keychain. Run: keyring set openai api_key")

## Openai client
client = OpenAI(api_key=OPENAI_API_KEY)


def summarise_text(text: str) -> str:
    prompt = f"""
        You are a helpful assistant that summarises text from a tweet.
        Please summarise the following:
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
    usr_input = input("Enter text you want to summarise: ")
    summary = summarise_text(usr_input)
    print("Summary: \n", summary)
