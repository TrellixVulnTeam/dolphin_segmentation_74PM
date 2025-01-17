import os
import shutil
import tarfile
import zipfile
import subprocess
from pathlib import Path

from api.services.validation.archive import FileArchiveTask, FileArchiveType

class Archiver:
    def process(self, task, type, inFile, out):
        if task == FileArchiveTask.ARCHIVE.value: return self.archive(type, inFile, out)
        if task == FileArchiveTask.EXTRACT.value: return self.extract(type, inFile, out)
        raise NotImplementedError(f"Task has not been implemented: {task}")

    def archive(self, type, inFile, out):
        Path(Path(out).parent).mkdir(parents = True, exist_ok = True)

        if type == FileArchiveType.TAR.value:
            os.chdir(Path(inFile).parent)
            subprocess.call(['tar', '-czf', out, Path(inFile).name])
            return True            

        if type == FileArchiveType.ZIP.value: 
            os.chdir(Path(inFile).parent)
            if os.path.isdir(inFile): 
                out_path = Path(out)
                if out_path.suffix == ".zip": out = f"{out_path.parent}/{out_path.stem}"
                shutil.make_archive(out, 'zip', Path(inFile).stem)
            if os.path.isfile(inFile): 
                with zipfile.ZipFile(out, 'w') as z: z.write(Path(inFile).name) 
            return True

        raise NotImplementedError(f"Type has not been implemented: {type}")

    def extract(self, type, inFile, out):
        Path(Path(out).parent).mkdir(parents = True, exist_ok = True)

        if type == FileArchiveType.TAR.value:
            with tarfile.open(inFile, 'r') as f: 
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(f, out)
                return True

        if type == FileArchiveType.ZIP.value: 
            with zipfile.ZipFile(inFile, 'r') as f: 
                f.extractall(out)
                return True

        raise NotImplementedError(f"Type has not been implemented: {type}")