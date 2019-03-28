#!/usr/bin/env bash

mkdir -p log

if [ -e ./.env ]; then
  source .env
else
  echo "Error, please add a .env file (copy .env.sample and fill in)"
  exit 1
fi

watchmedo auto-restart -p '*.py' python3 ecupdate.py
