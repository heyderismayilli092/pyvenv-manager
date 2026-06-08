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

