from src.services.mappings import update_fields_mappings
from src.services import dynamodb
from src.utils import ttl
import os

STATUS_TABLE_NAME = os.environ['STATUS_TABLE_NAME']



def handler(event, context):
  print(event)
  list_name = next(name['name'] for name in update_fields_mappings if name['list_id'] == event['list_id'])
  records_sum = sum([ item['records_to_process'] for item in event['pull_results'] ])

  dynamodb.put_item(
    STATUS_TABLE_NAME,
    {
      'PK': f'RUN:{event["current_timestamp"]}',
      'SK': f'LIST:{event["list_id"]}',
      'records': records_sum,
      'list_name': list_name,
      'list_id': event['list_id'],
      'errors': 0,
      'ttl': ttl(91)
    }
  )

  return True
