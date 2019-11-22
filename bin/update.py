# {"version": "2"}

import re, os, glob, sys, zlib, base64, hashlib, errno

import maintlib, uxcore, nicejson

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
    meta = maintlib.get_meta(first_line)
    if meta and ('version') in meta:
      self.version = meta['version']
  def execute(self):
    self.patch.extract_file(self)

class NegativeEntry(PatchEntry):
  def __init__(self, patch, data):
    PatchEntry.__init__(self, patch, data['path'])
    self.pattern = data['pattern'] if 'pattern' in data else False
  def execute(self):
    self.patch.remove_entry(self)

class CollectEntry(PatchEntry):
  def __init__(self, patch, data):
    PatchEntry.__init__(self, patch, data['path'])
    self.pattern = data['pattern'] if 'pattern' in data else False
  def execute(self):
    self.patch.collect_entry(self)

entry_handlers = {
  'extract': BundledFile,
  'remove': NegativeEntry,
  'collect': CollectEntry
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
    if (len(self.additions) + len(self.changes) + len(self.deletions) > 0):
      return self.format_string.format(len(self.additions), len(self.changes), len(self.deletions))
    return None

class FileCollection:
  format_string = 'collected {num} files to {out}'
  def __init__(self):
    self.signatures = set()
    self.paths = []
    self.output_path = None
  def add(self, path):
    relpath = os.path.relpath(path)
    if (relpath not in self.signatures):
      self.signatures.add(relpath)
      self.paths.append(path)
  def set_output(self, path):
    self.output_path = path
  def __len__(self):
    return len(self.paths)
  def execute(self):
    log_data = maintlib.produce_log('update:collect', self.paths, exception=False)
    nicejson.dump(log_data, self.output_path)
  def render_short(self):
    if (len(self.paths) > 0):
      return self.format_string.format(num= len(self.paths), out = self.output_path)
    return None

class Patch:
  def __init__(self, data):
    self.summary = Summary()
    self.properties = data['properties'] if 'properties' in data else {}
    self.entries = []
    self.collection = FileCollection()
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
    other_info = maintlib.get_file_info(path) if os.path.exists(path) else {}
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
    root = os.path.split(filespec.path)[0]
    try:
      os.makedirs(root)
    except OSError as e:
      if (e.errno != errno.EEXIST):
        raise
    with open(filespec.path, 'wb') as fp:
      fp.write(filespec.content)
  def remove_entry(self, filespec):
    if (filespec.pattern):
      for path in glob.iglob(filespec.path):
        self.remove_file(path)
    else:
      self.remove_file(filespec.path)
  def remove_file(self, path):
    try:
      if (os.path.exists(path)):
        os.remove(path)
        self.add_deletion(path)
    except:
      pass
  def collect_entry(self, filespec):
    if (filespec.pattern):
      for path in glob.iglob(filespec.path):
        self.collect_path(path)
    else:
        self.collect_path(filespec.path)
  def collect_path(self, path):
    self.collection.add(path)
  def execute(self):
    for item in self.entries:
      item.execute()
    if (len(self.collection) > 0):
      outfile = 'update_collect.json'
      if ('remote_output' in self.properties):
        outfile = self.properties['remote_output']
      self.collection.set_output(outfile)
      self.collection.execute()

if (__name__ == '__main__'):
  def abort():
    uxcore.display_error(['invalid patch format'])
    exit(0)
  
  try:
    data = nicejson.load(sys.argv[1])
  except (ValueError, IndexError):
    abort()
  if ('magic' not in data or data['magic'] != 'aunt-tabitha:update'):
    abort()

  patch = Patch(data)
  patch.execute()

  print(patch.summary.render())

  message = []
  summary = patch.summary.render_short()
  if (summary):
    message.append(summary)
  collection = patch.collection.render_short()
  if (collection):
    message.append(collection)
  if (not message):
    message = ['all up to date with patch']
  uxcore.display_success(message)
