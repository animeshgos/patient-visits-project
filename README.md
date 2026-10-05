# Patient Visits Project

This project puts 3 csv files (patients, diagnoses, medications) into one sqlite table, adds a small FastAPI app on top, and does some analysis with pandas.

## Files

- load_data.py: cleans the csvs and builds the database (clinic.db)
- main.py: the FastAPI app
- analysis.ipynb: the pandas analysis
- requirements.txt: packages needed

## How to run

Put the 3 csv files in the same folder, then run these:

```
pip install -r requirements.txt
python load_data.py
uvicorn main:app --reload --port 8000
```

Open http://127.0.0.1:8000/docs to try the API. Then open analysis.ipynb and run all the cells.

You can run load_data.py many times. It deletes the table and builds it again, so nothing gets doubled.

## The table

There is one table called patient_visits. Each row is one visit and one medicine. If a visit has no medicines it gets one row with medicine as NULL. The diagnoses column holds all the diagnoses of the visit, sorted and separated by commas, and it repeats on every row of that visit.

## Data problems and what I did

- Extra spaces in diagnosis and medicine names (like "GERD "): removed them.
- Mixed capital letters (GERD, Gerd, gerd): made everything lowercase.
- Duplicate rows (some were hidden until the spaces and capitals were fixed): removed them after cleaning.
- Diagnoses for patient P099, who is not in patients.csv: dropped them because there is no age or gender.
- Medicines for visits V9001, V9002 and V9003, which are not in diagnoses.csv: dropped them because there is no patient or date.
- Dates were stored as text: changed them to real dates, then saved as YYYY-MM-DD text.

Things that were already fine: no missing values, ids look correct, gender is only M or F, ages are 20 to 81, and every visit has one patient and one date.

## API

- POST /visits saves a new visit. It returns 201 if saved, 409 if the visit_id already exists, and 422 if the input is wrong (bad gender, age not 0-120, bad date, empty diagnoses, missing field). All rows of a visit are saved together, so a visit is never half saved.
- GET /patients/{patient_id}/summary gives the latest visit, polypharmacy (number of different medicines in the latest visit) and the number of different diagnoses. It returns 404 if the patient is not found.

## Assumptions

- I dropped P099 instead of keeping it with empty age and gender, because keeping it would make the age and gender results wrong.
- The latest visit is the one with the newest date. If two visits have the same date, the bigger visit_id wins.
- Dates are text but still sort correctly in YYYY-MM-DD format.
- A diagnosis name with a comma would break the diagnoses column, since commas are the separator.
- The analysis only counts patients who have at least one visit in the table.
- One visit has many rows, so I counted distinct patients or distinct visits instead of counting rows.

## Analysis results

- Mean polypharmacy at the latest visit: 2.38
- Mean distinct diagnoses per patient: 2.6
- Top 5 diagnoses: viral fever, hypertension, migraine, type 2 diabetes, upper respiratory infection
- Top 5 medicines: paracetamol, vitamin d3, amlodipine, telmisartan, sumatriptan
- Bonus, % with polypharmacy of 5 or more at the latest visit: under 40 is 6.2%, 40-59 is 4.5%, 60+ is 18.2%
