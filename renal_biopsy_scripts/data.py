import os
import random
from pathlib import Path
from typing import Tuple

import h5py
import numpy as np
from scipy.spatial.distance import cdist
from torch.utils.data import Dataset
import torch
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
    auto_skip: bool = True):

    MPP_PROPS = ['openslide.mpp-x', 'openslide.mpp-x']
    EXT = ".h5"
    COORDS = 'coords'

    os.makedirs(save_directory, exist_ok=True)

    for slide_file in os.listdir(slides_directory):
        slide_id = slide_file.split('.')[0]
        slide = openslide.OpenSlide(str(slides_directory/slide_file))
        save_file = save_directory / (slide_id + EXT)

        if auto_skip and os.path.exists(save_file):
            continue

        if MPP_PROPS[0] not in slide.properties:
            raise Exception("I can't do my job without mpp!")

        microns_per_pixel_lvl0 = [float(slide.properties[i]) for i in MPP_PROPS]
        millimeters_per_pixel = max([(mpp*downsample)/1000 for mpp in microns_per_pixel_lvl0])

        patches = h5py.File(patches_directory/(slide_id+EXT), mode='r')
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

class PatchPairs(Dataset):
    def __init__(
        self,
        patches_directory: Path, 
        pairs_directory: Path,        
    ):
        self.patch_pairs = []
        self.pairs_directory = pairs_directory
        self.patches_directory = patches_directory

        for pair_file in os.listdir(pairs_directory):
            slide_id = pair_file.split('.')[0]
            with h5py.File(pairs_directory / pair_file, 'r') as f:
                for cat in ('similar', 'dissimilar'):
                    arr  = f[cat]
                    cat_items = [{
                        "slide_id": slide_id,
                        "category": cat,
                        "index": i
                    } for i in range(len(arr))]
                    self.patch_pairs.extend(cat_items)

    def __len__(self):
        return len(self.patch_pairs)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor]:
        # TODO
        patch_pair_info = self.patch_pairs[index]
        slide_id = patch_pair_info['slide_id']
        indexes_file = self.pairs_directory / (slide_id + ".h5")
        patches_file = self.patches_directory / (slide_id + ".h5")

        category = patch_pair_info['category'] # one of similar or dissimilar
        patch_index = patch_pair_info['index']
        with h5py.File(indexes_file, 'r') as f:
            indices: np.ndarray = f[category][patch_index]
        
        with h5py.File(patches_file, 'r') as f:
            p1, p2 = [f['patches'][indices[i]] for i in range(2)]

        return torch.from_numpy(p1), torch.from_numpy(p2)

if __name__ == "__main__":
    dataset = PatchPairs(
        Path("/media/vsivan/Untitled/CEYLON16_patches/patches/"),
        Path("/media/vsivan/Untitled/CEYLON16_patches/ssl")
    )
    print(len(dataset))
    patch_pairs = dataset[10]
    for p in patch_pairs:
        print(p.shape)
    # app()