import sys
import os
import openslide
import torch
from tqdm import tqdm
from torch.utils.data import Dataset
from typing import Union, Callable, Optional, Dict, Any
from pathlib import Path
from statistics import mode, median

__all__ = ["SlidesDataset"]


class SlidesDataset(Dataset):
    """
    Slides Dataset.

    Parameters
    ----------
    root_dir: Union[Path, str]
    transform: Optional[Callable]
        Default=None
    """

    ALLOWED_EXTENSIONS = ["svs"]

    def __init__(
        self, root_dir: Union[Path, str], transform: Optional[Callable] = None
    ):
        self.transform = transform
        self.im_paths = {
            i.split(".")[0]: Path(root_dir) / i
            for i in os.listdir(str(root_dir))
            if i.split(".")[1] in self.ALLOWED_EXTENSIONS
        }
        self.paths = list(self.im_paths.values())
        self.summary_stats = None

    def __len__(self):
        return len(self.im_paths)

    def __getitem__(
        self, query: Union[int, str]
    ) -> Union[opesnlide.OpenSlide, torch.Tensor]:
        """
        Overload getitem to allow accessing slides by id
        """
        if isinstance(query, str):
            if query not in self.im_paths:
                raise KeyError(f"Slide id {query} not found")
            slide = openslide.OpenSlide(str(self.im_paths[query]))
        else:
            slide = openslide.OpenSlide(str(self.paths[query]))
        if self.transform is not None:
            slide = self.transform(slide)
        return slide

    def summarize(
        self, save_thumbnail_images: Optional[Union[Path, str]] = None
    ) -> Dict[str, Any]:
        """
        Gets summary information about the entire dataset.
        This function takes a while, ideally should be called only when exploring.

        Parameters
        ----------
        save_thumbnail_images: Optional[Union[Path, str]]
            If provided, it will save thumbnail image of each slide to this directory.
            Default=None
        """
        levels = []
        dimensions = []
        if not self.summary_stats:
            for s in tqdm(self):
                levels.append(s.level_count)
                dimensions.append(s.dimensions)
                if save_thumbnail_images:
                    if not os.path.exists(str(save_thumbnail_images)):
                        os.mkdir(str(save_thumbnail_images))
                    s.associated_images["thumbnail"].save(
                        str(
                            Path(save_thumbnail_images)
                            / s._filename.split("/")[-1].split(".")[0]
                        )
                        + ".png"
                    )

            self.summary_stats = {
                "num_levels": {
                    "mode": mode(levels),
                    "min": min(levels),
                    "max": max(levels),
                },
                "dimensions": {
                    "min_w": min([m[0] for m in dimensions]),
                    "max_w": max([m[0] for m in dimensions]),
                    "median_w": median([m[0] for m in dimensions]),
                    "min_h": min([m[1] for m in dimensions]),
                    "max_h": max([m[1] for m in dimensions]),
                    "median_h": median([m[1] for m in dimensions]),
                },
            }
        return self.summary_stats


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage {sys.argv[0]} <path_to_slides>")
        exit(0)
    dataset = SlidesDataset(sys.argv[1])
