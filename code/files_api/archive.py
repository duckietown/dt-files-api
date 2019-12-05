import os
import io
import zipfile
import tarfile
from abc import ABC, abstractmethod


class Archive(ABC):

  def __init__(self):
    self._buffer = io.BytesIO()

  @abstractmethod
  def add(self, file, arcname):
    pass

  @abstractmethod
  def mime(self):
    pass

  def data(self):
    self._buffer.seek(0)
    return self._buffer

  def size(self):
    return self._buffer.getbuffer().nbytes


class Zip(Archive):

  def add(self, filepath, arcname):
    if not os.path.exists(filepath):
      raise ValueError(f'File {filepath} not found.')
    for file, aname in listfiles(filepath, arcname):
      mode = "a" if self.size() else "w"
      with zipfile.ZipFile(self._buffer, mode, zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.write(file, aname)

  def mime(self):
    return 'application/zip', None



class Tar(Archive):

  def add(self, filepath, arcname):
    if not os.path.exists(filepath):
      raise ValueError(f'File {filepath} not found.')
    mode = "a" if self.size() else "w"
    with tarfile.TarFile(fileobj=self._buffer, mode=mode) as tar_file:
      tar_file.add(filepath, arcname)

  def mime(self):
    return 'application/x-gzip', None


def listfiles(filepath, arcpath):
  if os.path.isfile(filepath):
    yield filepath, arcpath
  return
  # ---
  for root, _, files in os.walk(filepath):
    for filename in files:
      arcname = os.path.join(arcpath, root[len(filepath):], filename)
      yield os.path.join(root, filename), arcname
