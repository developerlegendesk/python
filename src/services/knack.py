from src.services import mappings

import os, json
import requests

KNACK_API_KEY = os.environ['KNACK_API_KEY'] if 'KNACK_API_KEY' in os.environ else ''
KNACK_APP_ID = os.environ['KNACK_APP_ID'] if 'KNACK_APP_ID' in os.environ else ''

headers = {
  'X-Knack-Application-Id': KNACK_APP_ID,
  'X-Knack-REST-API-Key': KNACK_API_KEY
}

tb_object = 'object_14'



def get_knack_filter_string(email_id, field = 'field_64'):
  results = {
    'match': 'and',
    'rules': [
      {
        'field': field, 
        'operator': 'is',
        'value': email_id
      }
    ]
  }

  return json.dumps(results)


def get_knock_objects_per_email_id(email_id):
  try:
    filter_set = get_knack_filter_string(email_id)
    url = f'https://api.knack.com/v1/objects/{tb_object}/records/?filters={filter_set}'
    response = requests.request('GET', url, headers = headers)

    if response.status_code == 429:
      print(
        f'get_knock_objects_per_email_id() :: [{email_id}] :: [Error] :: [{response.text}]'
      )

      return False

    knack_data = json.loads(response.text)

    if 'records' not in knack_data:
      print(
        f'get_knock_objects_per_email_id() :: [Record not found in Knack DB corresponding to {email_id} account]'
      )

      return []
    
    return knack_data['records']
  
  except Exception as e:
    print('[get_knock_objects_per_email_id()] :: [error] ::', e)

    return []


stauses = {
  'subscribed': 'Active',
  'cleaned': 'Cleaned',
  'unsubscribed': 'Unsubscribed',
  'pending': 'Pending'
}

def calculate_update_payload(list_id, status, update, cleaned = None, unsub = None, active = None):
  _mappings = None
  for item in mappings.update_fields_mappings:
    if item['list_id'] == list_id:
      _mappings = item
      break
  
  payload = {
    _mappings['status']: stauses[status], # 'Active' if 'active' == 'subscribed' else status,
    _mappings['update']: update
  }

  if cleaned != None:
    payload[_mappings['cleaned']] = cleaned

  if unsub != None:
    payload[_mappings['unsub']] = unsub

  if active != None:
    payload[_mappings['active']] = active


  return payload



def get_payload(members_info):
  payload = calculate_update_payload(
    members_info['list_id'],
    members_info['status'],
    members_info['last_changed'],
    cleaned = members_info['last_changed'] if members_info['status'] == 'cleaned' else None,
    unsub = members_info['last_changed'] if members_info['status'] == 'unsubscribed' else None,
    active = members_info['last_changed'] if members_info['status'] == 'subscribed' else None
  )

  for key in mappings.payload_mappings.keys():
    if mappings.payload_mappings[key][:1] == '@':
      value = getattr(mappings, mappings.payload_mappings[key][1:])(members_info, key)
    elif mappings.payload_mappings[key][:1] == '_':
      value = members_info['merge_fields'][mappings.payload_mappings[key][1:]]
    else:
      value = members_info[mappings.payload_mappings[key]]
      
    if value != None:
      payload = {
        key: value,
        **payload
      }

  return payload




def update_knack_object_per_id(knack_record_id, members_info):
  url = f'https://api.knack.com/v1/objects/{tb_object}/records/{knack_record_id}'
  payload = get_payload(members_info)
  print('UPDATE PAYLOAD : ', payload)

  try:
    response = requests.request(
      'PUT', 
      url, 
      headers = { **headers, 'Content-Type': 'application/json' },
      data = json.dumps(payload)
    )
    if response.status_code == 200:
      return True
    
    print('Update_knack_record() :: [response] :: ', response.status_code, response.text)
    return json.loads(response.text)
    
  except Exception as e:
    print('Update_knack_record() :: [error] :: ', e)

    return False


def insert_knack_object(members_info):
  url = f'https://api.knack.com/v1/objects/{tb_object}/records'
  payload = get_payload(members_info)
  print('INSERT PAYLOAD : ', payload)

  try:
    response = requests.request(
      'POST', 
      url, 
      headers = { **headers, 'Content-Type': 'application/json' },
      data = json.dumps(payload)
    )
    if response.status_code == 200:
      return True
    
    print('Insert_knack_object() :: [response] :: ', response.status_code, response.text)
    return json.loads(response.text)
    
  except Exception as e:
    print('Insert_knack_object() :: [error] :: ', e)

    return False


def pull_lookup_data(name, object):
  url = f'https://api.knack.com/v1/objects/{object}/records/?rows_per_page=1000'

  response = requests.request('GET', url, headers = headers)
  print(response.text)
