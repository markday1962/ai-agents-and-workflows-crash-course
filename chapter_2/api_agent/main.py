from openai import OpenAI

## Required to read our .env file
from dotenv import load_dotenv
load_dotenv()

## Openai client
client = OpenAI() # No need to define apikey loads automatically


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
