import io
import zipfile

BUFFER = {
  'zip': lambda
}


class Archive(object):

  def __init__(self):
    self._buffer = io.BytesIO()

  def add_file(self, name, content):
    pass


class Zip(Archive):

  def add_file(self, name, content):
    with zipfile.ZipFile(self._buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
      zip_file.writestr(name, content)


class Tar(Archive):

  def add_file(self, name, content):
    pass
