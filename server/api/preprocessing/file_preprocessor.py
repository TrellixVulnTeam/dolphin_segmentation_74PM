import os
import shutil
import tarfile
import uuid
import zipfile

from datetime import datetime
from decouple import config
from pathlib import Path

from api.services.file_select import FileType
from api.services.validation.file import check_valid_image

#zip | tar | dir | images

IMAGE_DIR = config('IMAGE_DIR', default = '/home/app/images')

def _add_preprocessing_metadata(data, path, files):
    current_time = datetime.now().strftime('%Y_%m_%d_%H_%M')
    return {
        "path": path,
        "name": f'{current_time}_{data["name"]}',
        "type": data["type"],
        "files": files,
        "data": data
    }

def preprocess_archive(data, extracted_path):
    extracted_path_files = os.listdir(extracted_path)
    if len(extracted_path_files) == 1 and os.path.isdir(f"{extracted_path}/{extracted_path_files[0]}"): 
        for file in Path(f"{extracted_path}/{extracted_path_files[0]}").glob("*"): shutil.move(str(file), extracted_path)

    files = []
    for file in Path(extracted_path).glob("*"):
        file = str(file)
        if check_valid_image(file): files.append(file)

    return _add_preprocessing_metadata(data, extracted_path, files)

def preprocess_zip(data):
    full_path = f"{IMAGE_DIR}/{data['files'][0]}"
    extracted_path = f"/tmp/{uuid.uuid4().hex}"
    with zipfile.ZipFile(full_path, 'r') as f: f.extractall(extracted_path)
    return preprocess_archive(data, extracted_path)

def preprocess_tar(data):
    full_path = f"{IMAGE_DIR}/{data['files'][0]}"
    extracted_path = f"/tmp/{uuid.uuid4().hex}"
    with tarfile.open(full_path, 'r') as f: f.extractall(extracted_path)
    return preprocess_archive(data, extracted_path)

def preprocess_dir(data):
    file_dir = data["files"][0]
    full_path = Path(f"{IMAGE_DIR}/{file_dir}")

    files = []
    for file in full_path.glob("*"):
        file = str(file)
        if check_valid_image(file): files.append(file)

    return _add_preprocessing_metadata(data, str(full_path), files)

def preprocess_images(data):
    return _add_preprocessing_metadata(data, IMAGE_DIR, data["files"])

class FilePreprocessor:
    def preprocess(self, data):
        if data["type"] == FileType.ZIP.value: return preprocess_zip(data)
        if data["type"] == FileType.TAR.value: return preprocess_tar(data)
        if data["type"] == FileType.DIR.value: return preprocess_dir(data)
        if data["type"] == FileType.IMAGES.value: return preprocess_images(data)
        raise NotImplementedError(f"FilePreprocessor does not support preprocessing of type: {data['type']}")