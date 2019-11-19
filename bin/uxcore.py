# {"id": "uxcore", "version": "bin_meta_alpha"}

import traceback
import base64, zlib, json
import hashlib
import datetime
import random
from collections import OrderedDict
import os.path, glob, re

###############
# error logging
###############

nouns = [
  'angle', 'ant', 'apple', 'arch', 'arm', 'army', 'baby', 'bag', 'ball',
  'band', 'basin', 'basket', 'bath', 'bed', 'bee', 'bell', 'berry', 'bird',
  'blade', 'board', 'boat', 'bone', 'book', 'boot', 'bottle', 'box', 'boy',
  'brain', 'brake', 'branch', 'brick', 'bridge', 'brush', 'bucket', 'bulb',
  'button', 'cake', 'camera', 'card', 'cart', 'carriage', 'cat', 'chain',
  'cheese', 'chest', 'chin', 'church', 'circle', 'clock', 'cloud', 'coat',
  'collar', 'comb', 'cord', 'cow', 'cup', 'curtain', 'cushion', 'dog', 'door',
  'drain', 'drawer', 'dress', 'drop', 'ear', 'egg', 'engine', 'eye', 'face',
  'farm', 'feather', 'finger', 'fish', 'flag', 'floor', 'fly', 'foot', 'fork',
  'fowl', 'frame', 'garden', 'girl', 'glove', 'goat', 'gun', 'hair', 'hammer',
  'hand', 'hat', 'head', 'heart', 'hook', 'horn', 'horse', 'hospital', 'house',
  'island', 'jewel', 'kettle', 'key', 'knee', 'knife', 'knot', 'leaf', 'leg',
  'library', 'line', 'lip', 'lock', 'map', 'match', 'monkey', 'moon', 'mouth',
  'muscle', 'nail', 'neck', 'needle', 'nerve', 'net', 'nose', 'nut', 'office',
  'orange', 'oven', 'parcel', 'pen', 'pencil', 'picture', 'pig', 'pin', 'pipe',
  'plane', 'plate', 'plough', 'pocket', 'pot', 'potato', 'prison', 'pump',
  'rail', 'rat', 'receipt', 'ring', 'rod', 'roof', 'root', 'sail', 'school',
  'scissors', 'screw', 'seed', 'sheep', 'shelf', 'ship', 'shirt', 'shoe',
  'skin', 'skirt', 'snake', 'sock', 'spade', 'sponge', 'spoon', 'spring',
  'square', 'stamp', 'star', 'station', 'stem', 'stick', 'stocking', 'stomach',
  'store', 'street', 'sun', 'table', 'tail', 'thread', 'throat', 'thumb',
  'ticket', 'toe', 'tongue', 'tooth', 'town', 'train', 'tray', 'tree',
  'trousers', 'umbrella', 'wall', 'watch', 'wheel', 'whip', 'whistle', 'window',
  'wing', 'wire', 'worm']

def nouns_signature(seed, n=3):
  return '_'.join(random.choice(nouns) for _ in range(n))

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

def get_bin_dir(arg0):
  return os.path.split(arg0)[0]

bin_meta_re = re.compile(r'\s*#\s*({.*})\s*')

def collect_bin_info(bin_dir):
  data = {}
  for path in glob.iglob(os.path.join(bin_dir,'*.py')):
    path_data = {'full_path': path}
    with open(path, 'rb') as fp:
      first_line = fp.readline()
      content = fp.read()
    file_hash = hashlib.sha256(first_line)
    file_hash.update(content)
    path_data['integrity'] = file_hash.hexdigest()
    match = bin_meta_re.match(first_line)
    if (match):
      path_data['meta'] = json.loads(match.group(1), object_pairs_hook = OrderedDict)
    file_name = os.path.split(path)[1]
    data[file_name] = path_data
  return data

def produce_log(source=None, exception=True, files=None, context=None, first_arg=None):
  data = OrderedDict({'time': timestamp()})
  if (source):
    data['source'] = source
  if (exception):
    data['exception'] = traceback.format_exc()
  if (context):
    data['context'] = context
  if (first_arg):
    bin_dir = get_bin_dir(first_arg)
    data['bin_meta'] = collect_bin_info(bin_dir)
  if (files):
    data['files'] = []
    for path in files:
      data['files'].append(bundle_file(path))
  return data

def fix_timestamp(ts, compact=False):
  if (compact):
    return ts.replace(':','').replace('T','').replace('-','')
  return ts.replace(':','-')

def write_log(source=None, exception=True, files=None, log_prefix='log', context= None, first_arg=None):
  data = produce_log(source, exception, files, context, first_arg)
  ts = fix_timestamp(data['time'], compact=True)
  signature = nouns_signature(fix_timestamp(data['time'], compact=True))
  path = '{prefix}_{timestamp}_{signature}.json'.format(
    **{'prefix':log_prefix,'timestamp':ts,'signature':signature})
  with open(path, 'w') as fp:
    json.dump(data, fp)
  return path


#################################
# success/error message rendering
#################################

def render_message(message, border, message_prefix, inner_padding, outer_padding):
  payload = [message_prefix + line for line in message]
  payload = [inner_padding] + payload + [inner_padding]
  border_len = max(len(line) for line in payload)
  payload = [outer_padding, border * border_len] + payload + [border * border_len, outer_padding]
  return '\n'.join(payload)

success_params = ('-', '> ', '', '')
error_params = ('=', '!! > ', '!!', '')

def render_success(message):
  return render_message(message, *success_params)

def render_error(message):
  return render_message(message, *error_params)

def display_message(message, border, message_prefix, inner_padding, outer_padding, hard_acknowledge=False):
  print(render_message(message, border, message_prefix, inner_padding, outer_padding))
  if (hard_acknowledge):
    i = ''
    while (i != 'confirm'):
      i = raw_input('type "confirm" to exit > ').strip().lower()
  else:
    raw_input('press enter to exit > ')

def display_success(message):
  display_message(message, *success_params)

def display_error(message):
  display_message(message, *error_params, hard_acknowledge=True)

def display_success_standard(output_path):
  display_success(['SUCCESS: converted file, outputted:', '         {}'.format(output_path)])

def display_error_standard(log_path):
  display_error(['ERROR: Failed to convert file', '       error data and input files written to:', '       {}'.format(log_path)])
