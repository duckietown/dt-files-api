import copy
import os
import io
import zipfile
import tarfile
from abc import ABC, abstractmethod


class Archive(ABC):

    def __init__(self):
        self._buffer = io.BytesIO()

    @abstractmethod
    def add(self, file, arcname, logger):
        pass

    @abstractmethod
    def mime(self):
        pass

    @abstractmethod
    def extension(self):
        pass

    @abstractmethod
    def extract_all(self, destination: str):
        pass

    def data(self):
        self._buffer.seek(0)
        return self._buffer

    def size(self):
        return self._buffer.getbuffer().nbytes

    @classmethod
    def from_buffer(cls, buffer: io.BytesIO) -> 'Archive':
        archive = cls()
        archive._buffer = copy.deepcopy(buffer)
        return archive


class ArchiveError(BaseException):

    def __init__(self, message: str):
        self.message = message


class Zip(Archive):

    def add(self, filepath, arcname, logger):
        if not os.path.exists(filepath):
            raise ValueError(f'File {filepath} not found.')
        for file, aname in self.listfiles(filepath, arcname):
            mode = "a" if self.size() else "w"
            logger.debug(f'> Adding {file} -> {aname} '
                         f'({sizeof_fmt(os.path.getsize(file))}) to archive...')
            with zipfile.ZipFile(self._buffer, mode, zipfile.ZIP_DEFLATED, False) as zip_file:
                zip_file.write(file, aname)

    def mime(self):
        return 'application/zip', None

    def extension(self):
        return 'zip'

    def extract_all(self, destination: str):
        os.makedirs(destination, exist_ok=True)
        # extract all
        try:
            with zipfile.ZipFile(self._buffer, 'r', zipfile.ZIP_DEFLATED, False) as zip_file:
                zip_file.extractall(destination)
        except zipfile.BadZipfile as e:
            raise ArchiveError(str(e))

    @staticmethod
    def listfiles(filepath, arcpath):
        # filepath is a FILE
        if os.path.isfile(filepath):
            yield filepath, arcpath
        # filepath is a DIRECTORY
        if os.path.isdir(filepath):
            for root, _, files in os.walk(filepath):
                for filename in files:
                    arcname = os.path.join(arcpath, os.path.relpath(root, filepath), filename)
                    yield os.path.join(root, filename), arcname


class Tar(Archive):

    def add(self, filepath, arcname, logger):
        if not os.path.exists(filepath):
            raise ValueError(f'File {filepath} not found.')
        mode = "a" if self.size() else "w"
        logger.debug(f'> Adding {filepath} -> {arcname} '
                     f'({sizeof_fmt(os.path.getsize(filepath))}) to archive...')
        with tarfile.TarFile(fileobj=self._buffer, mode=mode) as tar_file:
            tar_file.add(filepath, arcname)

    def mime(self):
        return 'application/x-gzip', None

    def extension(self):
        return 'tar.gz'

    def extract_all(self, destination: str):
        os.makedirs(destination, exist_ok=True)
        # extract all
        try:
            with tarfile.TarFile(fileobj=self._buffer, mode='r') as tar_file:
                tar_file.extractall(destination)
        except tarfile.ReadError as e:
            raise ArchiveError(str(e))


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
