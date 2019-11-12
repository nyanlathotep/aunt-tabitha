import traceback
import base64, zlib, json
import hashlib
import datetime

###############
# error logging
###############

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

def produce_log(source=None, exception=True, files=None):
  data = {'time': timestamp()}
  if (source):
    data['source'] = source
  if (exception):
    data['exception'] = traceback.format_exc()
  if (files):
    data['files'] = []
    for path in files:
      data['files'].append(bundle_file(path))
  return data

def write_log(source=None, exception=True, files=None, log_prefix='errlog'):
  data = produce_log(source, exception, files)
  ts = data['time'].replace('-','').replace('T','').replace(':','')
  path = '{prefix}_{timestamp}.json'.format(**{'prefix':log_prefix,'timestamp':ts})
  with open(path, 'w') as fp:
    json.dump(data, fp)


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
      i = raw_input('type "confirm" to exit> ').strip().lower()
  else:
    raw_input('')

def display_success(message):
  display_message(message, *success_params)

def display_error(message):
  display_message(message, *error_params, hard_acknowledge=True)
