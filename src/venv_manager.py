from pathlib import Path
from typing import Tuple
import os
import subprocess
import venv
import json
import requests
import socket

homefolder = Path.home()
pyvenv_path = homefolder / ".cache" / "pyvenv-manager"  # the folder containing the created Python environments


# a function that creates a new Python environment
def venv_create(venv_name, python_version):
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

    # create environment for python3 version
    elif python_version == "python3":
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


# lists the packages installed on the selected venv environment
def pack_install(venv_name, package):
    venv_path = pyvenv_path / venv_name  # environment full path
    if not os.path.exists(venv_path):
        return False

    cmd = [str(venv_path / "bin" / "pip"), "install", package]  # install package
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    # using 'yield', the results are returned in parts for printing on the main screen
    try:
        for line in proc.stdout:
            yield line
    finally:
        proc.stdout.close()
        proc.wait()


# environments list
def venv_lists():
    lists = os.listdir(pyvenv_path)
    environments = []
    for vnv in lists:
      if os.path.exists(pyvenv_path / vnv / "bin" / "activate") and os.path.exists(pyvenv_path / vnv / "bin" / "python"):
          environments.append(vnv)
    return environments


# environment about
def venv_about(venv_name):
    venv_path = pyvenv_path / venv_name  # environment full path
    if not os.path.exists(venv_path):
        return False

    p = Path(venv_path).expanduser().resolve()
    out: Dict[str, Any] = {"env_path": str(p), "pyvenv_cfg_exists": False, "raw": {}, "include_system_site_packages": None, "hints": {}, "packages": {}}  # list to be returned at the end of the process

    cfg = p / "pyvenv.cfg"
    if not cfg.exists():
        out["pyvenv_cfg_exists"] = False
        # still provide some hints (common layout on Linux)
        out["hints"]["has_bin_python"] = (p / "bin" / "python").exists()
        out["hints"]["site_packages_paths"] = []
        # try to guess site-packages location under /lib
        lib_dir = p / "lib"
        if lib_dir.exists():
            for child in lib_dir.iterdir():
                if child.name.startswith("python"):
                    sp = child / "site-packages"
                    if sp.exists():
                        out["hints"]["site_packages_paths"].append(str(sp))
        return out

    out["pyvenv_cfg_exists"] = True
    try:
        with cfg.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    out["raw"][k] = v
    except Exception as e:
        out["error"] = f"failed reading pyvenv.cfg: {e}"
        return out

    # parse include-system-site-packages if present
    val = out["raw"].get("include-system-site-packages")
    if val is not None:
        vlow = val.strip().lower()
        out["include_system_site_packages"] = (vlow == "true")

    # helpful hints: check actual site-packages dir(s) under env
    site_paths = []
    lib_dir = p / "lib"
    if lib_dir.exists():
        for child in lib_dir.iterdir():
            if child.name.startswith("python"):
                sp = child / "site-packages"
                if sp.exists():
                    site_paths.append(str(sp))
    out["hints"]["site_packages_paths"] = site_paths
    out["hints"]["has_bin_python"] = (p / "bin" / "python").exists()

    out["packages"] = list_packages(venv_name)

    return out


# it helps to remove a packet from a medium
def uninstall_package(venv_name, package, timeout = 300):
    venv_path = pyvenv_path / venv_name  # environment full path
    if not os.path.exists(venv_path):
        return False

    cmd = [str(venv_path / "bin" / "pip"), "uninstall", "-y", package]  # package removing

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # when the process is completed within the specified time, the relevant results are obtained
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        #return proc.returncode or 1, stdout, stderr + "\nProcess killed due to timeout"
        return False

    if proc.returncode == 0 or stdout.lower() in "successfully":
        return True


# checks if a package with the given name exists
def package_exists_check(name):
    url = f"https://pypi.org/pypi/{name}/json"
    try:
        resp = requests.head(url, timeout=5.0, allow_redirects=True)  # speed test with 'head': 200 -> package avaliable, 404 -> not found
        return resp.status_code == 200
    except requests.RequestException:
        return False  # returning False in case of network error


# package is checked to see if it is installed in the specified environment
def packinstall_check(venv_name, package):
    venv_path = pyvenv_path / venv_name  # environment full path
    if not os.path.exists(venv_path):
        return False
    try:
        output = subprocess.run(
            [str(venv_path / "bin" / "pip"), "show", package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        return output.returncode == 0
    except Exception:
        return False


# lists the requirements of the package
def pack_requires(venv_name, package):
    venv_path = pyvenv_path / venv_name
    if not venv_path.exists():
        return None

    result = subprocess.run(
        [str(venv_path / "bin" / "pip"), "show", package],
        capture_output=True,
        text=True
    )

    for line in result.stdout.splitlines():  # find the "Requires:" line by traversing each line
        if line.startswith("Requires:"):
            # remove the part after "Requires:", clean up the spaces with the strip
            requires_part = line[len("Requires:"):].strip()
            if not requires_part:
                return None
            # clear and rotate comma-separated lists
            return [pkg.strip() for pkg in requires_part.split(",") if pkg.strip()]

    return None  # return None if the Requires line does not exist


# check internet
def intcheck():
    test_hosts = [("8.8.8.8", 53), ("1.1.1.1", 53)]  # DNS server IPs
    # for better control, 2 DNS server IP addresses are being tested
    for host, port in test_hosts:
        try:
            with socket.create_connection((host, port), timeout=2.0):
                return True
        except OSError:
            continue
    return False

