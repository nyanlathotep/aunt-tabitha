#!/usr/local/bin/python
from sys import argv
from json import dump
from collections import OrderedDict
from tryload import tryload
from clocky import time_12, time_24
import uxcore

try:
  ### configuration

  fp = open('data\\config.json')
  config = tryload(fp)
  fp.close()

  ### input

  fp = open(argv[1], mode = 'r')
  week = tryload(fp, object_pairs_hook = OrderedDict)
  fp.close()

  ### convert times to 24 hour

  for day in week:
    for event in week[day]['classes']:
      event['begin'] = time_24(event['begin'])
      event['end'] = time_24(event['end'])

  ### set margins

  for i in week:
    classes = []
    for x in week[i]["classes"]:
      begin = x["begin"].split(":")
      begin = int(begin[0])*60 + int(begin[1])
      end = x["end"].split(":")
      end = int(end[0])*60 + int(end[1])
      classes += [(begin,end)]
    fitness = {}
    for sm in range(30, 480, 15):
      for em in range(0, 240, 15):
        f = 0
        for time in range(480+60*(i==5), 1261-360*(i==5), 5):
          stuff = sum([1 for x in classes if time >= (x[0] - sm) and time <= (x[1] + em)])
          if stuff > f:
            f = stuff
        fitness[(sm,em)] = f
    good = {x:fitness[x] for x in fitness if fitness[x] <= 13}
    sel = []
    for x in good:
      val = abs(0.5 - x[1]/(x[0]-59.)) - 2*(x[0]>60) - 2*(x[0]>90) - x[0]/30. - x[1]/30.
      sel += [(x, val)]
    sel.sort(key=lambda x: x[1])
    week[i]["start_margin"] = sel[0][0][0]
    week[i]["end_margin"] = sel[0][0][1]

  ### output

  time_mode = config['time_mode']

  for day in week:
    for event in week[day]['classes']:
      event['begin'] = time_12(event['begin'], time_mode)
      event['end'] = time_12(event['end'], time_mode)

  fp = open(argv[1], mode = 'w')
  dump(week, fp, indent=2, separators=(',', ': '))
  fp.close()
  uxcore.display_success(['SUCCESS: converted file, outputted:', '         {}'.format(argv[1])])
except:
  log_path = uxcore.write_log('conv', files=[argv[1]])
  uxcore.display_error(['ERROR: Failed to convert file, error data written:', '       {}'.format(log_path)])
