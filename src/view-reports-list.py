from src.utils import render_event_row
from src.services.mappings import update_fields_mappings
from src.services import dynamodb

import os, json, datetime


STATUS_TABLE_NAME = os.environ['STATUS_TABLE_NAME']



def handler(event, context):
  print(event)

  routes = event['path'].split('/')

  if (len(routes) > 1):
    if routes[1] == 'reports':
      report_data = dynamodb.query(STATUS_TABLE_NAME, 'LIST_OF_RUNS', None, False)
    else:
      report_data = []
  else:
    report_data = []

  debug = False
  if 'queryStringParameters' in event:
    if event['queryStringParameters'] != None and 'debug' in event['queryStringParameters']:
      if event['queryStringParameters']['debug'] == '1':
        debug = True
  
  files_names = [
    'reports_list.html',
    'table.css',
    'report_list_row.html'
  ]
  files_content = {}

  for file_name in files_names:
    with open(f'templates/{file_name}', 'r') as file:
      _file_name = file_name.replace('.', '_')
      files_content[_file_name] = file.read()

  if debug:
    files_content['reports_list_html'] = files_content['reports_list_html'].replace('/* results_dump */', json.dumps(report_data, indent = 2))
  else:
    files_content['reports_list_html'] = files_content['reports_list_html'].replace('/* results_dump */', '')

  
  files_content['reports_list_html'] = files_content['reports_list_html'].replace('/* __table.css__ */', files_content['table_css'])
  files_content['reports_list_html'] = files_content['reports_list_html'].replace('__ENV__', os.environ['ENV'])


  event_loop_content = ''
  for item in report_data:
    the_date = datetime.datetime.strptime(item['SK'] + '-00+0000', '%Y-%m-%d_%H-%M-%S%z')
    since = str(item['since']) if 'since' in item else ''
    lists = [
      next(name['abrv'] for name in update_fields_mappings if name['list_id'] == list_id)
      for list_id in item['lists']
    ]

    event_loop_content += render_event_row(
      files_content['report_list_row_html'], 
      {
        'timestamp2': the_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'timestamp1': item['SK'],
        'lists': ', '.join(lists),
        'records': f'{int(item["records"] if "records" in item else 0):,}',
        'errors': f'{int(item["errors"] if "errors" in item else 0):,}',
        'since': since if since != 'None' else 'RESET'
      },
      ['timestamp1', 'timestamp2', 'lists', 'records', 'since', 'errors']
    ) + '\n'

  files_content['reports_list_html'] = files_content['reports_list_html'].replace('/* __events_loop__ */', event_loop_content)


  return {
    'statusCode': 200,
    'headers': {
      'Content-Type': 'text/html'
    },
    'body': files_content['reports_list_html']
  }
