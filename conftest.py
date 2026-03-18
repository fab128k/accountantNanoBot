# conftest.py — pytest configuration for accountantNanoBot
# Ensures the project root is on sys.path so tests can import project modules
# regardless of which Python interpreter runs pytest.

import sys
from pathlib import Path

# Insert project root at the front of sys.path so 'swarm', 'agents', etc.
# are always importable even when pytest is run with a different Python than
# the one in which dependencies are installed (e.g. /bin/python vs pyenv).
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
