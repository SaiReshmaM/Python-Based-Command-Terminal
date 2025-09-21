# backend/monitor.py
import psutil
from typing import Dict, Any, List

def system_summary() -> Dict[str, Any]:
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    cpu_perc = psutil.cpu_percent(interval=0.1)
    per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
    return {
        "cpu_percent": cpu_perc,
        "per_cpu": per_cpu,
        "mem_total": mem.total,
        "mem_available": mem.available,
        "mem_used_percent": mem.percent,
        "swap_total": swap.total,
        "swap_used_percent": swap.percent,
    }

def top_processes(n: int = 10, sort_by: str = "cpu") -> List[Dict[str, Any]]:
    procs = []
    for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
        try:
            info = p.info
            procs.append(info)
        except Exception:
            pass
    key = "cpu_percent" if sort_by=="cpu" else "memory_percent"
    procs.sort(key=lambda x: x.get(key,0), reverse=True)
    return procs[:n]
