"""Local-only paths for the existing-tab connector (never inside Git)."""
import os
from pathlib import Path
PRIVATE_DIR = Path(os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "MouseVirtual" / "existing-tab"
TOKEN_FILE = PRIVATE_DIR / "pairing.key"
SOURCE_EXTENSION_DIR = Path(__file__).resolve().parents[2] / "infrastructure" / "browser" / "existing_tab_extension"
EXTENSION_DIR = PRIVATE_DIR / "extension"
