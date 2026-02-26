"""Bash runner for the bash adventure. Tracks cwd and runs each command as a subprocess."""

import subprocess
import os


class BashRunner:
    def __init__(self, station_dir: str):
        self.station_dir = os.path.abspath(station_dir)
        self.cwd = os.path.join(self.station_dir, "airlock")

    def start(self) -> str:
        """Return the START text."""
        start_file = os.path.join(self.station_dir, "START")
        with open(start_file) as f:
            return f.read()

    def run_command(self, command: str, timeout: float = 10.0) -> str:
        """Run a command in the current working directory, track cd changes."""
        command = command.strip()
        if not command:
            return ""

        # Handle cd specially — we need to track the directory change
        if command.startswith("cd "):
            target = command[3:].strip()
            # Resolve the path relative to current cwd
            new_path = os.path.normpath(os.path.join(self.cwd, target))
            # Follow symlinks to get the real path
            real_path = os.path.realpath(new_path)
            if os.path.isdir(real_path):
                self.cwd = real_path
                return ""
            else:
                return f"bash: cd: {target}: No such file or directory"

        # For everything else, run in a subshell
        try:
            result = subprocess.run(
                ["bash", "-c", command],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = result.stdout
            if result.stderr:
                output += result.stderr
            return output.strip()
        except subprocess.TimeoutExpired:
            return "ERROR: Command timed out."
        except Exception as e:
            return f"ERROR: {e}"

    def check_win(self) -> bool:
        """Check if .win file exists."""
        return os.path.exists(os.path.join(self.station_dir, ".win"))
