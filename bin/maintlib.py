# {"version": "2"}

import re, json, hashlib, glob, os, datetime, traceback, sys, base64, zlib
from collections import OrderedDict

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

def collect_file_info(root, pattern, key_root= os.curdir):
  data = {}
  for path in glob.iglob(os.path.join(root, pattern)):
    path_data = get_file_info(path)
    key = os.path.relpath(path, key_root)
    data[key] = path_data
  return data

def timestamp():
  dt = datetime.datetime.now()
  dt = dt.replace(microsecond = 0)
  return dt.isoformat()

def bundle_file(path):
  data = {'path': path}
  try:
    with open(path, 'rb') as fp:
      content = fp.read()
    data['content'] = base64.b64encode(zlib.compress(content))
    data['integrity'] = hashlib.sha256(content).hexdigest()
  except:
    data['exception'] = traceback.format_exc()
  return data

def get_bin_dir():
  return os.path.split(sys.argv[0])[0]

def collect_bin_info(bin_dir):
  return collect_file_info(bin_dir, '*.py', bin_dir)

def produce_log(source=None, files=None, exception=True, bin_info=True):
  data = OrderedDict({'time': timestamp()})
  if (source):
    data['source'] = source
  if (exception):
    data['exception'] = traceback.format_exc()
  if (bin_info):
    bin_dir = get_bin_dir()
    data['bin_meta'] = collect_bin_info(bin_dir)
  if (files):
    data['files'] = []
    for path in files:
      data['files'].append(bundle_file(path))
  return data
