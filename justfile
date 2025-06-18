set dotenv-load

# Deployment entry point
deploy target:
	#!/bin/bash
	echo "Deploying {{target}}..."
	set -e
	REMOTE_PATH=$(just just-remote-path {{target}})
	SSH_HOST=$(just just-ssh-host {{target}})
	RESTART_CMD=$(just just-restart-cmd {{target}})
	echo "→ syncing to $SSH_HOST:$REMOTE_PATH"
	rsync -avz --delete ./ "$SSH_HOST:$REMOTE_PATH" --exclude=".git" --exclude="instance/" --exclude="__pycache__" --exclude="*.pyc" --exclude=".env" --exclude=".venv"
	echo "→ restarting with: $RESTART_CMD"
	ssh "$SSH_HOST" "$RESTART_CMD"







# Helper "commands" that extract from the toml file
just-remote-path name:
    @grep '^remote_path' config/{{name}}.toml | cut -d'=' -f2- | tr -d ' "'

just-ssh-host name:
    @grep '^ssh_host' config/{{name}}.toml | cut -d'=' -f2- | tr -d ' "'

just-restart-cmd name:
    @grep '^restart_cmd' config/{{name}}.toml | cut -d'=' -f2- | tr -d '"' | sed 's/^ *//'
