# backend/executor.py

import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import stat
from collections import deque

HISTORY_FILE = Path.home() / ".pyterminal_history"
MAX_HISTORY = 1000

# in-memory history (load from file on import)
_history = deque(maxlen=MAX_HISTORY)
if HISTORY_FILE.exists():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                _history.append(line.rstrip("\n"))
    except Exception:
        pass

def _save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            for cmd in _history:
                f.write(cmd + "\n")
    except Exception:
        pass

def add_history(cmd: str):
    if not cmd.strip():
        return
    _history.append(cmd)
    _save_history()

def get_history(n: int = 50) -> List[str]:
    return list(_history)[-n:][::-1]

# Helpers
def _safe_listdir(path: Path):
    try:
        return sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except Exception as e:
        raise RuntimeError(str(e))

def _format_file_info(p: Path):
    st = p.stat()
    mode = stat.filemode(st.st_mode)
    size = st.st_size
    mtime = st.st_mtime
    return f"{mode}\t{size}\t{p.name}"

# Main executor
def execute_command(cmd: str, cwd: str = None, allow_shell: bool = False) -> Dict[str, Any]:
    """
    Execute a terminal-like command. Returns dict:
    {
        "ok": True/False,
        "stdout": "...",
        "stderr": "...",
        "cwd": "...",
        "exit_code": int
    }
    """
    import psutil

    add_history(cmd)
    cwd = cwd or os.getcwd()
    tokens = shlex.split(cmd, posix=True)
    out = {"ok": True, "stdout": "", "stderr": "", "cwd": cwd, "exit_code": 0}
    if len(tokens) == 0:
        return out

    try:
        cmd0 = tokens[0]

        # ------------------- BUILTINS -------------------
        if cmd0 in ("pwd", "cwd"):
            out["stdout"] = os.getcwd()

        elif cmd0 == "ls":
            path = tokens[1] if len(tokens) > 1 else "."
            p = Path(path if Path(path).is_absolute() else os.path.join(os.getcwd(), path))
            items = _safe_listdir(p)
            lines = []
            long = "-l" in tokens or "--long" in tokens
            for it in items:
                if long:
                    lines.append(_format_file_info(it))
                else:
                    lines.append(it.name + ("/" if it.is_dir() else ""))
            out["stdout"] = "\n".join(lines)

        elif cmd0 == "cd":
            target = tokens[1] if len(tokens) > 1 else str(Path.home())
            target_path = Path(target if Path(target).is_absolute() else os.path.join(os.getcwd(), target))
            if not target_path.exists() or not target_path.is_dir():
                raise FileNotFoundError(f"No such directory: {target}")
            os.chdir(str(target_path))
            out["stdout"] = os.getcwd()
            out["cwd"] = os.getcwd()

        elif cmd0 == "mkdir":
            if len(tokens) < 2:
                raise ValueError("mkdir requires a directory name")
            Path(tokens[1]).mkdir(parents=True, exist_ok=False)
            out["stdout"] = f"Created {tokens[1]}"

        elif cmd0 in ("rm", "del"):
            if len(tokens) < 2:
                raise ValueError("rm requires a target")
            target = Path(tokens[1])
            if not target.exists():
                raise FileNotFoundError("Target not found")
            if "-r" in tokens or "-rf" in tokens:
                if target.is_dir():
                    shutil.rmtree(target)
                    out["stdout"] = f"Removed directory {target}"
                else:
                    target.unlink()
                    out["stdout"] = f"Removed file {target}"
            else:
                if target.is_dir():
                    raise IsADirectoryError("Directory - use -r to remove directories")
                else:
                    target.unlink()
                    out["stdout"] = f"Removed file {target}"

        elif cmd0 == "touch":
            if len(tokens) < 2:
                raise ValueError("touch requires a filename")
            Path(tokens[1]).touch(exist_ok=True)
            out["stdout"] = f"Touched {tokens[1]}"

        elif cmd0 == "cat":
            if len(tokens) < 2:
                raise ValueError("cat requires a filename")
            p = Path(tokens[1])
            if not p.exists() or not p.is_file():
                raise FileNotFoundError("File not found")
            out["stdout"] = p.read_text(encoding="utf-8", errors="replace")

        elif cmd0 == "mv":
            if len(tokens) < 3:
                raise ValueError("mv requires source and destination")
            shutil.move(tokens[1], tokens[2])
            out["stdout"] = f"Moved {tokens[1]} -> {tokens[2]}"

        elif cmd0 == "cp":
            if len(tokens) < 3:
                raise ValueError("cp requires source and destination")
            shutil.copy2(tokens[1], tokens[2])
            out["stdout"] = f"Copied {tokens[1]} -> {tokens[2]}"

        elif cmd0 == "head":
            n = 10
            path = tokens[-1]
            if len(tokens) >= 3 and tokens[1].startswith("-"):
                try:
                    n = int(tokens[1].lstrip("-n"))
                except:
                    pass
            p = Path(path)
            out["stdout"] = "\n".join(p.read_text().splitlines()[:n])

        elif cmd0 == "tail":
            n = 10
            path = tokens[-1]
            if len(tokens) >= 3 and tokens[1].startswith("-"):
                try:
                    n = int(tokens[1].lstrip("-n"))
                except:
                    pass
            p = Path(path)
            lines = p.read_text().splitlines()
            out["stdout"] = "\n".join(lines[-n:])

        elif cmd0 == "history":
            out["stdout"] = "\n".join(get_history(200))

        elif cmd0 == "help":
            out["stdout"] = (
                "Builtins: pwd ls cd mkdir rm touch cat mv cp head tail history help cpu mem ps\n"
                "Use `command` alone or with args. Unknown commands are blocked in web mode.\n"
            )

        # ------------------- MONITORING -------------------
        elif cmd0 == "ps":
            # ps [--sort cpu|mem] [n]
            n = 10
            sort = "cpu"
            for t in tokens[1:]:
                if t.isdigit():
                    n = int(t)
                if t.startswith("--sort="):
                    sort = t.split("=", 1)[1]
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    info = p.info
                    procs.append(info)
                except Exception:
                    pass
            procs.sort(key=lambda x: x.get("cpu_percent", 0) if sort == "cpu" else x.get("memory_percent", 0), reverse=True)
            lines = []
            for p in procs[:n]:
                lines.append(f"{p['pid']}\t{p.get('name')}\tCPU:{p.get('cpu_percent')}\tMEM:{p.get('memory_percent')}")
            out["stdout"] = "\n".join(lines)

        elif cmd0 == "cpu":
            out["stdout"] = f"CPU Usage: {psutil.cpu_percent()}%"

        elif cmd0 == "mem":
            mem_info = psutil.virtual_memory()
            out["stdout"] = (
                f"Memory Usage: {mem_info.percent}% "
                f"({mem_info.used / (1024**3):.2f}GB used / {mem_info.total / (1024**3):.2f}GB total)"
            )

        # ------------------- FALLBACK -------------------
        else:
            if allow_shell:
                try:
                    proc = subprocess.run(tokens, capture_output=True, text=True, cwd=cwd, timeout=30)
                    out["stdout"] = proc.stdout
                    out["stderr"] = proc.stderr
                    out["exit_code"] = proc.returncode
                    out["ok"] = proc.returncode == 0
                except subprocess.TimeoutExpired:
                    out["ok"] = False
                    out["stderr"] = "Command timed out"
                    out["exit_code"] = 124
            else:
                raise PermissionError("Unknown command and shell execution is disabled for safety")

    except Exception as e:
        out["ok"] = False
        out["stderr"] = str(e)
        out["exit_code"] = 1

    return out
