from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AI_CONFIG_PATH = PROJECT_ROOT / "02_AI"

if str(AI_CONFIG_PATH) not in sys.path:
    sys.path.insert(0, str(AI_CONFIG_PATH))

from Config.settings import settings

print(settings.project)

print(settings.trading)

print(settings.risk)