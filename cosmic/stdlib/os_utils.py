"""Cosmic Standard Library — os_utils module."""
from __future__ import annotations
import os
import sys
import subprocess
import platform
from typing import Any


def env(name: str, default: str = '') -> str:
    return os.environ.get(name, default)


def set_env(name: str, value: str) -> None:
    os.environ[name] = value


def get_env(name: str) -> str | None:
    return os.environ.get(name)


def unset_env(name: str) -> None:
    os.environ.pop(name, None)


def cpu_count() -> int:
    return os.cpu_count() or 1


def memory_info() -> dict[str, int]:
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        info = {}
        for line in lines:
            parts = line.split(':')
            if len(parts) == 2:
                key = parts[0].strip()
                val = int(parts[1].strip().split()[0]) * 1024
                info[key] = val
        return info
    except Exception:
        return {'total': 0, 'available': 0}


def disk_usage(path: str = '/') -> dict[str, int]:
    usage = os.statvfs(path)
    total = usage.f_blocks * usage.f_frsize
    free = usage.f_bfree * usage.f_frsize
    used = total - free
    return {'total': total, 'used': used, 'free': free}


def getpid() -> int:
    """Return the current process ID."""
    return os.getpid()


pid = getpid


def hostname() -> str:
    import socket
    return socket.gethostname()


def username() -> str:
    return os.getenv('USER', os.getenv('USERNAME', 'unknown'))


def platform_name() -> str:
    return platform.platform()


def is_windows() -> bool:
    return sys.platform == 'win32'


def is_linux() -> bool:
    return sys.platform == 'linux'


def is_macos() -> bool:
    return sys.platform == 'darwin'


def is_posix() -> bool:
    return os.name == 'posix'


def exec_command(cmd: str, shell: bool = True, timeout: int | None = None) -> tuple[int, str, str]:
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return result.returncode, result.stdout, result.stderr


def exec_background(cmd: str) -> subprocess.Popen:
    return subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def shell(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout


def which(name: str) -> str | None:
    import shutil
    return shutil.which(name)


def chmod(path: str, mode: int) -> None:
    os.chmod(path, mode)


def chown(path: str, uid: int, gid: int) -> None:
    os.chown(path, uid, gid)


def getppid() -> int:
    return os.getppid()


def set_cwd(path: str) -> None:
    os.chdir(path)


def list_env() -> dict[str, str]:
    return dict(os.environ)


def expand_vars(s: str) -> str:
    return os.path.expandvars(s)


def umask(mask: int = 0o022) -> int:
    old = os.umask(mask)
    return old


def is_admin() -> bool:
    if is_windows():
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    return os.geteuid() == 0


def open_file(path: str) -> None:
    if is_macos():
        os.system(f'open "{path}"')
    elif is_linux():
        os.system(f'xdg-open "{path}"')
    else:
        os.startfile(path)


def clipboard_copy(text: str) -> None:
    if is_macos():
        process = subprocess.Popen('pbcopy', stdin=subprocess.PIPE)
        process.communicate(text.encode())
    elif is_linux():
        process = subprocess.Popen('xclip', stdin=subprocess.PIPE)
        process.communicate(text.encode())
    else:
        process = subprocess.Popen('clip', stdin=subprocess.PIPE)
        process.communicate(text.encode())


def clipboard_paste() -> str:
    if is_macos():
        return subprocess.check_output('pbpaste', text=True)
    elif is_linux():
        return subprocess.check_output('xclip -o', text=True, shell=True)
    else:
        return subprocess.check_output('powershell -command "Get-Clipboard"', text=True)
