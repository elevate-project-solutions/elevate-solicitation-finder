"""
Installs the daily ESBD launchd job on my macOS.
Will consider adding other operating systems if necessary
"""

import os
import plistlib
import subprocess
import sys

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

PYTHON = BACKEND_DIR / ".venv" / "bin" / "python"

LOG_DIR = BACKEND_DIR / ".local" / "esbd" / "logs"

LABEL = "com.elevate.esbd.daily"

PLIST_PATH = (
    Path.home()
    / "Library"
    / "LaunchAgents"
    / f"{LABEL}.plist"
)

def main() -> None:
    if sys.platform != "darwin":
        raise RuntimeError(
            "This scheduler installer requires macOS."
        )

    if not PYTHON.is_file():
        raise FileNotFoundError(
            f"Virtual environment Python not found: {PYTHON}"
        )

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    PLIST_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    config = {
        "Label": LABEL,
        "ProgramArguments": [
            str(PYTHON),
            "-m",
            "scripts.daily_esbd",
        ],
        "WorkingDirectory": str(BACKEND_DIR),
        "StartCalendarInterval": {
            "Hour": 6,
            "Minute": 0,
        },
        "RunAtLoad": False,
        "StandardOutPath": str(
            LOG_DIR / "daily_stdout.log"
        ),
        "StandardErrorPath": str(
            LOG_DIR / "daily_stderr.log"
        ),
        "EnvironmentVariables": {
            "PATH": os.environ.get(
                "PATH",
                "/usr/bin:/bin:/usr/sbin:/sbin",
            ),
        },
    }

    with PLIST_PATH.open("wb") as file:
        plistlib.dump(config, file)

    uid = os.getuid()

    subprocess.run(
        [
            "launchctl",
            "bootout",
            f"gui/{uid}",
            str(PLIST_PATH),
        ],
        check=False,
        capture_output=True,
    )

    subprocess.run(
        [
            "launchctl",
            "bootstrap",
            f"fui/{uid}",
            str(PLIST_PATH),
        ],
        check=True,
    )

    print(f"Installed: {PLIST_PATH}")
    print("Scheduled: daily at 6:00 AM Mac local time")

if __name__ == "__main__":
    main()