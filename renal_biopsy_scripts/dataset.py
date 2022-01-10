import os
from pathlib import Path
from typing import Tuple

import h5py
from torch.utils.data import Dataset
import torch

__all__ = ["PatchPairs"]

class PatchPairs(Dataset):
    def __init__(
        self,
        patches_directory: Path, 
        pairs_directory: Path,        
    ):
        slide_ids = [i.split('.')[0] for i in os.listdir(pairs_directory)]
        buckets_to_slide = {}
        num_pairs = 0

        for slide_id in slide_ids:
            pairs_file = pairs_directory / (slide_id + ".h5")
            start = num_pairs
            with h5py.File(pairs_file, 'r') as f:
                try:
                    for label in ("similar", "dissimilar"):
                        num_pairs += len(f[label])
                except (KeyError, ValueError) as e:
                    print("Problem with ", pairs_file)
            stop = num_pairs
            buckets_to_slide[(start, stop)] = slide_id
        
        self.patches_directory = patches_directory
        self.pairs_directory = pairs_directory
        self.slide_ids = slide_ids
        self.buckets_to_slide = buckets_to_slide
        self.num_pairs = num_pairs

    def get_bucket_from_index(self, index):
        for (bmin, bmax) in self.buckets_to_slide.keys():
            if index > bmin and index < bmax:
                return (bmin, bmax)

    def __len__(self):
        return self.num_pairs

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor, str]:
        bucket = self.get_bucket_from_index(index)
        slide_id = self.buckets_to_slide[bucket]

        indexes_file = self.pairs_directory / (slide_id + ".h5")
        patches_file = self.patches_directory / (slide_id + ".h5")

        with h5py.File(indexes_file, 'r') as f:
            start = bucket[0]
            patch_index = index - start
            if patch_index < len(f["similar"]):
                label = "similar"
                indices = f["similar"][patch_index]
            else:
                label = "dissimilar"
                indices = f["dissimilar"][patch_index]
        
        with h5py.File(patches_file, 'r') as f:
            p1, p2 = [f['imgs'][indices[i]] for i in range(2)]

        return torch.from_numpy(p1), torch.from_numpy(p2), label
