import os
import sqlite3
import sys
from datetime import date

import keyring
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
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
    report_date: date = Field(
        ...,
        description="Date of the diagnosis given in the medical report, as YYYY-MM-DD",
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


def create_database():
    conn = sqlite3.connect("medical_reports.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_reports (
            id INTEGER PRIMARY KEY,
            hospital_name TEXT,
            hospital_address TEXT,
            physician TEXT,
            patient_name TEXT,
            patient_age INTEGER,
            patient_gender TEXT,
            patient_id TEXT,
            report_date TEXT,
            diagnosis TEXT,
            prescription TEXT,
            notes TEXT
        )
    """)
    # The same report for the same patient can only be stored once
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS unique_report
        ON medical_reports (hospital_name, patient_id, report_date)
    """)
    conn.commit()
    return conn


def insert_report(conn: sqlite3.Connection, report: MedicalReport) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO medical_reports (
            hospital_name,
            hospital_address,
            physician,
            patient_name,
            patient_age,
            patient_gender,
            patient_id,
            report_date,
            diagnosis,
            prescription,
            notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report.hospital.name,
            report.hospital.address,
            report.hospital.physician,
            report.patient.name,
            report.patient.age,
            report.patient.gender,
            report.patient.patient_id,
            report.report_date.isoformat(),
            report.diagnosis,
            report.prescription,
            report.notes,
        ),
    )
    conn.commit()

    # No row is inserted when the report is already in the database
    return cursor.rowcount == 1


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

    try:
        print("Extracting medical report details")
        report = extract_report_details(pdf_content)
    except ValidationError as e:
        print(f"Error: The model returned invalid medical report details: {e}")
        return

    if report is None:
        print("Error: The model did not return the medical report details")
        return

    print("Creating database")
    conn = create_database()
    print("Inserting medical records")
    if insert_report(conn, report):
        print("Medical record saved")
    else:
        print("Medical record already exists, skipping")
    conn.close()


if __name__ == "__main__":
    main()
