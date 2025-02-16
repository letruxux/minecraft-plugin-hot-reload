# minecraft-plugin-hot-reload

simple hot reload script for minecraft plugins. supports both local and pterodactyl servers.

## setup

create a .env file with your config:

```bash
JAR_OUTPUT_PATH=path/to/your/plugin.jar
RCON_PASSWORD=your_rcon_pass
RCON_PORT=25575
PLUGINS_FOLDER=path/to/plugins
PTERO_API_URL=your_panel_url
PTERO_API_KEY=your_api_key
PTERO_SERVER_ID=your_server_id
```

install requirements:

```bash
pip install -r requirements.txt
```

usage
local server:

```bash
bash python main.py
```

pterodactyl server:

```bash
bash python main.py --ptero
```
