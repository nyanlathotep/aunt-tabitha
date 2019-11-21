# in contrast to aunt-tabitha's core scripts
# this is a utility script for reading uxcore logs
# it is written to work in python3 (>=3.7)
# it has an external dependency (ruamel.yaml)

import os
import json, base64, zlib, hashlib
from ruamel.yaml import YAML
import io

yaml = YAML()

file_summary_template = """{name} ({size} B)"""
integrity_summary_template = """{integrity} [{passed}]"""

class Bundle:
  def __init__(self, content, path):
    super().__init__()
    self.content = content
    self.path = path
    self.short_path = os.path.split(self.path)[1]

file_exc_template = """exception loading {name} (during logging):
=========================================
{exc}
"""
file_exc_summary = """{name} (failed to load)"""

class BundledFileException(Bundle):
  def __init__(self, data):
    super().__init__(self.render_file_exc(data), data['path'] + '.log')
  def render_file_exc(self, data):
    return file_exc_template.format(name= os.path.split(data['path'])[1], exc= data['exception'])
  def render_summary(self):
    return file_exc_summary.format(name = self.short_path)

class BundledFile(Bundle):
  def __init__(self, data, compressed= True):
    super().__init__(
      zlib.decompress(base64.b64decode(data['content'])) if compressed else data['content'],
      data['path'])
    self.integrity = data['integrity'] if 'integrity' in data else None
    if (self.integrity):
      content_hash = hashlib.sha256(self.content).hexdigest()
      self.integrity_passed = content_hash == self.integrity
    if (compressed):
      self.content = self.content.decode('utf-8')
  def render_summary(self):
    output = file_summary_template.format(name=self.short_path, size=len(self.content))
    if (self.integrity):
      output += '\n' + integrity_summary_template.format(integrity= self.integrity, passed = 'PASS' if self.integrity_passed else 'FAIL')
    return output


log_summary_template = """time: {time}
log source: {source}
=====================
exception:
{exception}
"""

class UXCoreLog:
  def __init__(self, data):
    self.time = data['time'] if 'time' in data else None
    self.source = data['source'] if 'source' in data else None
    self.exception = data['exception'] if 'exception' in data else None
    self.context = data['context'] if 'context' in data else None
    self.bin_meta = data['bin_meta'] if 'bin_meta' in data else None
    self.files = []
    if ('files' in data):
      for fil in data['files']:
        if ('content' in fil):
          self.files.append(BundledFile(fil))
        else:
          self.files.append(BundledFileException(fil))
  def get_files(self):
    yield BundledFile({'content': self.render_summary(), 'path': 'summary.txt'}, compressed= False)
    if (self.context):
      yield BundledFile({'content': self.render_yaml(self.context), 'path': 'context.yaml'}, compressed= False)
    if (self.bin_meta):
      yield BundledFile({'content': self.render_yaml(self.bin_meta), 'path': 'bin_meta.yaml'}, compressed= False)
    for fil in self.files:
      yield fil
  def render_summary(self):
    output = log_summary_template.format(**{
      'time': self.time or 'unknown',
      'source': self.source or 'unknown',
      'exception': self.exception or 'no exception!?'})
    output += '\nbundled files:\n==============\n'
    output += '\n'.join([x.render_summary() for x in self.files])
    if (self.bin_meta):
      output += '\n\ncode versions:\n==============\n'
      output += '\n'.join(['{}: {}'.format(k, self.bin_meta[k]['meta']['version']) for k in self.bin_meta])
    return output
  def render_yaml(self, obj):
    buffer = io.StringIO()
    yaml.dump(obj, buffer)
    return buffer.getvalue()

def get_basename(path):
  return os.path.splitext(os.path.split(path)[1])[0]

def write_log(folder, log):
  try:
    os.mkdir(folder)
  except FileExistsError:
    pass
  for fil in log.get_files():
    path = os.path.join(folder, fil.short_path)
    with open(path, 'w') as fp:
      fp.write(fil.content)

if (__name__ == '__main__'):
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('log_file')
  parser.add_argument('--verbose', '-v', action=argparse._StoreTrueAction)
  parser.add_argument('--extract', '-e', action=argparse._StoreTrueAction)
  args = parser.parse_args()

  with open(args.log_file) as fp:
    dat = json.load(fp)
  log = UXCoreLog(dat)

  if (args.verbose):
    print(log.render_summary())

  if (args.extract):
    basename = get_basename(args.log_file)
    write_log(basename, log)
