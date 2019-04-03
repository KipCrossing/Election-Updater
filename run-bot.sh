#!/usr/bin/env bash

GECKODRIVER_URL="https://github.com/mozilla/geckodriver/releases/download/v0.21.0/geckodriver-v0.21.0-linux64.tar.gz"

mkdir -p log

if [ -e ./.env ]; then
  source .env
else
  echo "Error, please add a .env file (copy .env.sample and fill in)"
  exit 1
fi


if [ ! -e ./geckodriver ]; then
  wget "$GECKODRIVER_URL" \
    -O gd.tar.gz
  tar zxvf gd.tar.gz
  rm gd.tar.gz
fi


check_for_updates(){
  sleep 10
  while ps axo cmd | grep "^python3 ecupdate.py$" > /dev/null; do
    git pull > /dev/null
    sleep 15
  done
}
check_for_updates &

# needed for headless FF driver
export MOZ_HEADLESS="1"

which python3.6 > /dev/null && PYEXE="python3.6" || PYEXE="python3"

while sleep 1; do
  $PYEXE ecupdate.py || exit 1
done

