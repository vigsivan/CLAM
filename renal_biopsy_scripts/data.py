import os
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial.distance import cdist
from tqdm import tqdm
import openslide
import typer

__all__ = ["PatchPairs"]

app = typer.Typer()

@app.command()
def generate_patch_pairs(
    slides_directory: Path,
    patches_directory: Path, 
    save_directory: Path,
    downsample: int = 64,
    maximim_similar_mm: float = 20.,
    minimum_dissimilar_mm: float = 100.,
    num_similar_per_slide: int = 32,
    num_dissimilar_per_slide: int = 32,
    auto_skip: bool = True,):

    MPP_PROPS = ['openslide.mpp-x', 'openslide.mpp-x']
    EXT = ".h5"
    COORDS = 'coords'

    os.makedirs(save_directory, exist_ok=True)

    for f in tqdm(os.listdir(patches_directory)):
        slide_id = f.split('.')[0]
        slide = openslide.OpenSlide(str(slides_directory/(slide_id+".svs")))
        save_file = save_directory / (slide_id + EXT)
        patches_file = patches_directory/(slide_id+EXT)

        if auto_skip and os.path.exists(save_file):
            continue

        if MPP_PROPS[0] not in slide.properties:
            raise Exception("I can't do my job without mpp!")

        microns_per_pixel_lvl0 = [float(slide.properties[i]) for i in MPP_PROPS]
        millimeters_per_pixel = max([(mpp*downsample)/1000 for mpp in microns_per_pixel_lvl0])

        patches = h5py.File(patches_file, mode='r')
        coords = patches[COORDS]

        distances = np.sqrt(2) * millimeters_per_pixel * cdist(coords, coords)
        similar = np.argwhere((distances < maximim_similar_mm) & (distances > 0) )
        dissimilar = np.argwhere(distances > minimum_dissimilar_mm)
        
        if len(similar) < num_similar_per_slide:
            raise Exception(f"Only found {len(similar)} similar out of {num_similar_per_slide}")

        if len(dissimilar) < num_dissimilar_per_slide:
            raise Exception(f"Only found {len(dissimilar)} dissimilar out of {num_dissimilar_per_slide}")
    
        with h5py.File(save_file, mode='w') as f:
            f.create_dataset("similar", data=similar)
            f.create_dataset("dissimilar", data=dissimilar)

if __name__ == "__main__":
    app()