import sys, os, traceback, base64, zlib, hashlib, json

def bundle_file(path, allow_exceptions= False):
  data = {'path': path}
  try:
    with open(path, 'rb') as fp:
      content = fp.read()
    data['content'] = base64.b64encode(zlib.compress(content)).decode('ascii')
    data['integrity'] = hashlib.sha256(content).hexdigest()
  except:
    if (allow_exceptions):
      data['exception'] = traceback.format_exc()
    else:
      raise
  return data

if (__name__ == '__main__'):
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--add_files', '-a', nargs='*')
  parser.add_argument('--del_files', '-d', nargs='*')
  parser.add_argument('--del_glob', '-D', nargs='*')
  parser.add_argument('--output', '-o')
  args = parser.parse_args()
  archive = {
    'magic': 'aunt-tabitha:update',
    'entries': []
  }
  if (args.add_files):
    for path in args.add_files:
      bundle = {'action': 'extract'}
      bundle.update(bundle_file(path))
      archive['entries'].append(bundle)
  if (args.del_files):
    for path in args.del_files:
      bundle = {'action': 'remove', 'path': path, 'pattern': False}
      archive['entries'].append(bundle)
  if (args.del_glob):
    for path in args.del_glob:
      bundle = {'action': 'remove', 'path': path, 'pattern': True}
      archive['entries'].append(bundle)
  with open(args.output, 'w') as fp:
    json.dump(archive, fp, indent= 2)
