from src.services import dynamodb
import os


STATUS_TABLE_NAME = os.environ['STATUS_TABLE_NAME']


def handler(event, context):
  print(event)
  current_timestamp = event['current_timestamp']


  runs = dynamodb.query(
    STATUS_TABLE_NAME,
    f'RUN:{current_timestamp}'
  )
  records_sum = sum([ item['records'] for item in runs ])

  errors = dynamodb.query(
    STATUS_TABLE_NAME,
    f'RUN_ERRORS:{current_timestamp}'
  )
  # calculate errors

  dynamodb.update_item(
    STATUS_TABLE_NAME,
    {
      'PK': 'LIST_OF_RUNS',
      'SK': current_timestamp
    },
    {
      'records': records_sum,
      'errors': len(errors)
    }
  )

  return True
