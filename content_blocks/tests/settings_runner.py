"""
Run tests with each test settings configuration.
"""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent.parent
    settings_dir = base_dir / "example" / "settings"

    for f in settings_dir.glob("test*.py"):
        settings_file = f.name.replace(".py", "")
        subprocess.run(
            ["pytest", "--ds", f"example.settings.{settings_file}"],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
