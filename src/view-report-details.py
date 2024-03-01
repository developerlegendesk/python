from src.services.mappings import get_field_name
from src.utils import render_event_row
from src.services import dynamodb

from datetime import datetime
from base64 import b64decode
import os, json


STATUS_TABLE_NAME = os.environ['STATUS_TABLE_NAME']



def handler(event, context):
  print(event)

  headers = event['headers']
  allow = False

  if 'authorization' in headers:
    value = (headers['authorization'] or '').split(' ')
    if len(value) == 2:
      credentials = b64decode(value[1]).decode('ascii')
      values = dynamodb.query(STATUS_TABLE_NAME, 'USERS')
      values = [
        f'{_v["username"]}:{_v["password"]}' for _v in values
      ]
      if str(credentials) in values:
        allow = True

  if not allow:
    return {
      'statusCode': 401,
      'headers': {
        'WWW-Authenticate': 'Basic realm="Access to Reports Details"',
        'Content-Type': 'text/html'
      },
      'body': 'No access to Reports Details Page'
    }


  routes = event['path'].split('/')

  if (len(routes) > 2):
    if routes[1] == 'reports':
      errors_data = dynamodb.query(STATUS_TABLE_NAME, f'RUN_ERRORS:{routes[2]}', None, False)
      report_data = dynamodb.query(STATUS_TABLE_NAME, f'RUN:{routes[2]}', None, False)
      details = dynamodb.query(STATUS_TABLE_NAME, f'RUN_LOG:{routes[2]}', None, False)

      for index, item in enumerate(report_data):
        report_data[index]['details'] = [
          detail for detail in details if detail['list_id'] == item['SK'][5:]
        ]
    else:
      report_data = []
      errors_data = []
  else:
    report_data = []
    errors_data = []

  debug = False
  if 'queryStringParameters' in event:
    if event['queryStringParameters'] != None and 'debug' in event['queryStringParameters']:
      if event['queryStringParameters']['debug'] == '1':
        debug = True
    
  report_time = datetime.strptime(report_data[0]['PK'][4:]+ ':00', "%Y-%m-%d_%H-%M:%S")

  files_names = [
    'report.html',
    'table.css',
    'start_row.html',
    'list_row.html',
    'detail_row.html',
    'error_row.html'
  ]
  files_content = {}

  for file_name in files_names:
    with open(f'templates/{file_name}', 'r') as file:
      _file_name = file_name.replace('.', '_')
      files_content[_file_name] = file.read()

  if debug:
    files_content['report_html'] = files_content['report_html'].replace('/* results_dump */', json.dumps(report_data + errors_data, indent = 2))
  else:
    files_content['report_html'] = files_content['report_html'].replace('/* results_dump */', '')


  files_content['report_html'] = files_content['report_html'].replace('__report_timestamp__', report_time.strftime('%Y-%m-%d %H:%M:%S').replace(' ', 'T') + 'Z')
  files_content['report_html'] = files_content['report_html'].replace('/* __table.css__ */', files_content['table_css'])

  # files_content['report_html'] = files_content['report_html'].replace('/* __start_event__ */', render_start_row(
  #   files_content['start_row_html'],
  #   {
  #     'entities': ', '.join(report_data[0]['entities']),
  #     'time': report_data[0]['time'].replace(' ', 'T') + 'Z'
  #   }
  # ))


  event_loop_content = ''
  for item in report_data:
    details_body = render_event_row(
        files_content['start_row_html'], 
        {
          'list_id': item['SK'][5:] # item['list_id'],
        },
        ['list_id']
      ) + '\n' if len(item['details']) > 0 else ''

    for detail in item['details']:
      change_defferences = '<br />'.join([
        f'{get_field_name(d["field"])} ({d["field"]}) | {d["prev"]} | {d["actual"]}'
        for d in (detail['defferences'] if 'defferences' in detail else [])
      ])
      if change_defferences != '':
        change_defferences = f'<table class="change-details"><tr><td>{change_defferences}</td></tr></table>'
        change_defferences = change_defferences.replace('<br />', '</td></tr><tr><td>')
        change_defferences = change_defferences.replace(' | ', '</td><td>')

      details_body += render_event_row(
        files_content['detail_row_html'], 
        {
          'is_new': 'is_new' if detail['action'] == 'insert' else '',
          'email': detail['email'],
          'previous_status': detail['previous_status'] if 'previous_status' in detail else '',
          'status': detail['status'],
          'list_id': detail['list_id'],
          'defferences': change_defferences
        },
        ['is_new', 'email', 'previous_status', 'status', 'list_id', 'defferences']
      ) + '\n'

    event_loop_content += render_event_row(
      files_content['list_row_html'], 
      {
        'list_name': item['list_name'],
        'list_id': item['SK'][5:], # item['list_id'],
        'records': f'{int(len(item["details"])):,}',
        'details': details_body,
        'errors': item['errors']
      },
      ['list_name', 'list_id', 'records', 'details', 'errors']
    ) + '\n'

  files_content['report_html'] = files_content['report_html'].replace('/* __events_loop__ */', event_loop_content)

  error_loop_content = ''
  for item in errors_data:
    for error in item['errors']:
      error_loop_content += render_event_row(
        files_content['error_row_html'], 
        {
          'list_name': item['list_name'],
          'message': error['message'] if 'message' in error else '',
          'type': error['type'] if 'type' in error else '',
          'field': error['field'] if 'field' in error else ''
        },
        ['list_name', 'message', 'type', 'field']
    ) + '\n'

  files_content['report_html'] = files_content['report_html'].replace('/* __errors_loop__ */', error_loop_content)
  files_content['report_html'] = files_content['report_html'].replace('__errors_count__', str(len(errors_data)))

  if len(errors_data) == 0:
    files_content['report_html'] = files_content['report_html'].replace('__hide_errors__', 'hidden')


  return {
    'statusCode': 200,
    'headers': {
      'Content-Type': 'text/html'
    },
    'body': files_content['report_html']
  }
