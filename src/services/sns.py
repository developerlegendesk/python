import boto3
import json

sns = boto3.client('sns')


def publish_message(topic_arn, message_object):
  response = sns.publish(
    TargetArn = topic_arn, 
    Message = json.dumps({ 'default': json.dumps(message_object) }),
    MessageStructure = 'json'
  )

  return response
