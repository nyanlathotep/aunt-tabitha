# {"version": "bootstrap"}

import json, re, os, glob, sys, zlib, base64, hashlib

def get_bin_dir(arg0):
  return os.path.split(arg0)[0]

bin_meta_re = re.compile(r'\s*#\s*({.*})\s*')

def get_meta(first_line):
  match = bin_meta_re.match(first_line)
  if (match):
    try:
      meta = json.loads(match.group(1))
    except ValueError:
      meta = None
  else:
    meta = None
  return meta

def get_file_info(path):
  data = {'full_path': path}
  with open(path, 'rb') as fp:
    first_line = fp.readline()
    content = fp.read()
  file_hash = hashlib.sha256(first_line)
  file_hash.update(content)
  data['integrity'] = file_hash.hexdigest()
  meta = get_meta(first_line)
  if (meta):
    data['meta'] = meta
  return data

class PatchEntry:
  def __init__(self, patch, path):
    self.patch = patch
    self.path = path
  def execute(self):
    pass

class BundledFile(PatchEntry):
  def __init__(self, patch, data):
    PatchEntry.__init__(self, patch, data['path'])
    self.content = zlib.decompress(base64.b64decode(data['content']))
    self.integrity = self.integrity = data['integrity']
    content_hash = hashlib.sha256(self.content).hexdigest()
    self.integrity_passed = content_hash == self.integrity
    self.content = self.content
    self.version = None
    self.detect_version()
  def detect_version(self):
    first_line = self.content.partition('\n')[0]
    meta = get_meta(first_line)
    if ('version') in meta:
      self.version = meta['version']
  def execute(self):
    self.patch.extract_file(self)

class NegativeEntry(PatchEntry):
  def __init__(self, patch, data):
    PatchEntry.__init__(self, patch, data['path'])
  def execute(self):
    self.patch.remove_file(self)

entry_handlers = {
  'extract': BundledFile,
  'remove': NegativeEntry
}

def render_version(version):
  return 'untracked' if version is None else 'v({})'.format(version)

def render_integrity(integrity):
  return '[{}]'.format('pass' if integrity else 'FAIL')

class SummaryListing:
  format_string = 'nothing'
  def __init__(self, *data):
    self.data = data
  def preprocess(self):
    return {}
  def render(self, indent=''):
    data = self.preprocess()
    return indent + self.format_string.format(**data)

class SummaryAddition(SummaryListing):
  format_string = '{path}, {version} {integrity}'
  def __init__(self, *data):
    SummaryListing.__init__(self, *data)
  def preprocess(self):
    return {
      'path': self.data[0],
      'version': render_version(self.data[1]),
      'integrity': render_integrity(self.data[2])
    }

class SummaryChange(SummaryListing):
  format_string = '{path}, {old_version} -> {version} {integrity}'
  def __init__(self, *data):
    SummaryListing.__init__(self, *data)
  def preprocess(self):
    return {
      'path': self.data[0],
      'version': render_version(self.data[2]),
      'old_version': render_version(self.data[1]),
      'integrity': render_integrity(self.data[3])
    }

class SummaryDeletion(SummaryListing):
  format_string = '{path}'
  def __init__(self, *data):
    SummaryListing.__init__(self, *data)
  def preprocess(self):
    return {
      'path': self.data[0]
    }

class SummarySection:
  def __init__(self, title, members):
    self.title = title
    self.members = members
    self.items = []
  def append(self, *data):
    self.items.append(self.members(*data))
  def __len__(self):
    return len(self.items)
  def render(self):
    output = self.title + ':'
    output += '\n' + ('=' * len(self.title)) + '\n'
    output += '\n'.join(item.render('  ') for item in self.items)
    return output

class Summary:
  format_string = 'created {} files, updated {} files, removed {} files'
  def __init__(self):
    self.additions = SummarySection('CREATED', SummaryAddition)
    self.changes = SummarySection('UPDATED', SummaryChange)
    self.deletions = SummarySection('REMOVED', SummaryDeletion)
  def render(self):
    sections = [self.additions, self.changes, self.deletions]
    return '\n\n'.join(section.render() for section in sections if len(section) > 0)
  def render_short(self):
    return self.format_string.format(len(self.additions), len(self.changes), len(self.deletions))

class Patch:
  def __init__(self, data):
    self.summary = Summary()
    self.entries = []
    for item in data['entries']:
      self.entries.append(entry_handlers[item['action']](self, item))
  def add_addition(self, *params):
    self.summary.additions.append(*params)
  def add_change(self, *params):
    self.summary.changes.append(*params)
  def add_deletion(self, *params):
    self.summary.deletions.append(*params)
  def extract_file(self, filespec):
    path = filespec.path
    other_info = get_file_info(path) if os.path.exists(path) else {}
    if (not other_info):
      self.write_file(filespec)
      self.add_addition(path, filespec.version, filespec.integrity_passed)
    else:
      if (other_info['integrity'] == filespec.integrity):
        return
      self.write_file(filespec)
      old_version = None
      if ('meta' in other_info and 'version' in other_info['meta']):
        old_version = other_info['meta']['version']
      self.add_change(path, old_version, filespec.version, filespec.integrity_passed)
  def write_file(self, filespec):
    with open(filespec.path, 'wb') as fp:
      fp.write(filespec.content)
  def remove_file(self, filespec):
    try:
      if (os.path.exists(filespec.path)):
        os.remove(filespec.path)
        self.add_deletion(filespec.path)
    except:
      pass
  def execute(self):
    for item in self.entries:
      item.execute()

if (__name__ == '__main__'):
  def abort():
    raw_input('Invalid patch format.\nPress enter to exit.')
    exit(0)
  
  try:
    with (open(sys.argv[1])) as fp:
      data = json.load(fp)
  except (ValueError, IndexError):
    abort()
  if ('magic' not in data or data['magic'] != 'aunt-tabitha:update'):
    abort()

  patch = Patch(data)
  patch.execute()

  print(patch.summary.render())

  raw_input('\n{}\nall done! press enter to exit'.format(patch.summary.render_short()))
