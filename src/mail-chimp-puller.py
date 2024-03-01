from src.services import sqs, s3
from datetime import datetime, timedelta

import os, time
import dateutil.parser as dparser
import mailchimp_marketing as MailchimpMarketing


RECORDS_TO_SYNC_TO_KNACK_QUEUE_URL = os.environ['RECORDS_TO_SYNC_TO_KNACK_QUEUE_URL']
# DATA_BUCKET_NAME = os.environ['DATA_BUCKET_NAME']

MAILCHIMP_API_KEY = os.environ['MAILCHIMP_API_KEY']
MAILCHIMP_SERVER = os.environ['MAILCHIMP_SERVER']


MailChimpClient = MailchimpMarketing.Client()
MailChimpClient.set_config({
  'api_key': MAILCHIMP_API_KEY, 
  'server': MAILCHIMP_SERVER
})


def handler(event, context):
  print('Event : ', event)

  is_initial = event['is_initial'] if 'is_initial' in event else False
  list_size = event['list_size'] if 'list_size' in event else 10
  offset = event['offset'] if 'offset' in event else 0
  list_id = event['list_id']

  since = event['since'] if 'since' in event else 10
  if type(since) == int:
    d = datetime.today() - timedelta(days = since)
    since = d.strftime('%Y-%m-%d') + 'T00:00:00+00:00'

  timer = time.time()
  
  try:
    list_info_response = MailChimpClient.lists.get_list_members_info(
      list_id, 
      count = 1 if is_initial else list_size, 
      offset = offset,
      since_last_changed = since
    )
  except Exception as error:
    print('Error : ', error)
    raise error
  
  print('Pulling records from MC : ' + str(time.time() - timer))

  total_items = list_info_response['total_items']
  print('total_items:', total_items, is_initial)

  records_to_process = []

  if is_initial:
    response = [
      {
        'current_timestamp': event['current_timestamp'],
        'list_id': list_id,
        'offset': step,
        'list_size': list_size,
        'since': since
      }
      for step in range(0, total_items, list_size)
    ]
    print('Total items for list ', list_id, ': ', total_items)

  else:
    if 'members' in list_info_response:
      for member in list_info_response['members']:
        if member.get("merge_fields").get("KNACKDATE") is None:
          if member.get("status") == "subscribed":
            print('No KNACKDATE : ', member)

          records_to_process.append({
            **member, '_links': None
          })

        elif member.get("merge_fields").get("KNACKDATE") < str(
          dparser.parse(member.get("last_changed"), fuzzy=True).date()
        ):
          if member.get("status") == "subscribed":
            print('SMALLER KNACKDATE : ', member)

          records_to_process.append({
            **member, '_links': None
          })

      print('Number of pulled records : ', len(list_info_response['members']), 'of', total_items)
    else:
      print(list_info_response)

    timer = time.time()

    sqs.send_messages(RECORDS_TO_SYNC_TO_KNACK_QUEUE_URL, records_to_process)
    print('Submitting records to process : ' + str(time.time() - timer), len(records_to_process))


    response = {
      'records_to_process': len(records_to_process),
      'current_timestamp': event['current_timestamp']
    }


  return response
