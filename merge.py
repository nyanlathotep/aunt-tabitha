#!/usr/local/bin/python
from sys import argv
from json import dump
from collections import OrderedDict
from tryload import tryload
from clocky import time_24
import uxcore

try:
  ### configuration
  fp = open('data\\config.json')
  config = tryload(fp)
  fp.close()

  ### sort input files

  files = sorted(argv[1:])

  ### load first

  fp = open(files[0])
  data = tryload(fp, object_pairs_hook = OrderedDict)
  fp.close()

  ### append remainder

  for i in files[1:]:
    fp = open(i)
    week = tryload(fp, object_pairs_hook = OrderedDict)
    fp.close()
    for i in week:
      data[i] = week[i]

  ### output

  for day in data:
    for event in data[day]['classes']:
      event['begin'] = time_24(event['begin'])
      event['end'] = time_24(event['end'])

  output_path = 'schedule.json'
  fp = open(output_path, mode = 'w')
  dump(data, fp, indent=2, separators=(',', ': '))
  fp.close()
  uxcore.display_success(['SUCCESS: converted file, outputted:', '         {}'.format(output_path)])
except:
  log_path = uxcore.write_log('conv', files=[argv[1]])
  uxcore.display_error(['ERROR: Failed to convert file, error data written:', '       {}'.format(log_path)])
