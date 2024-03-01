#!/bin/bash

LAYER_NAME="$1"
AWS_REGION="$2"
S3_BUCKET_NAME="$3"

aws lambda publish-layer-version \
  --layer-name $LAYER_NAME \
  --region $AWS_REGION \
  --content S3Bucket=$S3_BUCKET_NAME,S3Key=layers/$LAYER_NAME.zip


  # --compatible-runtimes python3.11 \
