# web/app.py
import streamlit as st
import os

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend import executor, monitor
st.set_page_config(page_title="PyTerminal", layout="wide")

st.title("PyTerminal — Python-based Command Terminal")
st.markdown("Type built-in commands (ls, cd, pwd, mkdir, rm, cat, mv, cp, ps, history, help).")

# sidebar - system monitor
with st.sidebar:
    st.header("System Monitor")
    sys = monitor.system_summary()
    st.metric("CPU %", f"{sys['cpu_percent']:.1f}")
    st.metric("Memory %", f"{sys['mem_used_percent']:.1f}")
    st.write("Per-CPU:")
    st.write(sys['per_cpu'])
    st.write("Top processes (by CPU):")
    procs = monitor.top_processes(8, sort_by="cpu")
    for p in procs:
        st.write(f"{p['pid']} — {p['name']} — CPU:{p['cpu_percent']} MEM:{p['memory_percent']:.1f}")

# main UI
cwd = os.getcwd()
st.write(f"**Current directory:** `{cwd}`")

cmd = st.text_input("Command", key="cmd")
run = st.button("Run")

# safety: do NOT allow arbitrary shell execution on hosted environments
ALLOW_SHELL = False  # set to True locally if you know what you're doing

if run and cmd:
    res = executor.execute_command(cmd, allow_shell=ALLOW_SHELL)
    if res["stdout"]:
        st.code(res["stdout"])
    if not res["ok"] and res["stderr"]:
        st.error(res["stderr"])
    # update cwd display if changed
    st.experimental_rerun()

# file browser quick view
st.subheader("File Browser")
path = st.text_input("Path to browse", value=".")
try:
    items = os.listdir(path)
    for it in items:
        full = os.path.join(path, it)
        if os.path.isdir(full):
            st.write(f"📁 {it}   ")
        else:
            cols = st.columns([0.8, 0.2])
            cols[0].write(it)
            if cols[1].button(f"cat-{it}", key=f"cat-{path}-{it}"):
                p = os.path.join(path, it)
                if os.path.getsize(p) < 200_000:
                    st.code(open(p, "r", encoding="utf-8", errors="replace").read())
                else:
                    st.write("File too large to display.")
except Exception as e:
    st.error(str(e))
