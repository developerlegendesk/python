from src.services.mappings import update_fields_mappings
from src.services import sns, sqs, knack, dynamodb
from src.utils import ttl
# from datetime import datetime
import os, json

RECORDS_TO_SYNC_TO_MAIL_CHIMP_QUEUE_URL = os.environ['RECORDS_TO_SYNC_TO_MAIL_CHIMP_QUEUE_URL']
PUSH_AGAIN_TOPIC_ARN = os.environ['PUSH_AGAIN_TOPIC_ARN']
STATUS_TABLE_NAME = os.environ['STATUS_TABLE_NAME']


def handler(event, context):
  RECORDS_TO_SYNC_TO_KNACK_QUEUE_URL = os.environ['RECORDS_TO_SYNC_TO_KNACK_QUEUE_URL']
  save_errors = 'save_errors' in event and event['save_errors'] == True

  if save_errors:
    RECORDS_TO_SYNC_TO_KNACK_QUEUE_URL = os.environ['RECORDS_TO_SYNC_TO_KNACK_QUEUE_URL_DLQ']    

  action_messages = sqs.receive_message(RECORDS_TO_SYNC_TO_KNACK_QUEUE_URL, 10)
  print('pulled messages : ', len(action_messages))
  current_timestamp = event['current_timestamp'] if 'current_timestamp' in event else ''
  if 'Records' in event:
    Message = json.loads(event['Records'][0]['Sns']['Message'])
    current_timestamp = Message['current_timestamp']

  successes = []
  for action_message in action_messages:
    members_info = json.loads(action_message['Body'])
    records = knack.get_knock_objects_per_email_id(members_info['email_address'])
    
    if records == False:
      print('Records == False : ', members_info)
      continue

    if len(records) < 1:
      print('Records len < 0 : ', members_info)
      response = knack.insert_knack_object(members_info)

      if response == True:
        successes.append(action_message['ReceiptHandle'])
        sqs.send_message(RECORDS_TO_SYNC_TO_MAIL_CHIMP_QUEUE_URL, members_info)
        dynamodb.put_item(STATUS_TABLE_NAME, {
          'PK': f'RUN_LOG:{current_timestamp}',
          'SK': f'{members_info["list_id"]}:{members_info["email_address"]}',
          'list_id': members_info['list_id'],
          'email': members_info["email_address"],
          'status': knack.stauses[members_info['status']],
          'action': 'insert',
          'ttl': ttl(91)
        })

      elif save_errors:
        list_name = next(name['name'] for name in update_fields_mappings if name['list_id'] == members_info["list_id"])

        dynamodb.put_item(STATUS_TABLE_NAME, {
          'PK': f'RUN_ERRORS:{current_timestamp}',
          'SK': f'{members_info["list_id"]}:{members_info["email_address"]}',
          'list_name': list_name,
          'errors': response['errors'] if 'errors' in response else [],
          'ttl': ttl(91)
        })
        successes.append(action_message['ReceiptHandle'])

    else:
      knack_record_id = records[0]['id']
      response = knack.update_knack_object_per_id(knack_record_id, members_info)

      if response == True:
        successes.append(action_message['ReceiptHandle'])
        sqs.send_message(RECORDS_TO_SYNC_TO_MAIL_CHIMP_QUEUE_URL, members_info)

        status_field_name = next(name['status'] for name in update_fields_mappings if name['list_id'] == members_info["list_id"])
        previous_status = records[0][status_field_name] if status_field_name in records[0] else '.'

        payload = knack.get_payload(members_info)
        
        newsletters_keys = ['283', '289', '290', '267', '262']
        promotions_keys = ['294', '295', '293', '292', '291']
        dates_keys = [
          '167',
          '299', '252', '260', '256',
          '300', '253', '261', '257',
          '298', '250', '259', '255',
          '297', '251', '258', '254',
          '296', '243', '245', '244'
        ]
        diff = []

        for key in payload.keys():
          if key[-3:] in newsletters_keys + promotions_keys:
            actual = ', '.join(payload[key])
          
          # email
          elif key[-3:] == '_64':
            actual = f'<a href=\"mailto:{str(payload[key]).lower()}\">{str(payload[key]).lower()}</a>'
          
          # LINKEDIN
          elif key[-3:] == '229':
            actual = f'<a href=\"{payload[key]}\" target=\"_blank\">{payload[key]}</a>'
            
          # dates
          elif key[-3:] in dates_keys:
            parts = (payload[key][:10]).split('-')
            actual = f'{parts[1]}/{parts[2]}/{parts[0]} {payload[key][11:16]}'
          
          # state
          elif key[-3:] == '184':
            state_name = payload[key]['identifier'] if 'identifier' in payload[key] else ''
            state_id = payload[key]['id'] if 'id' in payload[key] else ''
            actual = f'<span class=\"{state_id}\">{state_name}</span>'
            if state_id == '' and state_name == '':
              actual = ''
          # country
          elif key[-3:] == '179':
            country_name = payload[key]['identifier'] if 'identifier' in payload[key] else ''
            country_id = payload[key]['id'] if 'id' in payload[key] else ''
            actual = f'<span class=\"{country_id}\">{country_name}</span>'
            if country_id == '' and country_name == '':
              actual = ''
          # name from full
          elif key[-3:] == '_63':
            actual = payload[key]['full'] if 'full' in payload[key] else ''
          else:
            actual = payload[key]

          # print('actual : ', key, actual, records[0][key])

          if records[0][key] != actual:
            diff.append({
              'field': key,
              'prev': records[0][key],
              'actual': actual
            })

        dynamodb.put_item(STATUS_TABLE_NAME, {
          'PK': f'RUN_LOG:{current_timestamp}',
          'SK': f'{members_info["list_id"]}:{members_info["email_address"]}',
          'list_id': members_info['list_id'],
          'email': members_info["email_address"],
          'status': knack.stauses[members_info['status']],
          'previous_status': previous_status,
          'action': 'update',
          'defferences': diff,
          'ttl': ttl(91)
        })

      elif save_errors:
        list_name = next(name['name'] for name in update_fields_mappings if name['list_id'] == members_info["list_id"])

        dynamodb.put_item(STATUS_TABLE_NAME, {
          'PK': f'RUN_ERRORS:{current_timestamp}',
          'SK': f'{members_info["list_id"]}:{members_info["email_address"]}',
          'list_name': list_name,
          'errors': response['errors'] if 'errors' in response else [],
          'ttl': ttl(91)
        })
        successes.append(action_message['ReceiptHandle'])
  
  
  sqs.delete_messages(RECORDS_TO_SYNC_TO_KNACK_QUEUE_URL, successes)
  remaining = sqs.get_messages_count(RECORDS_TO_SYNC_TO_KNACK_QUEUE_URL)

  messages_in_flight = int(remaining['messages_in_flight']) 
  messages_in_queue = int(remaining['messages_in_queue'])

  if messages_in_flight + messages_in_queue > 0:
    if messages_in_flight < messages_in_queue:
      if messages_in_flight < 145:
        sns.publish_message(PUSH_AGAIN_TOPIC_ARN, {'current_timestamp': current_timestamp})

    if messages_in_queue > 100:
      sns.publish_message(PUSH_AGAIN_TOPIC_ARN, {'current_timestamp': current_timestamp})

  if 'trigger' in event and event['trigger'] == True:
    return event
  
  return {
    'remaining': messages_in_flight + messages_in_queue,
    'waiting': messages_in_flight > messages_in_queue,
    **remaining
  }
