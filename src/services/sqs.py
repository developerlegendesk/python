# from multiprocessing.pool import Pool
import boto3
import json

sqs = boto3.client('sqs')


def send_message(queue_url, message_object):
  response = sqs.send_message(
    QueueUrl = queue_url, 
    MessageBody = json.dumps(message_object)
  )

  return response


def send_messages(queue_url, messages):
  max_batch_size = 10 # current maximum allowed
  chunks = [messages[x:x + max_batch_size] for x in range(0, len(messages), max_batch_size)]

  for chunk in chunks:
    entries = []

    for index, message_object in enumerate(chunk):
      entry = {
        'MessageBody': json.dumps(message_object),
        'Id': str(index)
      }
      entries.append(entry)

    sqs.send_message_batch(
      QueueUrl = queue_url,
      Entries = entries
    )


def receive_message(queue_url, max_messages = 10):
  response = sqs.receive_message(
    QueueUrl = queue_url,
    MaxNumberOfMessages = max_messages
  )

  return response['Messages'] if 'Messages' in response else []


def delete_messages(queue_url, ids = []):
  max_batch_size = 10 # current maximum allowed
  chunks = [ids[x:x + max_batch_size] for x in range(0, len(ids), max_batch_size)]

  for chunk in chunks:
    entries = []

    for index, message_receipt_handle in enumerate(chunk):
      entry = {
        'ReceiptHandle': str(message_receipt_handle),
        'Id': str(index)
      }
      entries.append(entry)

    sqs.delete_message_batch(
      QueueUrl = queue_url,
      Entries = entries
    )


def get_messages_count(queue_url):
  response = sqs.get_queue_attributes(
    QueueUrl = queue_url,
    AttributeNames = [
      'ApproximateNumberOfMessagesNotVisible',
      'ApproximateNumberOfMessages'
    ]
  )

  if 'Attributes' in response:
    return {
      'messages_in_flight': response['Attributes']['ApproximateNumberOfMessagesNotVisible'],
      'messages_in_queue': response['Attributes']['ApproximateNumberOfMessages']
    }
  
  return False
