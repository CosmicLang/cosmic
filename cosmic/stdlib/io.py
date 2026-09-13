"""Cosmic Standard Library — I/O module."""
from __future__ import annotations
import os
import sys
import shutil
import tempfile
from typing import Any, Callable


def read_file(path: str, encoding: str = 'utf-8') -> str:
    with open(path, 'r', encoding=encoding) as f:
        return f.read()


def write_file(path: str, content: str, encoding: str = 'utf-8') -> None:
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding=encoding) as f:
        f.write(content)


def append_file(path: str, content: str, encoding: str = 'utf-8') -> None:
    with open(path, 'a', encoding=encoding) as f:
        f.write(content)


def file_exists(path: str) -> bool:
    return os.path.isfile(path)


def dir_exists(path: str) -> bool:
    return os.path.isdir(path)


def mkdir(path: str, exist_ok: bool = True) -> None:
    os.makedirs(path, exist_ok=exist_ok)


def list_dir(path: str = '.') -> list[str]:
    return os.listdir(path)


def walk_dir(path: str) -> list[tuple[str, list[str], list[str]]]:
    return list(os.walk(path))


def copy_file(src: str, dst: str) -> None:
    shutil.copy2(src, dst)


def move_file(src: str, dst: str) -> None:
    shutil.move(src, dst)


def remove_file(path: str) -> None:
    os.remove(path)


def temp_dir() -> str:
    return tempfile.mkdtemp()


def stdin() -> str:
    return sys.stdin.read()


def stdout() -> Any:
    return sys.stdout


def stderr() -> Any:
    return sys.stderr


def input_line(prompt: str = '') -> str:
    return input(prompt)


def confirm(prompt: str = 'Are you sure?') -> bool:
    response = input(f"{prompt} [y/N]: ").strip().lower()
    return response in ('y', 'yes')


def print_color(text: str, color: str = 'reset', **kwargs: Any) -> None:
    colors = {
        'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m',
        'blue': '\033[94m', 'magenta': '\033[95m', 'cyan': '\033[96m',
        'white': '\033[97m', 'reset': '\033[0m', 'bold': '\033[1m',
        'dim': '\033[2m', 'italic': '\033[3m', 'underline': '\033[4m',
    }
    code = colors.get(color, colors['reset'])
    print(f"{code}{text}{colors['reset']}", **kwargs)


def print_error(text: str, **kwargs: Any) -> None:
    print_color(f"error: {text}", 'red', file=sys.stderr, **kwargs)


def print_warning(text: str, **kwargs: Any) -> None:
    print_color(f"warning: {text}", 'yellow', file=sys.stderr, **kwargs)


def print_success(text: str, **kwargs: Any) -> None:
    print_color(text, 'green', **kwargs)


def print_info(text: str, **kwargs: Any) -> None:
    print_color(text, 'cyan', **kwargs)


def prompt(message: str, default: str = '') -> str:
    result = input(f"{message} [{default}]: ").strip()
    return result if result else default


def prompt_int(message: str, default: int = 0, min_val: int | None = None, max_val: int | None = None) -> int:
    while True:
        try:
            result = int(input(f"{message} [{default}]: ").strip() or default)
            if min_val is not None and result < min_val:
                print_color(f"Value must be >= {min_val}", 'red')
                continue
            if max_val is not None and result > max_val:
                print_color(f"Value must be <= {max_val}", 'red')
                continue
            return result
        except ValueError:
            print_color("Please enter a valid integer", 'red')


def prompt_float(message: str, default: float = 0.0) -> float:
    while True:
        try:
            return float(input(f"{message} [{default}]: ").strip() or default)
        except ValueError:
            print_color("Please enter a valid number", 'red')


def prompt_choice(message: str, choices: list[str], default: str = '') -> str:
    print(f"{message}")
    for i, choice in enumerate(choices, 1):
        marker = ' (default)' if choice == default else ''
        print(f"  {i}. {choice}{marker}")
    while True:
        result = input("Choice: ").strip()
        if not result and default:
            return default
        try:
            idx = int(result) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            if result in choices:
                return result
        print_color("Invalid choice", 'red')


class Spinner:
    def __init__(self, message: str = 'Loading...'):
        self.message = message
        self.chars = '|/-\\'
        self.running = False

    def start(self) -> None:
        self.running = True
        import threading
        def spin():
            i = 0
            while self.running:
                print(f"\r{self.chars[i % len(self.chars)]} {self.message}", end='', flush=True)
                import time
                time.sleep(0.1)
                i += 1
        self.thread = threading.Thread(target=spin, daemon=True)
        self.thread.start()

    def stop(self, final_message: str = 'Done!') -> None:
        self.running = False
        print(f"\r{final_message}{' ' * (len(self.message) + 2)}")


def progress_bar(iterable: Any, total: int | None = None, desc: str = '') -> list:
    if total is None:
        total = len(iterable) if hasattr(iterable, '__len__') else None
    items = list(iterable)
    if total is None:
        total = len(items)
    result = []
    for i, item in enumerate(items):
        pct = (i + 1) / total * 100
        filled = int(20 * (i + 1) / total)
        bar = '█' * filled + '░' * (20 - filled)
        print(f"\r{desc} |{bar}| {pct:.0f}% ({i+1}/{total})", end='', flush=True)
        result.append(item)
    print()
    return result


def table_print(headers: list[str], rows: list[list[str]], widths: list[int] | None = None) -> None:
    if widths is None:
        widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0)) + 2
                  for i, h in enumerate(headers)]
    header_line = '│'.join(h.center(w) for h, w in zip(headers, widths))
    sep_line = '┼'.join('─' * w for w in widths)
    print(f"┌{'┬'.join('─' * w for w in widths)}┐")
    print(f"│{header_line}│")
    print(f"├{sep_line}┤")
    for row in rows:
        line = '│'.join(str(row[i]).center(widths[i]) if i < len(row) else ' ' * widths[i]
                        for i in range(len(widths)))
        print(f"│{line}│")
    print(f"└{'┴'.join('─' * w for w in widths)}┘")


def print_json(data: Any, indent: int = 2) -> None:
    import json
    print(json.dumps(data, indent=indent, default=str))


def print_yaml(data: Any) -> None:
    try:
        import yaml
        print(yaml.dump(data, default_flow_style=False))
    except ImportError:
        print_json(data)


def watch_file(path: str, callback: Callable[[str], None], interval: float = 1.0) -> None:
    import time
    last_mtime = os.path.getmtime(path)
    while True:
        time.sleep(interval)
        current_mtime = os.path.getmtime(path)
        if current_mtime != last_mtime:
            callback(path)
            last_mtime = current_mtime
