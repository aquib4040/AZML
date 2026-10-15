#!/bin/bash
# Capture dynamic PORT provided by Heroku or cloud runtime before anything else
HEROKU_PORT="${PORT}"

rm -f *.session *.session-journal *.session*

# If .env exists locally (e.g. copied during docker build), source it
if [ -f .env ]; then
  set -a
  source .env
  set +a
elif [ -n "$BOT_TOKEN" ]; then
  # Auto-generate .env from environment variables if deployed via Heroku config vars
  cat <<EOF > .env
BOT_TOKEN=${BOT_TOKEN}
OWNER_ID=${OWNER_ID}
TELEGRAM_API=${TELEGRAM_API}
TELEGRAM_HASH=${TELEGRAM_HASH}
DATABASE_URL=${DATABASE_URL}
EOF
  if [ -n "$BASE_URL" ]; then
    echo "BASE_URL=${BASE_URL}" >> .env
  fi
fi

if [ -f config.env ]; then
  set -a
  source config.env 2>/dev/null || true
  set +a
fi

if [ -n "$HEROKU_APP_NAME" ] && [ -z "$BASE_URL" ]; then
  export BASE_URL="https://${HEROKU_APP_NAME}.herokuapp.com"
fi

# Always prioritize dynamic port given by Heroku / cloud environments over hardcoded ports
if [ -n "$HEROKU_PORT" ]; then
  export PORT="$HEROKU_PORT"
  export BASE_URL_PORT="$HEROKU_PORT"
else
  export PORT="${PORT:-85}"
  export BASE_URL_PORT="${BASE_URL_PORT:-$PORT}"
fi

python3 update.py && python3 -m bot

