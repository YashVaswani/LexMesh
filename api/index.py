import os
import sys
from pathlib import Path

# Add parent directory to python path for imports
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from nicegui_app import app
