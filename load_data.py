import sqlite3
import pandas as pd


patients = pd.read_csv("data/patients.csv")
diagnoses = pd.read_csv("data/diagnoses.csv")
medications = pd.read_csv("data/medications.csv")


# cleaning dates and names
diagnoses["diagnosis"] = diagnoses["diagnosis"].str.strip().str.lower()
medications["medicine"] = medications["medicine"].str.strip().str.lower()
diagnoses["visit_date"] = pd.to_datetime(
    diagnoses["visit_date"]
).dt.strftime("%Y-%m-%d")


# removing duplicates
patients = patients.drop_duplicates("patient_id")
diagnoses = diagnoses.drop_duplicates()
medications = medications.drop_duplicates()


diagnoses = diagnoses[
    diagnoses["patient_id"].isin(patients["patient_id"])
]

medications = medications[
    medications["visit_id"].isin(diagnoses["visit_id"])
]


def combine_diagnoses(values):
    return ",".join(sorted(set(values)))


visits = (
    diagnoses
    .groupby(["visit_id", "patient_id", "visit_date"])["diagnosis"]
    .agg(combine_diagnoses)
    .reset_index()
    .rename(columns={"diagnosis": "diagnoses"})
)

visits = visits.merge(patients, on="patient_id")

# final data
final = visits.merge(medications, on="visit_id", how="left")

final = final[
    [
        "patient_id",
        "age",
        "gender",
        "visit_id",
        "visit_date",
        "diagnoses",
        "medicine",
    ]
]


con = sqlite3.connect("clinic.db")

con.executescript("""
DROP TABLE IF EXISTS patient_visits;

CREATE TABLE patient_visits (
    patient_id TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    gender TEXT NOT NULL CHECK (gender IN ('M', 'F')),
    visit_id TEXT NOT NULL,
    visit_date TEXT NOT NULL,
    diagnoses TEXT NOT NULL CHECK (diagnoses <> ''),
    medicine TEXT,
    UNIQUE (visit_id, medicine)
);
""")


final.to_sql(
    "patient_visits",
    con,
    if_exists="append",
    index=False
)

con.close()

print("Patients:", len(patients))
print("Visits:", len(visits))
print("Rows saved:", len(final))