from json import load

def tryload(fp, *args, **kwargs):
  data = load(fp, *args, **kwargs)
  return data
