# {"version": "2"}

from sys import argv
from clocky import time_24
import uxcore
from config import ConfigManager
import nicejson

try:
  ### configuration
  config = ConfigManager(
    core='data\\config.json')

  ### sort input files

  files = sorted(argv[1:])

  ### load first
  data = nicejson.load(files[0])

  ### append remainder

  for path in files[1:]:
    week = nicejson.load(path)
    for i in week:
      data[i] = week[i]

  ### output

  for day in data:
    for event in data[day]['classes']:
      event['begin'] = time_24(event['begin'])
      event['end'] = time_24(event['end'])

  output_path = 'schedule.json'
  nicejson.dump(data, output_path)
  uxcore.display_success_standard(output_path)
except:
  log_path = uxcore.write_log('merge', files=files)
  uxcore.display_error_standard(log_path)
