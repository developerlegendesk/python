from src.services import step_function, dynamodb
from src.utils import ttl

from datetime import datetime
import os


ORCHESTRATION_STATE_MACHINE_ARN = os.environ['ORCHESTRATION_STATE_MACHINE_ARN']
STATUS_TABLE_NAME = os.environ['STATUS_TABLE_NAME']


def handler(event, context):
  current_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M') # current date and time
  print('Event : ', event)

  list_size = event['list_size'] if 'list_size' in event else 950
  since = event['since'] if 'since' in event else 10
  list_ids = event['list_ids'] # array

  state_machine_payload = {
    'current_timestamp': current_timestamp,
    'list_ids': list_ids,
    'list_size': list_size,
    'lists': [
      {
        'current_timestamp': current_timestamp,
        'list_id': list_id,
        'list_size': list_size,
        'since': since
      }
      for list_id in list_ids
    ]
    # add offset from second branch
  }

  response = step_function.start_execution(
    ORCHESTRATION_STATE_MACHINE_ARN,
    f'{len(list_ids)}_lists_at_{current_timestamp}',
    state_machine_payload
  )

  dynamodb.put_item(STATUS_TABLE_NAME, {
    'PK': 'LIST_OF_RUNS',
    'SK': f'{current_timestamp}',
    'lists': list_ids,
    'since': since,
    'ttl': ttl(91)
  })

  # print(response)

  return state_machine_payload
