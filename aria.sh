#!/usr/bin/env bash
if [ -x /usr/local/bin/aria.sh ]; then
    exec /usr/local/bin/aria.sh "$@"
elif [ -x /usr/bin/aria.sh ]; then
    exec /usr/bin/aria.sh "$@"
elif [ -x /aria.sh ]; then
    exec /aria.sh "$@"
fi