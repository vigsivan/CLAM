"""
Generates a dataset.csv (for CLAM) for the multimodal renal pathology dataset.
"""
import os
from pathlib import Path

import pandas as pd
import typer

import config
from sheets import get_subject_slides_mapping, get_tables

CLAM_PATIENT_ID = "case_id"
CLAM_SLIDE_ID = "slice_id"

def main(multimodal_renal_directory: Path, output_csv_file: Path):

    # df_mapping maps subject id -> (multiple) slice ids and high-level info (diagnosis, patient info)
    # df_case_data maps subject id -> report information (raw text)

    df_mapping = process_mapping_sheets_as_df(multimodal_renal_directory)

    # TODO: merge case data by first extracting meaningful info from the raw reports
    # df_case_data = process_reports_sheet_as_df(multimodal_renal_directory)
    # df_merged = pd.merge(df_mapping, df_case_data, on=CLAM_PATIENT_ID)
    
    df_mapping.to_csv(output_csv_file, index=False)

def process_mapping_sheets_as_df(root_dir: Path):
    rejection_path = root_dir / config.rejection_path
    other_path = root_dir / config.other_path
    slides_paths = [root_dir / sp for sp in config.slides_paths]

    # We cannot rely on a complete dataset
    # So generate a list of slides that we can filter the dataframe with
    all_slides = os.listdir(slides_paths[0]) + os.listdir(slides_paths[1])
    all_slides_wo_ext = [sli.split(".")[0] for sli in all_slides]
    all_slides_set = set(all_slides_wo_ext)

    tables = get_tables(rejection_path, other_path)
    tcmr_slides, abmr_slides, non_rejection_slides = [tables[i+2] for i in range(3)]
    tcmr_map, abmr_map, nr_map = (get_subject_slides_mapping(tcmr_slides, "tcmr"),
                                get_subject_slides_mapping(abmr_slides, "abmr"),
                                get_subject_slides_mapping(non_rejection_slides, "other"))

    slide_rows = []
    stains = ('H&E', 'PAS', 'Trichrome')
    for mapping in (tcmr_map, abmr_map, nr_map):
        for accession, params in mapping.items():
            for stain in stains:
                if stain not in params:
                    continue
                if params[stain] in all_slides_set:
                    slide_rows.append({
                        CLAM_PATIENT_ID: accession,
                        CLAM_SLIDE_ID: params[stain],
                        "diagnosis": params["diagnosis"]
                    })
    
    df = pd.DataFrame(slide_rows)
    return df

def process_reports_sheet_as_df(root_dir: Path):
    reports_sheet = root_dir / config.reports_sheet_path
    pid = config.reports_sheet_patient_id

    df_case_data = pd.read_excel(reports_sheet, engine='openpyxl')
    change_format_pid = lambda row: "SP-".join(row[pid].split(":SP"))if ":" in row[pid] else row[pid]
    df_case_data[pid] = df_case_data.apply(lambda row: change_format_pid(row), axis=1)

    # FIXME: why does the following line not work?
    # return df_case_data.rename({pid: CLAM_PATIENT_ID})
    df_case_data[CLAM_PATIENT_ID] = df_case_data[pid]
    del df_case_data[pid]

    # TODO: need to actually get the data out
    return df_case_data

if __name__ == "__main__":
    typer.run(main)
