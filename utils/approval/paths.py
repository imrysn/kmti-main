"""Path constants for approval system"""
import os
from pathlib import Path

# Get root directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"

# Define paths
APPROVAL_QUEUE = str(DATA_DIR / "approval_queue")
APPROVED_DB = str(DATA_DIR / "approved" / "public_db")
METADATA_FILE = str(DATA_DIR / "logs" / "approvals_metadata.json")

# Ensure directories exist
os.makedirs(APPROVAL_QUEUE, exist_ok=True)
os.makedirs(APPROVED_DB, exist_ok=True)
os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
