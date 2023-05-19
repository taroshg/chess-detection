# installed imports
from torchvision.io import read_image
from torch.utils.data import Dataset
from torchvision import transforms
from torchvision.ops import box_convert
from torchvision.datasets import CocoDetection
from pycocotools.coco import COCO
from PIL import Image
import torch

# default imports
from typing import Any, List
import json
import os
import glob


class PieceDetectorDataset(Dataset):
    """
    Args:
        (str) root: directory with all the images
        (str) json_file: coco json file with boxes information
        (tuple) size: resize shape of the images
    """
    def __init__(self, root, json_file, size=(320, 320)):
        super().__init__()
        assert(json_file is not None), "json_file not provided for piece detector dataset"
        self.data_folder = root
        self.json_file = json_file
        self.data = json.load(open(json_file))
        self.w = size[0]
        self.h = size[1]
        self.tr = transforms.Compose([transforms.Resize(size), transforms.ToTensor()])
        self.classes = self.data['categories']
        self.coco = CocoDetection(root, json_file)
        print("Piece Detector Dataset initialized!")

    def __len__(self):
        return len(self.data["images"])

    def __getitem__(self, index: int):
        img, target = self.coco[index]
        h, w = img.size
        img = self.tr(img)
        if len(target) == 0:
            return img, {'boxes': torch.tensor([[[],[],[],[]]], dtype=torch.float), 'labels': torch.tensor([], dtype=torch.int64)}

        boxes = torch.tensor([t['bbox'] for t in target], dtype=torch.float)
        labels = torch.tensor([t['category_id'] for t in target], dtype=torch.int64)

        boxes[:, 0::2] *= (self.h / h)
        boxes[:, 1::2] *= (self.w / w)

        boxes = box_convert(boxes, 'xywh', 'xyxy')

        target = {'boxes': boxes, 'labels': labels}

        return img, target


class PieceDetectorCOGDataset(Dataset):
    """
    Args:
        (str) root: directory with all the images
        (str) json_file: coco json file with boxes information
        (tuple) size: resize shape of the images
    """
    def __init__(self, root, size=(320, 320)):
        super().__init__()
        self.root = root
        self.image_files = glob.glob1(root, '*.png')
        json_files = glob.glob1(root, '*.json')
        self.all_data = [json.load(open(os.path.join(root, j))) for j in json_files]
        self.h = size[1]
        self.w = size[0]
        self.tr = transforms.Compose([transforms.Resize(size), transforms.ToTensor()])
        self.classes = [{'name': 'none'}, {'name': 'P'}, {'name': 'N'}, {'name': 'B'}, {'name': 'R'},
                        {'name': 'Q'}, {'name': 'K'}, {'name': 'p'}, {'name': 'n'}, {'name': 'b'},
                        {'name': 'r'}, {'name': 'q'}, {'name': 'k'}]
        self.labels_dict = {'none': 0, 'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6,
                            'p': 7, 'n': 8, 'b': 9, 'r': 10, 'q': 11, 'k': 12}
        print("Piece COG Detector Dataset initialized!")

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, index: int):
        img = Image.open(os.path.join(self.root, self.image_files[index])).convert('RGB')
        data = self.all_data[index]
        h, w = img.size
        img = self.tr(img)

        labels = torch.tensor([self.labels_dict[d['piece']] for d in data['pieces']], dtype=torch.int64)
        boxes = torch.tensor([d['box'] for d in data['pieces']], dtype=torch.float)

        boxes[:, 0::2] *= (self.h / h)
        boxes[:, 1::2] *= (self.w / w)

        boxes = box_convert(boxes, 'xywh', 'xyxy')

        target = {'boxes': boxes, 'labels': labels}

        return img, target

