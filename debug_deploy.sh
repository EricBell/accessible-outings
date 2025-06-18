#!/bin/bash
set -e

echo "Debug deploy script"

REMOTE_PATH=$(just just-remote-path myapp)
SSH_HOST=$(just just-ssh-host myapp)
RESTART_CMD=$(just just-restart-cmd myapp)

echo "REMOTE_PATH: '$REMOTE_PATH'"
echo "SSH_HOST: '$SSH_HOST'"
echo "RESTART_CMD: '$RESTART_CMD'"

echo "Combined: '$SSH_HOST:$REMOTE_PATH'"

echo "Testing rsync..."
rsync -avz --delete ./ "$SSH_HOST:$REMOTE_PATH" --exclude=".git" --exclude="instance/" --exclude="__pycache__" --exclude="*.pyc" --exclude=".env" --exclude=".venv"

echo "Testing restart..."
ssh "$SSH_HOST" "$RESTART_CMD"

echo "Deploy completed successfully!"