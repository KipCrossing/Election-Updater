#!/usr/bin/env bash

echo "will start after 60s"

while sleep 60; do
  git pull
  ./run-bot.sh
done

