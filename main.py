import time
import shutil
import os
import argparse
from pathlib import Path
from mcrcon import MCRcon
from pydactyl import PterodactylClient
from dotenv import load_dotenv

load_dotenv()

JAR_OUTPUT_PATH = os.getenv("JAR_OUTPUT_PATH")

LOCAL_CONFIG = {
    "rcon_password": os.getenv("RCON_PASSWORD"),
    "rcon_port": int(os.getenv("RCON_PORT")),
    "plugins_folder": os.getenv("PLUGINS_FOLDER"),
}

PTERO_CONFIG = {
    "api_url": os.getenv("PTERO_API_URL"),
    "api_key": os.getenv("PTERO_API_KEY"),
    "server_id": os.getenv("PTERO_SERVER_ID"),
}


# Initialize Pterodactyl client
ptero = PterodactylClient(PTERO_CONFIG["api_url"], PTERO_CONFIG["api_key"])


def copy_plugin_local():
    plugin_jar = Path(JAR_OUTPUT_PATH)
    if not plugin_jar.exists():
        print(f"Plugin JAR not found at {JAR_OUTPUT_PATH}")
        return False

    try:
        shutil.copy2(JAR_OUTPUT_PATH, LOCAL_CONFIG["plugins_folder"])
        print(f"Copied {plugin_jar.name} to plugins folder")
        return True
    except Exception as e:
        print(f"Error copying plugin: {e}")
        return False


def upload_to_pterodactyl():
    plugin_jar = Path(JAR_OUTPUT_PATH)
    if not plugin_jar.exists():
        print(f"Plugin JAR not found at {JAR_OUTPUT_PATH}")
        return False

    try:
        with open(JAR_OUTPUT_PATH, "rb") as file:
            ptero.client.servers.files.write(
                PTERO_CONFIG["server_id"], f"plugins/{plugin_jar.name}", file
            )
        print(f"Uploaded {plugin_jar.name} to Pterodactyl server")
        return True
    except Exception as e:
        print(f"Failed to upload plugin: {e}")
        return False


def reload_local():
    try:
        with MCRcon(
            "localhost", LOCAL_CONFIG["rcon_password"], LOCAL_CONFIG["rcon_port"]
        ) as mcr:
            resp = mcr.command("reload confirm")
            print(f"Server reload response: {resp}")
            return True
    except Exception as e:
        print(f"Error reloading server: {e}")
        return False


def restart_pterodactyl():
    try:
        ptero.client.servers.send_power_action(PTERO_CONFIG["server_id"], "restart")
        print("Server restart initiated")
        return True
    except Exception as e:
        print(f"Error restarting server: {e}")
        return False


def watch_and_reload(use_ptero):
    last_modified = os.path.getmtime(JAR_OUTPUT_PATH)

    while True:
        current_modified = os.path.getmtime(JAR_OUTPUT_PATH)

        if current_modified > last_modified:
            print("Plugin JAR changed, updating...")
            if use_ptero:
                if upload_to_pterodactyl() and restart_pterodactyl():
                    print("Pterodactyl update successful!")
            else:
                if copy_plugin_local() and reload_local():
                    print("Local reload successful!")
            last_modified = current_modified

        time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description="Minecraft plugin hot reloader")
    parser.add_argument(
        "--ptero", action="store_true", help="Use Pterodactyl mode instead of local"
    )
    args = parser.parse_args()

    print("Starting Minecraft plugin hot reloader...")
    print(f"Watching: {JAR_OUTPUT_PATH}")
    print(f"Mode: {'Pterodactyl' if args.ptero else 'Local'}")
    if args.ptero:
        srv = ptero.client.servers.get_server(PTERO_CONFIG["server_id"])
        print(f"Server: {srv["name"]} | {srv["description"]}")

    try:
        watch_and_reload(args.ptero)
    except KeyboardInterrupt:
        print("\nStopping hot reloader")


if __name__ == "__main__":
    main()
