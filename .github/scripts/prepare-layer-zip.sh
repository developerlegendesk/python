#!/bin/bash

FOLDERS_TO_INCLUDE="$2"
LAYER_NAME="$1"

IFS=',' read -ra FOLDERS_TO_INCLUDE_LIST <<< "$FOLDERS_TO_INCLUDE"


mkdir -p layers/$LAYER_NAME/python

for element in "${FOLDERS_TO_INCLUDE_LIST[@]}"; do
  echo "Folder: $element"
  cp -r layers_packages/$element layers/$LAYER_NAME/python
done

cd layers/$LAYER_NAME
zip -r ../../python_"$LAYER_NAME"_layer.zip .
cd ../..
ls -l
