import json
from collections import OrderedDict

def load(path):
  with open(path) as fp:
    data = json.load(fp, object_pairs_hook = OrderedDict)
  return data

def dump(obj, path):
  with open(path, 'w') as fp:
    json.dump(obj, fp, indent=2, separators=(',', ': '))
