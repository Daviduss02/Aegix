import os
import shutil
import json

TRACKER_FILE = os.path.join(os.path.dirname(__file__), ".created_files.json")

class FileManager:
    def __init__(self):
        self.created_files = self._load_tracker()

    def _load_tracker(self):
        if os.path.exists(TRACKER_FILE):
            with open(TRACKER_FILE, "r") as f:
                return set(json.load(f))
        return set()

    def _save_tracker(self):
        with open(TRACKER_FILE, "w") as f:
            json.dump(list(self.created_files), f)

    def register_creation(self, path):
        abs_path = os.path.abspath(path)
        self.created_files.add(abs_path)
        self._save_tracker()

    def safe_delete_file(self, path):
        abs_path = os.path.abspath(path)
        if abs_path in self.created_files:
            if os.path.isfile(abs_path):
                os.remove(abs_path)
                self.created_files.remove(abs_path)
                self._save_tracker()
                return True
            elif os.path.islink(abs_path):
                os.unlink(abs_path)
                self.created_files.remove(abs_path)
                self._save_tracker()
                return True
        return False

    def safe_delete_dir(self, path):
        abs_path = os.path.abspath(path)
        if abs_path in self.created_files:
            if os.path.isdir(abs_path):
                shutil.rmtree(abs_path)
                # Also remove sub-items from tracker if they were there
                self.created_files = {p for p in self.created_files if not p.startswith(abs_path)}
                self._save_tracker()
                return True
        return False

    def create_file(self, path, content=""):
        abs_path = os.path.abspath(path)
        with open(abs_path, "w") as f:
            f.write(content)
        self.register_creation(abs_path)

    def create_dir(self, path):
        abs_path = os.path.abspath(path)
        os.makedirs(abs_path, exist_ok=True)
        self.register_creation(abs_path)

# Global instance
file_manager = FileManager()
