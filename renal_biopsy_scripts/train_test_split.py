import math
import os
import random
from pathlib import Path
from typing import Dict, List, Union, Tuple

import numpy as np
import pandas as pd
import typer

from sheets import get_subject_slides_mapping, get_tables

CLAM_PATIENT_ID = "case_id"
CLAM_SLIDE_ID = "slide_id"
SLIDE_EXT = ".svs"
STAINS = ('H&E', 'PAS', 'Trichrome')

Mapping = Dict[str, Dict[str,str]]

# parameters
root: Path = Path("/media/vsivan/Untitled/multimodal_renal")

def write_list_to_file(filename: Path, li: List[str]):
    """Writes a list to a file

    Parameters
    ----------
    filename : Path
    li : List[str]
    """
    with open(filename, "w") as f:
        for i in li:
            f.write(f"{i}\n")

def main(root: Path, output_dir: Path, test_pct: float=.25, random_seed: int=42):
    """Splits the data into training and test data.

    This script will create the following files and directories:

    OUTDIR/
        + train/
            + train_dataset.csv
            + train_slides.txt
            + train_subjects.txt
        + test/
            + test_dataset.csv
            + test_slides.txt
            + test_subjects.txt

    Parameters
    ----------
    root : Path
        The root multimodal_renal directory
    output_dir : Path
        The directory in which to store the split information
    test_pct : float, optional
        Amount of data to store in test, by default .25
    random_seed : int, optional
        by default 42
    """
    random.seed(random_seed)
    np.random.seed(random_seed)
    mapping, all_slides = get_mapping_and_slides(root)
    df = get_diagnosis_df(mapping, all_slides)
    df_train, df_test = split_df_by_group(df, group="diagnosis", test_pct=test_pct)

    for split, df_split in zip(("train", "test"), (df_train, df_test)):
        split_dir = output_dir/split
        os.makedirs(split_dir, exist_ok=True)
        
        split_slides = df_split[CLAM_SLIDE_ID].tolist()
        split_subjects = df_split[CLAM_PATIENT_ID].unique().tolist()

        write_list_to_file(split_dir/"slides.txt", split_slides)
        write_list_to_file(split_dir/"subjects.txt", split_subjects)

        df_split.to_csv(split_dir/"data.csv", index=False)


def get_multimodal_renal_dataset_directories(root: Path) -> Dict[str, Union[Path,List[Path]]]:
    return {
        "rejection_path" : root / "Sheets/Rejection & Infection Cases.xlsx",
        "other_path" : root / "Sheets/Other Cases.xlsx",
        "slides_folders": [root / "WSI" / i for i in ("Anonymized Slides", "Anonymized Slides #2")]
    }


def get_mapping_and_slides(root) -> Tuple[Mapping, List[str]]:
    dirs = get_multimodal_renal_dataset_directories(root)

    all_slides = []
    for slide_folder in dirs["slides_folders"]:
        all_slides.extend([i.split('.')[0] for i in os.listdir(slide_folder)])

    # the first two tables do not contain any slide info
    # nr=no rejection
    _, _, tcmr_slides, abmr_slides, nr_slides = get_tables(dirs["rejection_path"], dirs["other_path"])
    tcmr_map, abmr_map, nr_map = (get_subject_slides_mapping(tcmr_slides, "tcmr"),
                                get_subject_slides_mapping(abmr_slides, "abmr"),
                                get_subject_slides_mapping(nr_slides, "other"))
    mapping = {**tcmr_map, **abmr_map, **nr_map}
    return mapping, all_slides

def get_diagnosis_df(mapping: Mapping, all_slides: List[str]) ->pd.DataFrame:
    slide_rows = []
    for accession, params in mapping.items():
        for stain in STAINS:
            if stain not in params:
                continue
            if params[stain] in all_slides:
                slide_rows.append({
                    CLAM_PATIENT_ID: accession,
                    CLAM_SLIDE_ID: params[stain]+SLIDE_EXT,
                    "diagnosis": params["diagnosis"]
                })
    df = pd.DataFrame(slide_rows)
    return df

def split_df_by_group(df: pd.DataFrame, group: str, test_pct: float) -> Tuple[pd.DataFrame, pd.DataFrame]: 
    subjects_by_group = df.groupby(group)[CLAM_PATIENT_ID].apply(lambda x: np.unique(x))
    train_subjects, test_subjects = [], []
    groups = subjects_by_group.index.tolist()
    for group in groups:
        subjects_group = (subjects_by_group[group])
        np.random.shuffle(subjects_group)
        test_amount = math.ceil(len(subjects_group) * test_pct)
        test_subjects.extend(subjects_group[:test_amount])
        train_subjects.extend(subjects_group[test_amount:])

    df_train = df[df[CLAM_PATIENT_ID].isin(train_subjects)]
    df_test = df[df[CLAM_PATIENT_ID].isin(test_subjects)]

    return df_train, df_test

if __name__ == "__main__":
    typer.run(main)