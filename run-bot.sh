#!/usr/bin/env bash

if [ -e ./.env ]; then
  source .env
else
  echo "Error, please add a .env file (copy .env.sample and fill in)"
  exit 1
fi

python3 ./ecupdate.py
