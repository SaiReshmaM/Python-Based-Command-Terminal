# cli.py

import psutil

# Handle readline import for cross-platform compatibility
try:
    import readline
except ImportError:
    import pyreadline3 as readline

from backend.executor import execute_command


# -------------------------------
# System Monitoring Commands
# -------------------------------
def cpu():
    """Print current CPU usage."""
    print(f"CPU Usage: {psutil.cpu_percent()}%")


def mem():
    """Print current memory usage."""
    mem_info = psutil.virtual_memory()
    print(f"Memory Usage: {mem_info.percent}% "
          f"({mem_info.used / (1024**3):.2f}GB used / {mem_info.total / (1024**3):.2f}GB total)")


# -------------------------------
# Main CLI loop
# -------------------------------
def main():
    print("PyTerminal CLI - type 'help' for commands. Ctrl-C to exit.")
    allow_shell = True  # local CLI can enable shell fallback

    while True:
        try:
            # Show current working directory in prompt
            inp = input(f"{__import__('os').getcwd()} $ ")

            if not inp.strip():
                continue

            # Execute command
            res = execute_command(inp, allow_shell=allow_shell)

            # Print stdout if available
            if res["stdout"]:
                print(res["stdout"])

            # Print stderr if command failed
            if not res["ok"] and res["stderr"]:
                print("ERROR:", res["stderr"])

        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            print("Exception:", e)


# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    main()
