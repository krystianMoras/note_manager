from pathlib import Path
import yaml
from loguru import logger
from faster_whisper import WhisperModel
import asyncio
from watchfiles import awatch, Change
import yaml
from pathlib import Path
import shutil
import datetime

config = yaml.load(open(f"{Path(__file__).parent}/settings.yaml", "r"), Loader=yaml.FullLoader)

def filename_to_date_str(filename:str):
    

    dt = datetime.datetime.strptime(filename, "%Y_%m_%d_%H_%M_%S")
    formatted_dt = dt.strftime("%Y-%m-%d %H:%M:%S")

    return formatted_dt

def segments_to_brain_dump_entry(segments, path_in_vault:Path):

    content = " ".join([segment.text for segment in segments])

    recording_embed = f"![[{path_in_vault.as_posix()}]]"

    tags = "tags: #transcription"
    time = f"time: {filename_to_date_str(path_in_vault.stem)}"

    footnote = "___"

    entry = "\n".join(["",content, recording_embed, tags, time, footnote])

    return entry

def filter(change:Change, path:str):
    if change != Change.deleted and Path(path).suffix in [".m4a", ".mp4", ".wav"]:
        return True
    return False


async def process_recordings(voice_recordings_public_path:Path, vault_path:Path, voice_recordings_vault_path:Path, transcription_dump_path:Path):
    await asyncio.sleep(5)

    # for each file in voice_recordings_public_path

    logger.info(f"Processing recordings in {voice_recordings_public_path}")
    model = WhisperModel(config["model_id"], device="cpu", compute_type="default")
    for file in voice_recordings_public_path.iterdir():

        # if file is audio or video
        if file.suffix in [".m4a", ".mp4", ".wav"]:
            # transcribe
            logger.info(f"Transcribing {file.as_posix()}")
            segments, _ = model.transcribe(file.as_posix())
            segments = list(segments)
            
            logger.info(f"Transcribed")
            entry = segments_to_brain_dump_entry(segments, voice_recordings_vault_path / file.name)

            # append entry to .md

            with (vault_path / transcription_dump_path).open("a") as f:
                f.write(entry)

            logger.info(f"Entry written to file {len(entry)} characters")

            # move voice recording from public to vault
            new_file_path = vault_path / voice_recordings_vault_path / file.name
            shutil.move(file, new_file_path)

            logger.info(f"Moved file to vault {new_file_path}")

async def main():
    voice_recordings_public_path = Path(config["voice_recordings_public_path"])
    voice_recordings_vault_path = Path(config["voice_recordings_vault_path"])
    vault_path = Path(config["vault_path"])
    transcription_dump_path = Path(config["transcription_dump_path"])
    task = None
    logger.info(f"Processing existing files in {voice_recordings_public_path}")
    await process_recordings(voice_recordings_public_path, vault_path, voice_recordings_vault_path, transcription_dump_path)
    logger.info(f"Done processing existing files in {voice_recordings_public_path}")
    logger.info(f"Watching for file changes in {voice_recordings_public_path}")
    async for changes in awatch(voice_recordings_public_path, watch_filter=filter):
        logger.info(changes)
        if task:
            task.cancel()

        # start a task to transcribe the recording
        task = asyncio.create_task(process_recordings(voice_recordings_public_path, vault_path, voice_recordings_vault_path, transcription_dump_path))


if __name__ == '__main__':
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('stopped via KeyboardInterrupt')
