import os
import sys

# Add parent directory (D:\hack) to sys.path so 'backend' module can be found
sys.path.append(r"D:\hack")  # Adjust this if your path is different

import streamlit as st
from backend import executor, monitor

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(page_title="PyTerminal", layout="wide")

# -----------------------------
# Title and description
# -----------------------------
st.title("PyTerminal — Python-based Command Terminal")
st.markdown(
    "Type built-in commands like `ls`, `cd`, `pwd`, `mkdir`, `rm`, `cat`, `mv`, `cp`, "
    "`ps`, `history`, `help`, `cpu`, `mem`."
)

# -----------------------------
# Sidebar - System Monitor
# -----------------------------
with st.sidebar:
    st.header("System Monitor")

    sysinfo = monitor.system_summary()
    st.metric("CPU %", f"{sysinfo['cpu_percent']:.1f}")
    st.metric("Memory %", f"{sysinfo['mem_used_percent']:.1f}")
    st.write("Per-CPU Usage:")
    st.write(sysinfo['per_cpu'])

    st.write("Top processes (by CPU):")
    procs = monitor.top_processes(8, sort_by="cpu")
    for p in procs:
        pname = p['name'] or 'Unknown'
        st.write(f"{p['pid']} — {pname} — CPU: {p['cpu_percent']}% MEM: {p['memory_percent']:.1f}%")

# -----------------------------
# Current directory display
# -----------------------------
cwd = os.getcwd()
st.write(f"**Current directory:** `{cwd}`")

# -----------------------------
# Command input
# -----------------------------
cmd = st.text_input("Command", key="cmd")
run = st.button("Run")

# Safety: do NOT allow arbitrary shell execution on hosted environments
ALLOW_SHELL = False  # Set to True only locally and if safe

if run and cmd:
    res = executor.execute_command(cmd, allow_shell=ALLOW_SHELL)
    if res["stdout"]:
        st.code(res["stdout"])
    if not res["ok"] and res["stderr"]:
        st.error(res["stderr"])
    # Refresh the app to update cwd if changed by `cd`
    st.experimental_rerun()

# -----------------------------
# File Browser
# -----------------------------
st.subheader("File Browser")
path = st.text_input("Path to browse", value=".")

try:
    items = os.listdir(path)
    for it in items:
        full = os.path.join(path, it)
        if os.path.isdir(full):
            st.write(f"📁 {it}")
        else:
            cols = st.columns([0.8, 0.2])
            cols[0].write(it)
            if cols[1].button(f"cat-{it}", key=f"cat-{path}-{it}"):
                try:
                    if os.path.getsize(full) < 200_000:
                        content = open(full, "r", encoding="utf-8", errors="replace").read()
                        st.code(content)
                    else:
                        st.warning("File too large to display.")
                except Exception as fe:
                    st.error(f"Error reading file: {fe}")
except Exception as e:
    st.error(f"Error listing files in path `{path}`: {e}")
