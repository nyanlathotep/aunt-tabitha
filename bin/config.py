import copy, nicejson

def default_core():
  return {
    "time_mode": 0,

    "csv_action": 0,
    "csv_folder": "csv",

    "warn_name_length": 36,
    "warn_room_length": 26,

    "room_blacklist": [
      "aerobic"
    ],
    "name_blacklist": [
      "^breakfast$",
      "^lunch$",
      "^ndb ?presentations?:?$",
      "^special ?events?:? ?(?:social)? ?(?:hall)? ?:?$",
      "^reserved$"
    ],

    "room_filters": [
      ["class(?:\\s+)?room(?:\\s+)?(\\d+)(/? ?[a-z]+)?", "Classroom \\1"],
      ["(?:Classroom 10)|(card(?:\\s+)?room)", "Cardroom"],
      ["community(?:\\s+)?room", "Community Room"],
      ["computer(?:\\s+)?lounge", "Computer Lounge"],
      ["kiln(?:\\s+)room", "Kiln Room"],
      ["(?:[a-z\\s]+)?social(?:[a-z\\s]+)?", "Social Hall"],
      ["(?:[a-z\\s]+)?lobby(?:[a-z\\s]+)?", "Lobby"]
    ],
    "name_filters": [
      ["^ndb(?:\\s+)?presentations?:?(?:\\s+)?(.+)$", "\\1"],
      ["^special(?:\\s+)?events?:?(?:\\s+)?(?:social)?(?:\\s+)?(?:hall)? ?:? ?(.+)$", "\\1"],
      ["^(?:APS\\s+)?Transitiona?l?(?:\\s+)?Services(?:[/\\s]+APS)?$", "APS Transition Services"],
      ["after(?:\\s+)?school", "After-school"]
    ],
    "auto_cancel": [

    ],

    "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "date_pattern": "[a-z]+ ([a-z]+) (\\d+), (\\d+)",
    "date_replacement": "\\3 \\1 \\2"
  }

def default_language():
  return {
    "name too long": "the name of this event may be too long",
    "replace explain": "enter a new name or just press enter to leave it the same\nthe new name should be about this long or shorter:",
    "entry prompt": "> ",
    "room too long": "the name of this event's room may be too long",
    "replace explain room": "enter a new room or just press enter to leave it the same\nthe new room should be about this long or shorter:",
    "error found": "Error detected while reading %s, could not complete operation:",
    "help intro": "comments on this error:\n",
    "help": {
      "Expecting , delimiter": "this might mean you are missing a , on the previous line",
      "Expecting : delimiter": "this might mean you are missing either a : or a \" before the : on this line",
      "Invalid control character": "this might mean you are missing a \" at the end of this line",
      "Expecting property name": "this might mean that you are missing a } on the previous line"
    },
    "no help": "no extra help on this error was found",
    "extra help": "if you don't know how to address this error, run Help\nto send the relevant information to Kyle",
    "exit prompt": "press return to exit"
  }

def default_learned():
  return {
    "name_subs": {},
    "room_subs": {}
  }

config_defaults = {
  'core': default_core,
  'language': default_language,
  'learned': default_learned
}

class ConfigManager:
  def __init__(self, **cfg_files):
    self.cfg_files = cfg_files
    self.cfg_data = {}
  def __getattr__(self, attr):
    if (attr not in self.cfg_files):
      raise AttributeError
    path = self.cfg_files[attr]
    if (attr not in self.cfg_data):
      try:
        data = nicejson.load(path)
      except IOError:
        data = config_defaults[attr]()
      self.cfg_data[attr] = data
    return self.cfg_data[attr]
  def save(self):
    for attr in self.cfg_files:
      path = self.cfg_files[attr]
      if (attr in self.cfg_data):
        nicejson.dump(self.cfg_data[attr], path)
