from pathlib import Path
from typing import Tuple
import os
import subprocess
import venv
import json
import ast
import requests
import socket
import configparser
import shlex
import shutil
import re
import glob
import sysconfig
import runpy
import sys

homefolder = Path.home()
pyvenv_path = homefolder / ".cache" / "pyvenv-manager"  # the folder containing the created Python environments
connfile = pyvenv_path / "connections.json"  # connectedions info file


# A function that runs Pip directly from the wheel file located in the WHEEL_PKG_DIR directory
def run_pip_from_wheel(args):
    wheel_dir = sysconfig.get_config_var("WHEEL_PKG_DIR")
    if not wheel_dir:
        raise RuntimeError("Python was not compiled with WHEEL_PKG_DIR")

    wheel_dir = Path(wheel_dir)
    wheels = sorted(wheel_dir.glob("pip-*.whl"))

    if not wheels:
        raise FileNotFoundError(f"No pip wheel found inside {wheel_dir}")

    pip_wheel = wheels[-1]
    old_path = sys.path[:]
    old_argv = sys.argv[:]

    try:
        # Make the wheel importable
        sys.path.insert(0, str(pip_wheel))
        # Simulate command line
        sys.argv = ["pip"] + list(args)
        # Equivalent to:
        # python -m pip ...
        runpy.run_module("pip", run_name="__main__", alter_sys=True)
    finally:
        sys.path[:] = old_path
        sys.argv[:] = old_argv


# function to link an isolated Python2 installation to the system's environment variables
def envset_python2():
    print("environment variable assigned for Python 2")
    env = os.environ.copy()
    root = "/usr/lib/pyvenv-manager/python2"
    extra = [root + "/lib", root + "/lib/python2.7/x86_64-linux-gnu",]
    old = env.get("LD_LIBRARY_PATH")
    if old:
        env["LD_LIBRARY_PATH"] = ":".join(extra + [old])
    else:
        env["LD_LIBRARY_PATH"] = ":".join(extra)
    print("python2 -> LD_LIBRARY_PATH: ", root + "/lib/python2.7/x86_64-linux-gnu")
    return env


# a function that creates a new Python environment
def venv_create(venv_name, python_version, system_sitepacks):
    venv_path = pyvenv_path / venv_name  # environment full path
    if os.path.exists(venv_path):
        return False

    # create environment for python2 version
    if python_version == "python2":
        python2_execdir = "/usr/lib/pyvenv-manager/python2/bin/python2"
        env = envset_python2()
        try:
           print(f"'{venv_path}' creating...")
           output = subprocess.run([python2_execdir, "-m", "virtualenv", venv_path], env=env)  # install package
        except subprocess.CalledProcessError as e:
           return e

    # create environment for python3 version
    elif python_version == "python3":
        print(f"'{venv_path}' creating...")
        if system_sitepacks:
            venv.create(env_dir=venv_path, with_pip=True, system_site_packages=True)
        else:
            venv.create(env_dir=venv_path, with_pip=True)
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
    raw = result.stdout or result.stderr
    m = re.search(r'([\[\{].*)', raw, flags=re.DOTALL)

    j = m.group(1).strip()
    # Trim after last closing bracket/brace if trailing garbage present
    cut = max(j.rfind(']'), j.rfind('}'))
    if cut != -1:
        j = j[:cut+1]
    return j



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

    env = envset_python2()
    cmd = [str(venv_path / "bin" / "pip"), "install", package]  # install package
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, bufsize=1)
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
def package_exists_check(packname):
    if "==" in packname:  # if the package is provided with version information, it will be checked whether that version is available
        name, version = packname.split("==", 1)
        url = f"https://pypi.org/pypi/{name}/{version}/json"
    else:
        url = f"https://pypi.org/pypi/{packname}/json"

    try:
        resp = requests.head(url, timeout=4.0, allow_redirects=True)  # speed test with 'head': 200 -> package avaliable, 404 -> not found
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
    if not os.path.exists(venv_path):
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


# returns files attached to any environment
def connfiles_list(pyvenv):
    connected_list = []

    with open(connfile, "r") as connjson:
        data = json.load(connjson)
    connected = data["connected_files"]
    if connected:
        if pyvenv in connected:
            for lst in connected[pyvenv]:
                connected_list.append(lst)
            return connected_list
        else:
            return False
    else:
        return False


# returns apps attached to any environment
def connapps_list(pyvenv):
    connected_apps = []

    with open(connfile, "r") as  connjson:
        data = json.load(connjson)
    connected = data["connected_apps"]
    if connected:
        if pyvenv in connected:
            for lst in connected[pyvenv]:
                connected_apps.append(lst)
            return connected_apps
        else:
            return False
    else:
        return False


# function that modifies the Python script to execute it in the given environment
def connect_environment_file(venv_name, selectedpy):
    venv_path = pyvenv_path / venv_name
    if not os.path.exists(venv_path):
        return None

    # reading json metadata
    with open(connfile, "r", encoding="utf-8") as f:
        data = json.load(f)

    # create shebang
    startpy_file =  venv_path / "bin" / "python3"
    start_shebang = "#!" + str(startpy_file)

    # Additional interpreter control and redirection code lines are added to allow the Python file to be executed from the linked environment
    exec_comm = f"""import os
import sys
VENV_PYTHON = "{start_shebang[2:]}"
if os.path.realpath(sys.executable) != os.path.realpath(VENV_PYTHON):
    # environment variables are being updated
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = VENV_PYTHON
    env["PATH"] = os.path.join(VENV_PYTHON, "bin") + ":" + env["PATH"]
    os.execve(VENV_PYTHON, [VENV_PYTHON] + sys.argv, env)"""

    # the new shebang is printed to the first line of the Python file
    with open(selectedpy, "r", encoding="utf-8") as pyfile:
        tmpcontent = pyfile.read()

    with open(selectedpy, "w", encoding="utf-8") as pyfile:
        pyfile.write(start_shebang+"\n")
        pyfile.write("# '{}' environment was connected to by 'pyvenv-manager'\n".format(venv_name))
        pyfile.write("# Generated automatically by 'pyvenv-manager'\n# Do not edit manually.\n")
        pyfile.write(exec_comm+"\n")  # interpreter routing codes are being written
        pyfile.write("#--------------------------------------\n")  # separator line
        pyfile.write("\n")  # extra line
        pyfile.write(tmpcontent)  # main code is being written

    # connection is saved to a JSON metadata file
    data["connected_files"].setdefault(venv_name, [])
    data["connected_files"][venv_name].extend([
        f"{selectedpy}"
    ])
    with open(connfile, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True


# this function disconnects the Python script from its environment and returns it to its normal state
def disconnect_environment_file(venv_name, selectedpy, connapps_venvpath=None):
    if not connapps_venvpath:  # NOTE: 'environment_remove' function might not be able to find the path where the environments are located when it runs, so the environment paths must be obtained from the edge
        venv_path = pyvenv_path / venv_name
        connfile = pyvenv_path / "connections.json"  # connectedions info file
    else:
        venv_path = str(connapps_venvpath) + "/" + venv_name
        connfile = str(connapps_venvpath) + "/connections.json"

    # reading json metadata
    with open(connfile, "r", encoding="utf-8") as f:
        data = json.load(f)

    if os.path.exists(selectedpy):  # if the file exists on the computer, the relevant operations will be performed
        # shebang and other routing codes are being removed from the file.
        with open(selectedpy, "r", encoding="utf-8") as pyfile:
            lines = pyfile.readlines()
        with open(selectedpy, "w", encoding="utf-8") as pyfile:
            pyfile.writelines(lines[15:])

    if venv_name in data["connected_files"]:
        data["connected_files"][venv_name].remove(selectedpy)  # name of the Python file to be extracted from the environment is being removed
        # if the list is empty, also delete the key that exists in the environment name
        if not data["connected_files"][venv_name]:
            del data["connected_files"][venv_name]
    with open(connfile, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True


# this function removes the given environment from the computer
def environment_remove(venv_name, connapps_venvpath=None):
    if not connapps_venvpath:
        venv_path = pyvenv_path / venv_name
        connfile = pyvenv_path / "connections.json"  # connectedions info file
    else:
        venv_path = str(connapps_venvpath) + "/" + venv_name
        connfile = str(connapps_venvpath) + "/connections.json"

    # reading json metadata
    with open(connfile, "r", encoding="utf-8") as f:
        data = json.load(f)

    # files or applications associated with the environment are being removed from the metadata file
    if venv_name in data["connected_files"]:
        # environment is disconnected from all files associated with it
        for connlist in data["connected_files"][venv_name]:
            disconnect_environment_file(venv_name, connlist, connapps_venvpath)
        del data["connected_files"][venv_name]

    if venv_name in data["connected_apps"]:
        for connlist in data["connected_apps"][venv_name]:
            disconnect_environment_app(connapps_venvpath, venv_name, connlist)
        del data["connected_apps"][venv_name]

    # writing metadata in json
    with open(connfile, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    os.system(f"rm -r {venv_path}")  # remove environment path
    return True


# The system lists .desktop launchers belonging to Python applications
def list_python_desktop_files():
    python_desktops = []

    for desktop in glob.glob("/usr/share/applications/*.desktop"):
        parser = configparser.ConfigParser(interpolation=None)
        try:
            parser.read(desktop, encoding="utf-8")
        except Exception:
            continue
        if not parser.has_section("Desktop Entry"):
            continue

        appname_line = parser["Desktop Entry"].get("Name")  # Name line
        exec_line = parser["Desktop Entry"].get("Exec")  # Exec line
        icon_line = parser["Desktop Entry"].get("Icon")  # Icon line
        try:
            args = shlex.split(exec_line)
        except ValueError:
            continue

        # remove %U, %F, etc
        args = [a for a in args if not a.startswith("%")]
        if not args:
            continue

        executable = args[0]

        # Find the actual file via PATH
        if not os.path.isabs(executable):
            executable = shutil.which(executable)

        if executable is None:
            continue

        is_python = False

        # exec calls the Python interpreter
        base = os.path.basename(executable)

        if base.startswith("python"):
            if len(args) >= 2:
                script = args[1]
                if not os.path.isabs(script):
                    script = os.path.abspath(script)
                if os.path.exists(script):
                    is_python = True
                    launcher_type = "interpreter"

        # if the file being executed is a Python script, it finds it
        else:
            try:
                with open(executable, "rb") as f:
                    first_line = f.readline(200)
                if first_line.startswith(b"#!") and b"python" in first_line.lower():
                    is_python = True
                    launcher_type = "shebang"
                elif executable.endswith(".py"):
                    is_python = True
            except Exception:
                pass

        if is_python:
            python_desktops.append({"appname": appname_line, "desktop": desktop, "exec": exec_line, "icon": icon_line, "target": executable, "launcher_type": launcher_type})
    return python_desktops


# function that maps a Python application to an environment
def connect_environment_app(venv_path, venv_name, app_info):  # since this operation requires root access, the venv path is provided externally
    venv_python = str(venv_path) + "/" + venv_name + "/bin/python3"
    connfile = str(venv_path) + "/connections.json"  # connectedions info file
    # reading json metadata
    with open(connfile, "r", encoding="utf-8") as f:
        data = json.load(f)

    launcher_type = app_info["launcher_type"]
    if launcher_type == "interpreter":
        desktop_file = app_info["desktop"]
        with open(desktop_file, encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if not line.startswith("Exec="):
                continue
            exec_line = line[len("Exec="):].rstrip("\n")
            args = shlex.split(exec_line)
            args[0] = venv_python
            lines[i] = "Exec=" + shlex.join(args) + "\n"
            break
        with open(desktop_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

    elif launcher_type == "shebang":
        script_file = app_info["target"]
        # the new shebang is printed to the first line of the Python file
        with open(script_file, "r", encoding="utf-8") as pyfile:
            tmpcontent = pyfile.read()

        with open(script_file, "w", encoding="utf-8") as pyfile:
            pyfile.write(f"#!{venv_python}"+"\n")
            pyfile.write("# '{}' environment was connected to by 'pyvenv-manager'\n".format(venv_name))
            pyfile.write("# Generated automatically by 'pyvenv-manager'\n# Do not edit manually.\n")
            pyfile.write("#--------------------------------------\n")  # separator line
            pyfile.write("\n")  # extra line
            pyfile.write(tmpcontent)  # main code is being written

    # connection is saved to a JSON metadata file
    data["connected_apps"].setdefault(venv_name, [])
    data["connected_apps"][venv_name].extend([
        f"{app_info}"
    ])
    with open(connfile, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True


# it disconnect Python applications that are connected to any environment
def disconnect_environment_app(venv_path, venv_name, app_info):
    connfile = str(venv_path) + "/connections.json"  # connectedions info file
    # reading json metadata
    with open(connfile, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(app_info)
    app_info = ast.literal_eval(str(app_info))
    launcher_type = app_info["launcher_type"]
    desktop_file = app_info["desktop"]

    if launcher_type == "interpreter":
        with open(desktop_file, encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if not line.startswith("Exec="):
                continue
            exec_line = line[len("Exec="):].rstrip("\n")
            print(exec_line)
            args = shlex.split(exec_line)
            args[0] = "python"
            lines[i] = "Exec=" + shlex.join(args) + "\n"
            break
        with open(desktop_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

    elif launcher_type == "shebang":
        targetfile = app_info["target"]
        # shebang and other routing codes are being removed from the file.
        with open(targetfile, "r", encoding="utf-8") as pyfile:
            lines = pyfile.readlines()
        with open(targetfile, "w", encoding="utf-8") as pyfile:
            pyfile.writelines(lines[6:])

    if venv_name in data["connected_apps"]:
        data["connected_apps"][venv_name].remove(str(app_info))  # list data of the disconnected Python application is extracted directly from the metadata file
        # if the list is empty, also delete the key that exists in the environment name
        if not data["connected_apps"][venv_name]:
            del data["connected_apps"][venv_name]
    with open(connfile, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True


# function that specifies access to global Python libraries for the selected environment
def system_site_packs_change(venv_name, activestatus):
    cfg_path = str(pyvenv_path) + "/" + venv_name + "/pyvenv.cfg"

    value = "true" if activestatus else "false"  # parameter to be written
    with open(cfg_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    found = False
    new_lines = []

    # relevant line is found and the sent parameter is printed
    for line in lines:
        if line.strip().startswith("include-system-site-packages"):
            new_lines.append(f"include-system-site-packages = {value}\n")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"include-system-site-packages = {value}\n")
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return True


# this shows the access status of the virtual environment to global Python libraries
def system_site_packs_status(venv_name):
    cfg_path = str(pyvenv_path) + "/" + venv_name + "/pyvenv.cfg"
    with open(cfg_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if line.strip().startswith("include-system-site-packages"):
            output = line.split()[-1]

    if output == "true":
        return True
    elif output == "false":
        return False


# function that lists pip cache
def cache_list():
    text = run_pip_from_wheel(["cache", "list"])
    items = []
    pattern = re.compile(r'^[\s-]*([^\s].*?\.whl)\s*\(([\d.]+)\s*([kMGT]?B)\)\s*$', re.IGNORECASE | re.MULTILINE)  # package name and size are separated
    if "No locally built" in text:
        return False

    for m in pattern.finditer(text):
        filename = m.group(1)  # package name
        size_val = float(m.group(2))  # package size
        size_unit = m.group(3).upper()  # KB, MB,...
        items.append({
            "filename": filename,
            "size": f"{size_val} {size_unit}"
        })

    output_lst = json.dumps(items, indent=2, ensure_ascii=False)
    return output_lst


# clear cache function
def clear_cache():
    # manual cleaning
    cache_dir = homefolder / ".cache" / "pip"
    if os.path.isdir(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            return True
        except Exception as e:
            return False
    else:
        return False

