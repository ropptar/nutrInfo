#!/bin/bash
SCRIPT_DIR="$(dirname "$0")"
PROJECT_ROOT="$SCRIPT_DIR/.."

echo Downloading FoodSeg103 Dataset...
curl -L --fail -o $PROJECT_ROOT/data/raw/foodseg103.zip https://www.kaggle.com/api/v1/datasets/download/fontainenathan/foodseg103 \
	&& echo FoodSeg103 Acquired... \
	|| { echo Download Failure!; rm -f $PROJECT_ROOT/data/raw/foodseg103.zip; exit 1; }

echo Ready
