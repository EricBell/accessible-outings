set dotenv-load

# Deployment entry point
deploy target:
	#!/usr/bin/env bash
	set -e
	echo "Deploying {{target}}..."
	REMOTE_PATH=$(grep "^remote_path" config/{{target}}.toml | cut -d"=" -f2- | sed 's/^ *"//;s/"$//')
	SSH_HOST=$(grep "^ssh_host" config/{{target}}.toml | cut -d"=" -f2- | sed 's/^ *"//;s/"$//')
	RESTART_CMD=$(grep "^restart_cmd" config/{{target}}.toml | cut -d"=" -f2- | sed 's/^ *"//;s/"$//')
	echo "→ rsync to $SSH_HOST:$REMOTE_PATH"
	rsync -avz --delete ./apps/{{target}}/ "$SSH_HOST:$REMOTE_PATH"
	echo "→ restarting: $RESTART_CMD"
	ssh "$SSH_HOST" "$RESTART_CMD"






# Helper "commands" that extract from the toml file
just-remote-path name:
    @grep '^remote_path' config/{{name}}.toml | cut -d'=' -f2- | tr -d ' "'

just-ssh-host name:
    @grep '^ssh_host' config/{{name}}.toml | cut -d'=' -f2- | tr -d ' "'

just-restart-cmd name:
    @grep '^restart_cmd' config/{{name}}.toml | cut -d'=' -f2- | tr -d ' "'
