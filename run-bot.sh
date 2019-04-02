#!/usr/bin/env bash

mkdir -p log

if [ -e ./.env ]; then
  source .env
else
  echo "Error, please add a .env file (copy .env.sample and fill in)"
  exit 1
fi


check_for_updates(){
  sleep 10
  while ps axo cmd | grep "^python3 ecupdate.py$" > /dev/null; do
    git pull > /dev/null
    sleep 15
  done
}
check_for_updates &

while sleep 1; do
  python3 ecupdate.py || exit 1
done
