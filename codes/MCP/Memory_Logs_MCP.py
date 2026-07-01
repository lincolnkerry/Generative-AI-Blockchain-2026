import os
import json
import datetime
from mcp.server.fastmcp import FastMCP

# Secure relative paths to avoid path errors
BASE = os.path.dirname(os.path.abspath(__file__))
MEM_FILE = os.path.join(BASE, "MEMORY.json")
LOG_FILE = os.path.join(BASE, "activity.log")

mcp = FastMCP("Sully_Memory")

def _ensure_files():
    """Create the base files if they are missing."""
    if not os.path.exists(MEM_FILE):
        with open(MEM_FILE, 'w') as f:
            json.dump({}, f)
            
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            f.write("")

@mcp.tool()
def store(k: str, v: str) -> str:
    """Store a key-value pair in memory."""
    _ensure_files()
    with open(MEM_FILE, 'r') as f: 
        m = json.load(f)
        
    m[k] = v
    with open(MEM_FILE, 'w') as f: 
        json.dump(m, f, indent=4)
    return f"Memorized: {k}"

@mcp.tool() 
def read(k: str = "") -> str:
    """Read memory by key or list all keys."""
    _ensure_files()
    with open(MEM_FILE, 'r') as f: 
        m = json.load(f)
    return str(m.get(k, m)) if k else str(list(m.keys()))

@mcp.tool()
def log(username: str, discord_id: str, tool: str, description: str) -> str:
    """Log an action in the format Date Username Discord_ID Tool Description
    Date : Format YYYY-MM-DD HH:MM:SS
    Username : The display name of the user
    Discord_ID : The Discord user identifier
    Tool : Name of the MCP function used
    Description : Details about the performed action, such as modified memory keys or errors encountered.
    """
    _ensure_files()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"{timestamp} {username} {discord_id} {tool} {description}\n"
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(formatted)
    return "Logged."

@mcp.tool()
def get_logs(n: int = 5) -> str:
    """Read the latest logs."""
    _ensure_files()
    with open(LOG_FILE, 'r', encoding='utf-8') as f: 
        lines = f.readlines()
    return "".join(lines[-n:])

if __name__ == "__main__": 
    mcp.run()