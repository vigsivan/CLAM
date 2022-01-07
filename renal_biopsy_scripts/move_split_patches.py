import os
from pathlib import Path
import typer

def main(
    patches_directory: Path,
    splits_directory: Path,
):
    split_slides = {}
    folders = ("patches", "masks", "stitches")
    extensions = (".h5", ".jpg", ".jpg")
    patches_dir = patches_directory / folders[0]

    for split in ("train", "test"):
        slides_file = splits_directory / split / "slides.txt"
        all_slides = []
        with open(slides_file, "r") as f:
            all_slides = [i.strip() for i in f.readlines()]
        for slide in all_slides:
            split_slides[slide] = split
        for folder in folders:
            os.makedirs(splits_directory / split / folder, exist_ok=True)
    
    for slide_file in os.listdir(patches_dir):
        slide_id = slide_file.split('.')[0]
        # NOTE: this condition is here because we have some slides
        # for which we have no data (i.e., there is no corresponding subject)
        if slide_id not in split_slides:
            continue
        split = split_slides[slide_id]
        for folder, ext in zip(folders, extensions):
            fname = (slide_id + ext)
            src = patches_directory / folder / fname
            dest = splits_directory / split / folder / fname
            os.rename(src, dest)

if __name__ == "__main__":
    # main(
    #     Path("/media/vsivan/Untitled/multimodal_renal/WSI/patches_fp"),
    #     Path("/media/vsivan/Untitled/multimodal_renal/split_25/")
    # )
    typer.run(main)