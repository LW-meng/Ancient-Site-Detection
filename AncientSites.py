from __future__ import print_function, division
import torch
import torch.nn as nn
import torchvision
from torchvision import datasets, models, transforms
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from skimage import io
import pandas as pd
import numpy as np
import os
from tqdm import tqdm

import warnings

warnings.filterwarnings("ignore")


class SitesDataset(Dataset):

    def __init__(self, coordinate_txt, root_dir='', transform=None):
        self.info = pd.read_csv(coordinate_txt, sep='\t')
        # root where you put the train folder
        self.root_dir = [os.path.join(root_dir, i) for i in self.info.iloc[:, 5]]

        self.labels = torch.tensor(self.info.iloc[:, 4] > 0)
        self.transform = transform

    def __len__(self):
        return len(self.info)

    def __getitem__(self, idx):
        img_dir = self.root_dir[idx]
        image = Image.open(img_dir)
        # for detection: 1/0
        # for detection on confidence level: 3/2/0
        label = self.labels[idx]

        if self.transform is not None:
            image = self.transform(image)

        return {'Image': image, 'label': label}
