#!/bin/bash
export PORT=${PORT:-85}

rm -f *.session *.session-journal *.session*

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

python3 update.py && python3 -m bot
