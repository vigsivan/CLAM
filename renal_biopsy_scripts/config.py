from pathlib import Path

reports_sheet_path = Path("Reports/2016-2021 Kidney Tx Bx (deID).xlsx")
reports_sheet_cols_to_ignore = ("Raw Case Text", "Gender","Age at Procedure")
reports_sheet_patient_id = "Accession #"

slides_mapping_slide_id = "Slide #"

rejection_path = Path("Sheets/Rejection & Infection Cases.xlsx")
other_path = Path("Sheets/Other Cases.xlsx")
slides_paths = [
    Path("WSI/Anonymized Slides"),
    Path("WSI/Anonymized Slides #2"),
]