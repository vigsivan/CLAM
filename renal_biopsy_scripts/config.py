from pathlib import Path
from typing import Dict, Union, List

def get_multimodal_renal_dataset_directories(root: Path) -> Dict[str, Union[Path,List[Path]]]:
    return {
        "rejection_path" : root / "Sheets/Rejection & Infection Cases.xlsx",
        "other_path" : root / "Sheets/Other Cases.xlsx",
        # FIXME: I moved everything into a single slides folder
        # stupidly kept the structure the same in the code,
        # so will just keep this value as a return for now
        # until I have time to fix it
        "slides_folders":[ root / "WSI" "Anonymized Slides"] #/ [root / "WSI" / i for i in (, "Anonymized Slides #2")]
    }

CLAM_PATIENT_ID = "case_id"
CLAM_SLIDE_ID = "slide_id"
SLIDE_EXT = ".svs"
STAINS = ('H&E', 'PAS', 'Trichrome')