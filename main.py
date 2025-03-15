import time
import shutil
import os
import argparse
from pathlib import Path
from mcrcon import MCRcon
from pydactyl import PterodactylClient
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
            ptero.client.servers.files.write_file(
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


class PluginJarHandler(FileSystemEventHandler):
    def __init__(self, use_ptero):
        self.use_ptero = use_ptero
        self.last_modified = time.time()
        # Debounce time in seconds
        self.debounce_time = 1

    def on_modified(self, event):
        if not event.is_directory and event.src_path == os.path.abspath(
            JAR_OUTPUT_PATH
        ):
            current_time = time.time()
            # Debounce to prevent multiple events firing for the same change
            if current_time - self.last_modified > self.debounce_time:
                print("Plugin JAR changed, updating...")
                if self.use_ptero:
                    if upload_to_pterodactyl() and restart_pterodactyl():
                        print("Pterodactyl update successful!")
                else:
                    if copy_plugin_local() and reload_local():
                        print("Local reload successful!")
                self.last_modified = current_time


def watch_and_reload(use_ptero: bool):
    # Create a file system observer
    observer = Observer()
    event_handler = PluginJarHandler(use_ptero)

    # Get the directory containing the JAR file
    jar_dir = os.path.dirname(os.path.abspath(JAR_OUTPUT_PATH))

    # Schedule the observer to watch the directory
    observer.schedule(event_handler, jar_dir, recursive=False)
    observer.start()

    try:
        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


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
