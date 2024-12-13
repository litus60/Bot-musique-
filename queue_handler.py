import json
import os

QUEUE_FILE = "queue_backup.json"

def save_queue(queue):
    """Sauvegarde la file d'attente dans un fichier JSON."""
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f)

def load_queue():
    """Charge la file d'attente depuis un fichier JSON."""
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []
