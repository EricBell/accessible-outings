#!/bin/bash
pkill -f app.py || true
sleep 2
cd /home/accessibleoutings/public_html/flaskapp/apps/myapp
source ../../.venv/bin/activate
pip install -r requirements.txt
PORT=5100 nohup python app.py > ../../app.log 2>&1 &
echo "App restarted"