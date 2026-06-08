from pathlib import Path
import os
import subprocess
import venv
import json

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
        [str(venv_path / "bin" / "pip"), "list", "--format", "json"],  # list json format
        capture_output=True,
        text=True
    )
    return result.stdout


# lists the packages installed on the selected venv environment
def pack_info(venv_name, package):
    venv_path = pyvenv_path / venv_name  # environment full path
    if not os.path.exists(venv_path):
        return False

    # package information is being retrieved
    result = subprocess.run(
        [str(venv_path / "bin" / "pip"), "show", package],
        capture_output=True,
        text=True
    )

    text = result.stdout or ""
    data = {}
    last_key = None

    for line in text.splitlines():
        if not line.strip():  # skip blank line
            last_key = None
            continue

        if ":" in line:
            # separate the key-value pair with the first ':'
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip() or None
            # some fields may be comma-separated lists
            if key.lower() == "requires" and val:
                data[key] = [x.strip() for x in val.split(",") if x.strip()]
            else:
                data[key] = val
            last_key = key
        else:
            # pip show can sometimes contain multi-line comments; the continuation line is merged
            if last_key:
                prev = data.get(last_key) or ""
                # if 'prev' is None, first convert it to a string
                if prev is None:
                    prev = ""
                data[last_key] = (prev + "\n" + line).strip()

    return json.dumps(data, ensure_ascii=False, indent=2)


