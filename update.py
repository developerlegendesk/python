from src.services.dynamodb import update_item, query, put_item, delete_item
import sys, datetime
from time import strftime, localtime, time
from src.utils import ttl


STATUS_TABLE_NAME = 'mc-2-knock-1-prod-status'


logs = query(STATUS_TABLE_NAME, 'RUN_LOG:', None, False)
runs = query(STATUS_TABLE_NAME, 'LIST_OF_RUNS', None, False)
print(len(logs), len(runs))


for log in logs[:21]:
  run_time_ttl = ttl(100)
  run_time = ''
  # print(run_time, run_time_ttl)

  for run in runs:
    if log['ttl'] < run_time_ttl and run['ttl'] < log['ttl']:
      run_time_ttl = run['ttl']
      run_time = run['SK']
      # print(
      #   log['ttl'], 
      #   datetime.datetime.utcfromtimestamp(log['ttl'] - 91 * 24 * 60 * 60).strftime('%c'), 
      #   run['SK'], run_time
      # )

  put_item(STATUS_TABLE_NAME, {
    **log,
    'PK': f'RUN_LOG:{run_time}'
  })
  delete_item(STATUS_TABLE_NAME, {
    'PK': log['PK'],
    'SK': log['SK']
  })


runs = query(STATUS_TABLE_NAME, 'LIST_OF_RUNS', None, False)

for run in runs:
  details = query(STATUS_TABLE_NAME, f'RUN_LOG:{run["SK"]}', None, False)
  records_count = len(details)
  print(run['PK'], run['SK'], run['records'], records_count)

  update_item(
    STATUS_TABLE_NAME, 
    {
      'PK': 'LIST_OF_RUNS',
      'SK': run['SK']
    },
    {
      'records': records_count
    }  
  )
