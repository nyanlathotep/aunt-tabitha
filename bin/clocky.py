# {"version": "1"}

def time_24(time):
  time = time.lower()
  time = time.replace(' ','')
  time = time.replace('m','')
  if time[-1] in 'ap':
    time = [time[:-1], time[-1]]
    time[0] = time[0].split(':')
    if (time[1] == "a" and time[0][0] == "12"):
      time[0][0] = "0"
    elif (time[1] == "p" and time[0][0] != "12"):
      time[0][0] = str(int(time[0][0])+12)
  else:
    return time

  return ':'.join(time[0])

def time_12(time, format):
  if format == -1:
    return time
  h,m = time.split(':')
  h = int(h)
  t = 'a' if h < 12 else 'p'
  if (format & 2):
    t += 'm'
  if (format & 1):
    t = t.upper()
  if (format & 4):
    t = ' ' + t
  h = h % 12
  h = h if h else 12
  return '%d:%s%s' % (h, m, t)