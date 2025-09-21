# web/app.py
import sys
import os

# Add parent folder to sys.path so backend can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

    sys_stats = monitor.system_summary()
    st.metric("CPU %", f"{sys_stats['cpu_percent']:.1f}")
    st.metric("Memory %", f"{sys_stats['mem_used_percent']:.1f}")
    st.write("Per-CPU Usage:")
    st.write(sys_stats['per_cpu'])

    st.write("Top processes (by CPU):")
    procs = monitor.top_processes(8, sort_by="cpu")
    for p in procs:
        st.write(f"{p['pid']} — {p['name']} — CPU:{p['cpu_percent']} MEM:{p['memory_percent']:.1f}")

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
ALLOW_SHELL = False  # Set True locally only if safe

if run and cmd:
    res = executor.execute_command(cmd, allow_shell=ALLOW_SHELL)
    if res["stdout"]:
        st.code(res["stdout"])
    if not res["ok"] and res["stderr"]:
        st.error(res["stderr"])
    # Refresh to update cwd if changed
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
                if os.path.getsize(full) < 200_000:
                    st.code(open(full, "r", encoding="utf-8", errors="replace").read())
                else:
                    st.write("File too large to display.")
except Exception as e:
    st.error(str(e))
