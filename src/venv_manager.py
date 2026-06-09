from pathlib import Path
import os
import subprocess
import venv
import json

homefolder = Path.home()
pyvenv_path = homefolder / ".cache" / "pyvenv-manager"  # the folder containing the created Python environments


# a function that creates a new Python environment
def venv_create(venv_name, python_version, req_file=None):
    venv_path = pyvenv_path / venv_name  # environment full path
    if os.path.exists(venv_path):
        return False

    # create environment for python2 version
    if python_version == "python2":
        # to create an environment with the older Python 2 version, you first need to download and install some requirements for the Python 2 version
        # checking if pip is available for Python 2
        checkpip = subprocess.check_output(["python2", "-m", "pip", "--version"], stderr=subprocess.STDOUT).decode("utf-8", errors="replace")
        if not "pip" in checkpip:
            print("Installing pip for Python 2...")
            subprocess.run(["curl", "-sS", "https://bootstrap.pypa.io/pip/2.7/get-pip.py", "-o", "/tmp/get-pip.py"])
            subprocess.run(["pkexec", "python2", "/tmp/get-pip.py"])
            os.remove("/tmp/get-pip.py")

        # the requirements for creating an environment with Python 2 are checked, and if none exist, they are installed
        print("Install python2 virtualenv required")
        required = ["pip", "setuptools", "wheel", "virtualenv"]
        for package in required:
            try:
                subprocess.check_output(
                    ["python2", "-c","import pkg_resources; pkg_resources.get_distribution('%s')" % package],
                    stderr=subprocess.STDOUT
                )
            except subprocess.CalledProcessError:
                subprocess.run(["python2", "-m", "pip", "install", "--upgrade", package])

        try:
           print(f"'{venv_path}' creating...")
           output = subprocess.run(["python2", "-m", "virtualenv", venv_path])  # install package
        except subprocess.CalledProcessError as e:
           return e

        # if a list of dependencies is provided when the environment is created, then the list is read and the dependencies are installed into the environment
        if req_file != None:
            requirements_file = open(req_file, "r")
            reqlist = requirements_file.read()
            for pack in reqlist.splitlines():
              print("Install -- ", pack)
              if not pack_install(venv_name, pack):
                  continue
        return True

    # create environment for python3 version
    elif python_version == "python3":
        print(f"'{venv_path}' creating...")
        venv.create(
            env_dir=venv_path,
            with_pip=True
        )
        # if a list of dependencies is provided when the environment is created, then the list is read and the dependencies are installed into the environment
        if req_file != None:
            requirements_file = open(req_file, "r")
            reqlist = requirements_file.read()
            for pack in reqlist.splitlines():
              print("Install -- ", pack)
              if not pack_install(venv_name, pack):
                  continue
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


# lists the packages installed on the selected venv environment
def pack_install(venv_name, package):
    venv_path = pyvenv_path / venv_name  # environment full path
    if not os.path.exists(venv_path):
        return False
    try:
      output = subprocess.run([str(venv_path / "bin" / "pip"), "install", package])  # install package
    except subprocess.CalledProcessError as e:
        return False

    return True


# environments list
def venv_lists():
    lists = os.listdir(pyvenv_path)
    environments = []
    for vnv in lists:
      if os.path.exists(pyvenv_path / vnv / "bin" / "activate") and os.path.exists(pyvenv_path / vnv / "bin" / "python"):
          environments.append(vnv)
    return environments

