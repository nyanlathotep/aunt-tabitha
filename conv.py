#!/usr/local/bin/python
from sys import argv
from csv import reader
from json import dump
import re
from collections import OrderedDict
import os

from codec import proc_line
from clocky import time_12
from tryload import tryload
import uxcore

def unduplicate(day):
  i = 1
  while i < len(day):
    name = day[i][2].lower().replace(' ','')
    lastname = day[i-1][2].lower().replace(' ','')
    if day[i][0:2] == day[i-1][0:2] and name == lastname:
      if day[i][3] == day[i-1][3]:
        del day[i]
      else:
        day[i-1][3] = day[i-1][3] + ', ' + day[i][3]
        del day[i]
    else:
      i += 1
  #print(day)
  return day
  
def blacklist(day, item, filters):
  for filt in filters:
    day = [x for x in day if not filt.search(x[item])]
  return day

def check_titlecase(s, seps, whitelist):
  bad_words = []
  for word in re.split(seps, s):
    if word in whitelist:
      continue
    if word[1:] != word[1:].lower() or word[0] != word[0].upper():
      bad_words += [word]
  return not bad_words, bad_words

try:
  ### configuration

  fp = open('data\\config.json')
  config = tryload(fp)
  fp.close()

  fp = open('data\\learned.json')
  learned = tryload(fp, object_pairs_hook = OrderedDict)
  fp.close()

  fp = open('data\\language.json')
  language = tryload(fp)
  fp.close()

  ### CSV reading

  fp = open(argv[1])
  week = reader(fp)
  week = [line for line in week if len([x for x in line if x != '']) > 0][2:]
  fp.close()

  ### initial processing

  days = []
  for line in week:
    if line[1] != '':
      days += [[line[1], []]]
      line[1] = ''
      if (len([x for x in line if x])):
        days[-1][1] += [proc_line(line)]
    elif days is not None and len(days) > 0:
      days[-1][1] += [proc_line(line)]

  ### blacklists and unduplication

  name_blacklist = [re.compile(x, flags = re.I) for x in config['name_blacklist']]
  room_blacklist = [re.compile(x, flags = re.I) for x in config['room_blacklist']]

  for day in days:
    day[1] = unduplicate(day[1])
    day[1] = blacklist(day[1], 2, name_blacklist)
    day[1] = blacklist(day[1], 3, room_blacklist)

  ### reorganizing

  firstday = None
  months = config['months']
  week = OrderedDict()
  for day in days:
    isoday = re.sub(config['date_pattern'], config['date_replacement'], day[0], flags = re.I)
    isoday = isoday.split(' ')
    isoday[1] = months.index(isoday[1]) + 1
    isoday = [int(x) for x in isoday]
    isoday = '%d-%02d-%02d' % tuple(isoday)
    if firstday == None:
      firstday = isoday
    week[isoday] = {'day': day[0], 'classes': [], 'start_margin': 60, 'end_margin': 0}
    for event in day[1]:
      week[isoday]['classes'] += [{'begin': event[0], 'end':event[1], 'name':event[2], 'room':event[3], 'active':True}]

  ### filters

  name_filters = config['name_filters']

  for filt in name_filters:
    filt[0] = re.compile(filt[0], re.I)

  for day in week:
    for event in week[day]['classes']:
      for filt in name_filters:
        event['name'] = filt[0].sub(filt[1], event['name'])

  room_filters = config['room_filters']

  for filt in room_filters:
    filt[0] = re.compile(filt[0], re.I)

  for day in week:
    for event in week[day]['classes']:
      for filt in room_filters:
        event['room'] = filt[0].sub(filt[1], event['room'])

  auto_cancel = [re.compile(x, flags = re.I) for x in config['auto_cancel']]

  for day in week:
    for event in week[day]['classes']:
      for filt in auto_cancel:
        if filt.search(event['name']):
          event['active'] = False
          break
  				
  ### length warnings

  name_thr = config['warn_name_length']
  name_subs = learned['name_subs']

  time_mode = config['time_mode']

  for day in week:
    for event in week[day]['classes']:
      if len(event['name']) >= name_thr:
        if event['name'].lower() in name_subs:
          event['name'] = name_subs[event['name'].lower()]
          continue
        print(language['name too long'])
        print(event['name'])
        print(event['room'])
        print(time_12(event['begin'], time_mode) + ' - ' + time_12(event['end'], time_mode))
        print('\n')
        print(language['replace explain'])
        print(' '*(name_thr+(len(language['entry prompt'])-1))+'|')
        new = raw_input(language['entry prompt'])
        if new:
          name_subs[event['name'].lower()] = new
          event['name'] = new

  room_thr = config['warn_room_length']
  room_subs = learned['room_subs']

  for day in week:
    for event in week[day]['classes']:
      if len(event['room']) >= room_thr:
        if event['room'].lower() in room_subs:
          event['room'] = room_subs[event['room'].lower()]
          continue
        print(language['room too long'])
        print(event['name'])
        print(event['room'])
        print(time_12(event['begin'], time_mode) + ' - ' + time_12(event['end'], time_mode))
        print('\n')
        print(language['replace explain room'])
        print(' '*(room_thr+(len(language['entry prompt'])-1))+'|')
        new = raw_input(language['entry prompt'])
        if new:
          room_subs[event['room'].lower()] = new
          event['room'] = new

  ### record learned behavior

  fp = open('data\\learned.json', 'w')
  dump(learned, fp, sort_keys=True, indent=2, separators=(',', ': '))
  fp.close()

  ### move/delete CSV
  try:
    if config['csv_action'] == 1:
      newpath = os.path.split(argv[1])
      newpath = os.path.join(newpath[0], config['csv_folder'], newpath[1])
      os.rename(argv[1], newpath)
    elif config['csv_action'] == 2:
      os.remove(argv[1])
  except:
    pass

  ### output

  for day in week:
    for event in week[day]['classes']:
      event['begin'] = time_12(event['begin'], time_mode)
      event['end'] = time_12(event['end'], time_mode)

  output_path = '{}.json'.format(firstday)
  fp = open(output_path, 'w')
  dump(week, fp, sort_keys=True, indent=2, separators=(',', ': '))
  fp.close()
  uxcore.display_success(['SUCCESS: converted file, outputted:', '         {}'.format(output_path)])
except:
  log_path = uxcore.write_log('conv', files=[argv[1]])
  uxcore.display_error(['ERROR: Failed to convert file, error data written:', '       {}'.format(log_path)])
