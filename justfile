set dotenv-load

# Deployment entry point
deploy target:
	echo "Deploying {{target}}..."
	rsync -avz --delete ./ "accessibleoutings@50.116.57.169:/home/accessibleoutings/public_html/flaskapp/" --exclude=".git" --exclude="instance/" --exclude="__pycache__" --exclude="*.pyc" --exclude=".env" --exclude=".venv"
	ssh "accessibleoutings@50.116.57.169" "sed -i 's/\r$//' /home/accessibleoutings/public_html/flaskapp/restart.sh && chmod +x /home/accessibleoutings/public_html/flaskapp/restart.sh && bash /home/accessibleoutings/public_html/flaskapp/restart.sh"







# Helper "commands" that extract from the toml file
just-remote-path name:
    @grep '^remote_path' config/{{name}}.toml | cut -d'=' -f2- | tr -d ' "'

just-ssh-host name:
    @grep '^ssh_host' config/{{name}}.toml | cut -d'=' -f2- | tr -d ' "'

just-restart-cmd name:
    @grep '^restart_cmd' config/{{name}}.toml | cut -d'=' -f2- | tr -d '"' | sed 's/^ *//'
