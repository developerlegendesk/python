import boto3
from boto3.dynamodb.conditions import Key
import decimal, json, os

REGION_NAME = os.environ['REGION_NAME']

dynamodb = boto3.resource('dynamodb', region_name = REGION_NAME)


class DecimalEncoder(json.JSONEncoder):

  def default(self, o):
    if isinstance(o, decimal.Decimal):
      if o % 1 > 0:
        return float(o)
      else:
        return int(o)
      
    return super(DecimalEncoder, self).default(o)



def put_item(table_name, item):
  table = dynamodb.Table(table_name)
  response = table.put_item(Item = item)

  return response


def query(table_name, pk, sk = None, ascending = True):
  search_criteria = Key('PK').eq(pk) if sk is None else Key('PK').eq(pk) & Key('SK').eq(sk)
  table = dynamodb.Table(table_name)
  response = table.query(
    KeyConditionExpression = search_criteria,
    ScanIndexForward = ascending
  )

  results = [
    { key : val for key, val in Item.items() if key != 'ttl__' } 
    for Item in (response['Items'] if 'Items' in response else [])
  ]

  return json.loads(json.dumps(results, cls = DecimalEncoder))


def update_item(table_name, record_key, items):
   table = dynamodb.Table(table_name)
   update_expression = ['set ']
   update_values = dict()

   for key, val in items.items():
     update_expression.append(f' {key} = :{key},')
     update_values[f':{key}'] = val

   response = table.update_item(
     Key = record_key,
     UpdateExpression = ''.join(update_expression)[:-1],
     ExpressionAttributeValues = dict(update_values)
   )

   return response


def delete_item(table_name, record_key):
  table = dynamodb.Table(table_name)
  table.delete_item(
     Key = record_key
  )
