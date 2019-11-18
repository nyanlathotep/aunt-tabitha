from clocky import time_24

def check_line(line):
  # check time exists
  if (line[2].strip() == '' or line[3].strip() == ''):
    return False
  return True

def proc_line(line):
  line = line[2:]
  line[1] = line[1][2:]
  del line[2]
  if (line[2].find('(') != -1):
    line[3] = line[2][line[2].rfind('(')+1:line[2].rfind(')')]
  else:
    line[3] = 'Nowhere'
  indices = [line[2].find(x) for x in '(*$']
  indices = [x for x in indices if x != -1]
  if indices:
    line[2] = line[2][:min(indices)].strip()
  else:
    line[2] = line[2].strip()
  line[0] = time_24(line[0])
  line[1] = time_24(line[1])
  return line