from pathlib import Path
import os
import subprocess
import venv

homefolder = Path.home()
pyvenv_path = homefolder / ".cache" / "pyvenv-manager"  # the folder containing the created Python environments


# a function that creates a new Python environment
def venv_create(venv_name):
    venv_path = pyvenv_path / venv_name  # environment full path
    if os.path.exists(venv_path):
        return False

    print(f"'{venv_path}' creating...")
    venv.create(
        env_dir=venv_path,
        with_pip=True
    )
    return True


# lists the packages installed on the selected venv environment
def list_packages(venv_name):
    venv_path = pyvenv_path / venv_name  # environment full path
    if not os.path.exists(venv_path):
        return False

    result = subprocess.run(
        [venv_path / "bin/pip", "list", "--format", "json"],  # list json format
        capture_output=True,
        text=True
    )
    return result.stdout



