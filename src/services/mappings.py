from src.services.states import state_abbrev, countries

update_fields_mappings = [
  {
    'name': 'Health Imaging',
    'abrv': 'HI',
    'list_id': '31a1719578',
    'status': 'field_247',
    'update': 'field_299',
    'active': 'field_252',
    'cleaned': 'field_260',
    'unsub': 'field_256',
    'groups_fields': ['field_283', 'field_294']
  },
  {
    'name': 'Radiology Business',
    'abrv': 'RB',
    'list_id': '342e16db33',
    'status': 'field_249',
    'update': 'field_300',
    'active': 'field_253',
    'cleaned': 'field_261',
    'unsub': 'field_257',
    'groups_fields': ['field_289', 'field_295']
  },
  {
    'name': 'Cardiovascular Business',
    'abrv': 'CVB',
    'list_id': '8725f4d734',
    'status': 'field_246',
    'update': 'field_298',
    'active': 'field_250',
    'cleaned': 'field_259',
    'unsub': 'field_255',
    'groups_fields': ['field_290', 'field_293']
  },
  {
    'name': 'Health Exec',
    'abrv': 'HE',
    'list_id': 'afd9a8e4ef',
    'status': 'field_248',
    'update': 'field_297',
    'active': 'field_251',
    'cleaned': 'field_258',
    'unsub': 'field_254',
    'groups_fields': ['field_267', 'field_292']
  },
  {
    'name': 'AI Healthcare',
    'abrv': 'AI',
    'list_id': 'fdc72b3ec4',
    'status': 'field_242',
    'update': 'field_296',
    'active': 'field_243',
    'cleaned': 'field_245',
    'unsub': 'field_244',
    'groups_fields': ['field_262', 'field_291']
  }
]


payload_mappings = {
  'field_64': 'email_address', # Email
  'field_63': '@get_name',     # Name
  'field_114': '_ORGNAME',
  'field_179': '@get_country',
  'field_185': '_CITY',
  'field_184': '@get_state', # '_STATE',
  'field_229': '_LINKEDIN',

  'field_121': 'status',
  'field_167': 'last_changed',

  # 'field_120': '@get_user_role'

  # Health Imaging
  'field_283': '@get_newsletters',
  'field_294': '@get_promotions',

  # Radiology Business
  'field_289': '@get_newsletters',
  'field_295': '@get_promotions',

  # Cardiovascular Business
  'field_290': '@get_newsletters',
  'field_293': '@get_promotions',

  # Health Exec
  'field_267': '@get_newsletters',
  'field_292': '@get_promotions',

  # AI Healthcare
  'field_262': '@get_newsletters',
  'field_291': '@get_promotions'
}


def get_name(members_info, field_name = ''):
  if len(members_info['full_name']) > 2:
    return {
      'first': members_info['merge_fields']['FNAME'],
      'last': members_info['merge_fields']['LNAME'],
      'full': members_info['full_name'],
      'title': members_info['merge_fields']['JOBTITLE'],
      'middle': ''
    }

  return None



def get_state(members_info, field_name = ''):
  state = members_info['merge_fields']['STATE']
  if len(state) > 0:
    for item in state_abbrev:
      if item['name'].upper() == state.upper() or item['abbrev'].upper() == state.upper():
        return {
          'identifier': item['name'],
          'id': item['id']
        }
    
    print(f'Wrong state : "{state}"', members_info['email_address'])

  return ''


def get_country(members_info, field_name = ''):
  country = members_info['merge_fields']['COUNTRY']
  if len(country) > 0:
    for item in countries:
      if item['name'].upper() == country.upper():
        return {
          'identifier': item['name'],
          'id': item['id']
        }
    
    print(f'Wrong country : "{country}"', members_info['email_address'])

  return ''

newsletters_mappings = {
  # Health Imaging
  '31a1719578': {
    '10ec5e2d22': 'Daily & Breaking News',
    'f04fd0a866': 'Weekly News Summary',
    'e9419244b8': 'Monthly News Highlights'
  },
  # Radiology Business
  '342e16db33': {
    '6b0680d4aa': 'Daily & Breaking News',
    '2a015f2199': 'Weekly News Summary',
    '1ac689f32e': 'Monthly News Highlights'
  },
  # Cardiovascular Business
  '8725f4d734': {
    '12f0d0eceb': 'Daily & Breaking News',
    '8c67b1cab3': 'Weekly News Summary',
    'd6214dca85': 'Monthly News Highlights'
  },
  # Health Exec
  'afd9a8e4ef': {
    '8702a7ae5c': 'Daily & Breaking News',
    '183d23dfa5': 'Weekly News Summary',
    'adc980e7e4': 'Monthly News Highlights'
  },
  # # AI Healthcare
  'fdc72b3ec4': {
    '6e7529dd40': 'Daily & Breaking News',
    'd881ca14d8': 'Weekly News Summary',
    'ddca8ec4aa': 'Monthly News Highlights'
  }  
}

def get_newsletters(members_info, field_name = ''):
  list_id = None
  for item in update_fields_mappings:
    if field_name in item['groups_fields']:
      list_id = item['list_id'] 

  sub_mappings = newsletters_mappings[list_id]
  results = []

  for newsletter in sub_mappings.keys():
    if newsletter in members_info['interests']:
      if members_info['interests'][newsletter] == True:
        results.append(sub_mappings[newsletter])

  return results if members_info['list_id'] == list_id else None


promotions_mappings = {
  # Health Imaging
  '31a1719578': {
    'ca55da00a8': 'Announcements', 
    '08c89626d8': 'Webinars & Events'
  },
  # Radiology Business
  '342e16db33': {
    'ddc9654fce': 'Announcements', 
    '14e76fd7fe': 'Webinars & Events'
  },
  # Cardiovascular Business
  '8725f4d734': {
    'b6d7d31829': 'Announcements', 
    '8c9847dfdd': 'Webinars & Events'
  },
  # Health Exec
  'afd9a8e4ef': {
    'bf2c20a135': 'Announcements', 
    'dafa6257b0': 'Webinars & Events'
  },
  # # AI Healthcare
  'fdc72b3ec4': {
    'd881ca14d8': 'Announcements', 
    'd67e5a9aca': 'Webinars & Events'
  }  
}

def get_promotions(members_info, field_name = ''):
  list_id = None
  for item in update_fields_mappings:
    if field_name in item['groups_fields']:
      list_id = item['list_id'] 

  sub_mappings = promotions_mappings[list_id]
  results = []

  for promotion in sub_mappings.keys():
    if promotion in members_info['interests']:
      if members_info['interests'][promotion] == True:
        results.append(sub_mappings[promotion])

  return results if members_info['list_id'] == list_id else None


def get_field_name(field_name):
  mapping = payload_mappings[field_name] if field_name in payload_mappings else ''
  if mapping == '':
    for _list in update_fields_mappings:
      mapping = next((key for key in _list.keys() if _list[key] == field_name), '')
      if mapping != '':
        break

  if mapping[:5] == '@get_':
    return mapping[5:]
  
  if mapping[:1] == '_':
    return mapping[1:]
  
  return mapping
