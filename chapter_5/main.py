import os
import sys

import keyring
from openai import OpenAI
from pypdf import PdfReader
from pypdf.errors import PdfReadError

# Retrieve openai api key from the macOS Keychain
OPENAI_API_KEY = keyring.get_password("openai", "api_key")
if OPENAI_API_KEY is None:
    raise RuntimeError("No OpenAI key in keychain. Run: keyring set openai api_key")

# Openai client
client = OpenAI(api_key=OPENAI_API_KEY)


def get_pdf_content(pdf_path: str) -> str:
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        return "\n".join(page.extract_text() for page in reader.pages)


def summarise_pdf_content(text: str) -> str:
    prompt = f"""
        You are a professional document summariser.
        Summarise the following text extracted from a PDF document.
        Give a short overview, then the key points as a bulleted list.
        <text>
        {text}
        </text>
    """
    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
    )

    return response.output_text


def main():
    if len(sys.argv) != 2:
        print("Usage: ../venv/bin/python main.py /path/to/file.pdf")
        return

    file_path = sys.argv[1]

    if not os.path.isfile(file_path) or not file_path.lower().endswith(".pdf"):
        print("Error: Provide a valid PDF file")
        return

    try:
        print(f"Processing {file_path}")
        pdf_content = get_pdf_content(file_path)
    except (OSError, PdfReadError) as e:
        print(f"Error: Could not read {file_path}: {e}")
        return

    if not pdf_content.strip():
        print(f"Error: No text found in {file_path}")
        return

    print("Summarising the PDF content")
    summary = summarise_pdf_content(pdf_content)
    print(f"\n{summary}")


if __name__ == "__main__":
    main()
