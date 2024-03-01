import boto3
import json, decimal


s3 = boto3.resource('s3')

class DecimalEncoder(json.JSONEncoder):

  def default(self, o):
    if isinstance(o, decimal.Decimal):
      if o % 1 > 0:
        return float(o)
      else:
        return int(o)
      
    return super(DecimalEncoder, self).default(o)
    
    

def put_object_as_text(bucket_name, key, content):
  bucket = s3.Bucket(bucket_name)
  response = bucket.put_object(Key = key, Body = content)

  return response


def put_object_as_json(bucket_name, key, items):
  return put_object_as_text(bucket_name, key, json.dumps(items, cls = DecimalEncoder))


def get_object_as_text(bucket_name, key, decode = 'utf-8'):
  obj = s3.Object(bucket_name, key).get()
  response = obj['Body'].read().decode(decode)

  return response


def list_objects(bucket_name, prefix = ''):
  s3_client = boto3.client('s3')

  response = s3_client.list_objects_v2(
    Bucket = bucket_name,
    Prefix = prefix
  )

  if 'Contents' in response:
    return [
      item['Key'] for item in response['Contents']
    ]
  else:
    return []


def download(bucket_name, key, file_name):
  bucket = s3.Bucket(bucket_name)
  bucket.download_file(key, f'/tmp/{file_name}')


def upload(file_name, bucket_name, key):
  bucket = s3.Bucket(bucket_name)
  bucket.upload_file(f'/tmp/{file_name}', key)
