# {"version": "2"}

import re, json, hashlib, glob, os

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
