run:
	python voice_notes_watcher.py
build_watcher:
	pyinstaller ./note_manager/voice_notes_watcher.py --console --add-data ./settings.yaml:.
