from json import load, dump

fp = open('data\language.json')
language = load(fp)
fp.close()

def tryload(fp, *args, **kwargs):
  try:
    data = load(fp, *args, **kwargs)
  except ValueError as e:
    print(language['error found'] % fp.name)
    print(e)
    print('\n')
    nothing = True
    for k in language['help']:
      if k in e.message:
        print(language['help intro'] + language['help'][k])
        nothing = False
        break
    if nothing:
      print(language['no help'])

    print('\n\n' + language['extra help'])

    fname = fp.name
    fp.close()
    fp = open(fname, 'r')
    error = {
      "message": e.message,
      "file": fp.read()
    }
    fp.close()
    fp = open('data\error.json', 'w')
    dump(error, fp)
    fp.close()

    raw_input('\n\n' + language['exit prompt'])
    exit(0)
  return data