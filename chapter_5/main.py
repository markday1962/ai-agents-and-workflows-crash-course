import os
import sys

import keyring
from openai import OpenAI
from pydantic import BaseModel, Field
from pypdf import PdfReader
from pypdf.errors import PdfReadError

# Retrieve openai api key from the macOS Keychain
OPENAI_API_KEY = keyring.get_password("openai", "api_key")
if OPENAI_API_KEY is None:
    raise RuntimeError("No OpenAI key in keychain. Run: keyring set openai api_key")

# Openai client
client = OpenAI(api_key=OPENAI_API_KEY)


## Pydantic derived classes
class Hospital(BaseModel):
    name: str = Field(..., description="Name of hospital issuing the medical report")
    address: str = Field(
        ..., description="Address of hospital or clinic issuing the medical report"
    )
    physician: str = Field(..., description="Name of the attending physician or doctor")


class Patient(BaseModel):
    name: str = Field(..., description="Name of the patient")
    age: int = Field(..., description="Age of the patient")
    gender: str = Field(..., description="Gender of the patient")
    patient_id: str = Field(..., description="Unique patient id")


class MedicalReport(BaseModel):
    hospital: Hospital = Field(
        ..., description="Details of the hospital issuing the medical report"
    )
    patient: Patient = Field(..., description="Details of the patient in the report")
    report_date: str = Field(
        ..., description="Date of the diagnosis given in the medical report"
    )
    diagnosis: str = Field(..., description="Diagnosis given in the medical report")
    prescription: str = Field(
        ..., description="Medication or treatment prescribed in the medical report"
    )
    notes: str = Field(..., description="Any other notes in the medical report")


def get_pdf_content(pdf_path: str) -> str:
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        return "\n".join(page.extract_text() for page in reader.pages)


def summarise_pdf_content(text: str) -> str:
    pdf_content_prompt = f"""
        You are a professional document summariser.
        Summarise the following text extracted from a PDF document.
        Give a short overview, then the key points as a bulleted list.
        <text>
        {text}
        </text>
    """
    response = client.responses.create(
        model="gpt-4o-mini",
        input=pdf_content_prompt,
    )

    return response.output_text


def extract_report_details(pdf_content: str) -> MedicalReport:
    report_details_prompt = f"""
        You are a professional medical scribe
        Analyse the following medical report and extract structured information:
        hospital info, patient info, diagnosis, prescription and notes.
        <medical-report>
        {pdf_content}
        </medical-report>
        Return a valid JSON object
    """
    response = client.responses.parse(
        model="gpt-4o-mini",
        input=report_details_prompt,
        text_format=MedicalReport,
    )

    return response.output_parsed


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
