import sqlite3
from datetime import date
from typing import Literal, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


DB = "clinic.db"
app = FastAPI()


class Visit(BaseModel):
    patient_id: str = Field(min_length=1)
    age: int = Field(ge=0, le=120)
    gender: Literal["M", "F"]
    visit_id: str = Field(min_length=1)
    visit_date: date
    diagnoses: List[str] = Field(min_length=1)
    medicines: List[str]


@app.post("/visits", status_code=201)
def create_visit(visit: Visit):
    con = sqlite3.connect(DB)

    # Don't allow the same visit twice
    existing = con.execute(
        "SELECT 1 FROM patient_visits WHERE visit_id = ?",
        (visit.visit_id,)
    ).fetchone()

    if existing:
        con.close()
        raise HTTPException(
            status_code=409,
            detail="visit_id already exists"
        )

    diagnoses = ",".join(visit.diagnoses)
    medicines = visit.medicines or [None]

    try:
        for medicine in medicines:
            con.execute(
                "INSERT INTO patient_visits VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    visit.patient_id,
                    visit.age,
                    visit.gender,
                    visit.visit_id,
                    str(visit.visit_date),
                    diagnoses,
                    medicine,
                ),
            )

        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()

    return {
        "message": "visit saved",
        "visit_id": visit.visit_id,
    }


@app.get("/patients/{patient_id}/summary")
def patient_summary(patient_id: str):
    con = sqlite3.connect(DB)

    latest = con.execute(
        """
        SELECT visit_id, visit_date
        FROM patient_visits
        WHERE patient_id = ?
        ORDER BY visit_date DESC, visit_id DESC
        LIMIT 1
        """,
        (patient_id,),
    ).fetchone()

    if not latest:
        con.close()
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    visit_id, visit_date = latest

    medicine_count = con.execute(
        """
        SELECT COUNT(DISTINCT medicine)
        FROM patient_visits
        WHERE visit_id = ?
        """,
        (visit_id,),
    ).fetchone()[0]

    diagnoses = con.execute(
        "SELECT DISTINCT diagnoses FROM patient_visits WHERE patient_id = ?",
        (patient_id,),
    ).fetchall()

    con.close()

    all_diagnoses = set()

    for row in diagnoses:
        all_diagnoses.update(row[0].split(","))

    return {
        "patient_id": patient_id,
        "latest_visit_id": visit_id,
        "latest_visit_date": visit_date,
        "polypharmacy": medicine_count,
        "distinct_diagnosis_count": len(all_diagnoses),
    }