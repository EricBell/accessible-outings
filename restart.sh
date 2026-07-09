#!/bin/bash
pkill -f app.py || true
sleep 2
cd /home/accessibleoutings/public_html/flaskapp/apps/myapp
uv sync --frozen --no-dev
PORT=5100 nohup uv run python app.py > ../../app.log 2>&1 &
echo "App restarted"