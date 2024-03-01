from src.services import sns, sqs
from datetime import date
import os, json

from mailchimp_marketing.api_client import ApiClientError
import mailchimp_marketing as MailchimpMarketing


RECORDS_TO_SYNC_TO_MAIL_CHIMP_QUEUE_URL = os.environ['RECORDS_TO_SYNC_TO_MAIL_CHIMP_QUEUE_URL']
PUSH_AGAIN_TOPIC_ARN = os.environ['PUSH_AGAIN_TOPIC_ARN']

MAILCHIMP_API_KEY = os.environ['MAILCHIMP_API_KEY']
MAILCHIMP_SERVER = os.environ['MAILCHIMP_SERVER']

MailChimpClient = MailchimpMarketing.Client()
MailChimpClient.set_config({
  'api_key': MAILCHIMP_API_KEY, 
  'server': MAILCHIMP_SERVER
})


def handler(event, context):
  action_messages = sqs.receive_message(RECORDS_TO_SYNC_TO_MAIL_CHIMP_QUEUE_URL, 10)

  successes = []
  for action_message in action_messages:
    members_info = json.loads(action_message['Body'])
    
    try:
      ORGTYPE_VALUE = members_info['merge_fields']['ORGTYPE'] if 'ORGTYPE' in members_info['merge_fields'] else False
      ORGTYPE = {
        'ORGTYPE': 'Select' if '- Select -' in ORGTYPE_VALUE else ORGTYPE_VALUE
      } if ORGTYPE_VALUE != False else {}

      response = MailChimpClient.lists.set_list_member(
        members_info['list_id'],
        members_info['email_address'],
        {
          'merge_fields': {
            'KNACKCHANG': members_info['last_changed'],
            'KNACKDATE': str(date.today()),
            **ORGTYPE
          }
        }
      )

      successes.append(action_message['ReceiptHandle'])
      print('response : ', response)

    except ApiClientError as error:
      print('Error: {}'.format(error.text))
  
  
  sqs.delete_messages(RECORDS_TO_SYNC_TO_MAIL_CHIMP_QUEUE_URL, successes)
  remaining = sqs.get_messages_count(RECORDS_TO_SYNC_TO_MAIL_CHIMP_QUEUE_URL)

  messages_in_flight = int(remaining['messages_in_flight']) 
  messages_in_queue = int(remaining['messages_in_queue'])

  if messages_in_flight + messages_in_queue > 0:
    if messages_in_flight < messages_in_queue:
      if messages_in_flight < 45:
        sns.publish_message(PUSH_AGAIN_TOPIC_ARN, {})

  return {
    'remaining': messages_in_flight + messages_in_queue,
    'waiting': messages_in_flight > messages_in_queue,
    **remaining
  }
