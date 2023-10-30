import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from loguru import logger
import yaml

class VaultHandler(FileSystemEventHandler):
    def __init__(self, vault_path):
        self.vault_path = vault_path

    def on_created(self, event):
        if event.is_directory:
            # Create a brain_dump.md file in the new directory
            new_dir = Path(event.src_path)
            logger.info(f'New directory created: {new_dir.as_posix()}')
            prepare_dir(new_dir)

    def on_modified(self, event):

        file_changed = Path(event.src_path)

        if file_changed.name == 'brain_dump.md':
            # if file content doesn't end with ___ then add it
            with open(file_changed, 'r') as f:
                content = f.read()
                if not content.endswith('___'):
                    with open(file_changed, 'a') as f:
                        f.write('\n___')
                        logger.info(f'Added ___ to {file_changed.as_posix()}')
            

def prepare_dir(dir_path: Path):

    brain_dump_path = dir_path / 'brain_dump.md'
    overview_path = dir_path / 'overview.md'

    if not brain_dump_path.exists():
        open(brain_dump_path, 'w').close()
        logger.info(f'Created brain_dump.md in {dir_path.as_posix()}')
    
    if not overview_path.exists():
        open(overview_path, 'w').close()
        logger.info(f'Created overview.md in {dir_path.as_posix()}')


if __name__ == "__main__":
    # load settings, which are next to this file
    settings_path = Path(__file__).parent / "settings.yaml"
    settings = yaml.safe_load(open(settings_path))
    if "vault_path" not in settings:
        raise Exception("Vault path not set in settings.yaml")
    vault_path = Path(settings["vault_path"])

    if not vault_path.exists():
        raise Exception("Vault path does not exist")
    
    if not vault_path.is_dir():
        raise Exception("Vault path is not a directory")
    
    # on startup prepare all directories recursively in the vault
    for dir_path, _, _ in os.walk(vault_path):
        # ignore hidden directories
        if dir_path.startswith("."):
            continue
        prepare_dir(Path(dir_path))

    event_handler = VaultHandler(vault_path)
    observer = Observer()
    observer.schedule(
        event_handler, path=vault_path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
