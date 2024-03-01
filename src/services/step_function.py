import boto3
import json

step_functions_client = boto3.client('stepfunctions')


def start_execution(step_function_arn, name, payload):
  response = step_functions_client.start_execution(
    stateMachineArn = step_function_arn, 
    name = name[:79],
    input = json.dumps(payload)
  )

  return response
