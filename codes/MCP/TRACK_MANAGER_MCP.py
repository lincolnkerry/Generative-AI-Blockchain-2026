import os
import re
import random
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("TrackManager")

MEMORY_FILE = "/home/infonet/.openclaw/MCP/TUTOR_MEMORY.md"

def _read_memory() -> str:
    if not os.path.exists(MEMORY_FILE):
        default_content = "## ACTIVE CURRICULUMS\n"
        _write_memory(default_content)
        return default_content
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return f.read()

def _write_memory(content: str):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def _get_next_track_id() -> str:
    content = _read_memory()
    existing_ids = {
        int(match.group(1))
        for match in re.finditer(r"### TRACK (\d+):", content)
        if match and match.group(1).isdigit()
    }
    next_id = 1
    while next_id in existing_ids:
        next_id += 1
    return str(next_id)

@mcp.tool()
def get_active_track(track_id: str) -> str:
    """
    Retrieves a specific curriculum track from TUTOR_MEMORY.md by its ID.
    """
    content = _read_memory()
    # Find the track section up to the next track or end of file
    pattern = rf"(### TRACK {re.escape(track_id)}:.*?(?=\n### TRACK |\Z))"
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    return f"Error: Track '{track_id}' not found."

@mcp.tool()
def increment_track_day(track_id: str) -> str | None:
    """
    Increments the Current Day counter and updates Last Sent Date in TUTOR_MEMORY.md for a specific track.
    If Current Day reaches Total Days, deletes the track and returns a message to delete the associated cron.
    Otherwise returns None.
    """
    import datetime
    content = _read_memory()
    
    # Locate the track block
    pattern = rf"(### TRACK {re.escape(track_id)}:.*?)(?=\n### TRACK |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return f"Error: Track '{track_id}' not found."
        
    track_block = match.group(1)
    
    # Extract Total Days
    total_days_match = re.search(r"\*\*Total Days:\*\* (\d+)", track_block)
    if not total_days_match:
        return "Error: Could not parse Total Days in track block."
    total_days = int(total_days_match.group(1))
    
    # Extract and increment Current Day
    day_match = re.search(r"\*\*Current Day:\*\* (\d+)", track_block)
    if not day_match:
        return "Error: Could not parse Current Day in track block."
        
    current_day = int(day_match.group(1))
    new_day = current_day + 1
    
    updated_block = re.sub(r"\*\*Current Day:\*\* \d+", f"**Current Day:** {new_day}", track_block)

    # Replace the old track block in the main memory content
    new_content = content.replace(track_block, updated_block)
    _write_memory(new_content)
    
    # Trigger deletion-message only when we've exceeded total days by 1
    if new_day == total_days + 1:
        # Remove the track since it's completed
        delete_track(track_id)
        return f"MUST Delete cron linked to track {track_id}"

    if new_day > total_days + 1:
        # If we somehow exceeded by more than 1, return a warning
        return f"Warning: Track '{track_id}' exceeded Total Days ({total_days}) by {new_day - total_days}. Current Day set to {new_day}."

@mcp.tool()
def delete_track(track_id: str) -> str:
    """
    Deletes a track completely from TUTOR_MEMORY.md based on its ID.
    """
    content = _read_memory()
    pattern = rf"(^|\n)### TRACK {re.escape(track_id)}:.*?(?=\n### TRACK |\Z)"
    
    new_content, count = re.subn(pattern, "", content, flags=re.DOTALL)
    
    if count > 0:
        _write_memory(new_content.strip() + "\n")
        return f"Success: Track '{track_id}' completely removed from memory."
    return f"Error: Track '{track_id}' could not be found for deletion."

@mcp.tool()
def add_new_track(
    theme: str,
    mode: str,
    recipient: str,
    total_days: int,
    syllabus_table: str,
    track_id: str | None = None
) -> str:
    """
    Appends a newly generated curriculum track to TUTOR_MEMORY.md.
    theme = The overarching theme or subject of the curriculum.
    mode = Either "RÉVISION" or "DÉCOUVERTE", which determines the structure of the syllabus table and the nature of the lessons.
    recipient = Discord ID User
    total_days = Total number of days
    syllabus_table = Preformatted markdown table with the outline you have created.
     - **syllabus Template:** Use the exact markdown table format corresponding to the mode:
     - For RÉVISION mode: `| Day | Topic | Source File | Target Pages |`
     - For DÉCOUVERTE mode: `| Day | Topic |` (Do NOT include file or page columns).
    Chooses the smallest available numeric track ID and returns it.
            """
    content = _read_memory()
    if not track_id:
        track_id = _get_next_track_id()

    mode_value = mode.strip() if isinstance(mode, str) else str(mode)

    new_track_block = f"""
### TRACK {track_id}: {theme}
**Mode:** {mode_value}
**Recipient:** {recipient}
**Total Days:** {total_days}
**Current Day:** 1

**Syllabus:**
{syllabus_table}
"""
    
    # Append the new track at the end of the file
    if not content.endswith("\n"):
        content += "\n"
    
    content += new_track_block
    _write_memory(content)
    random_number = random.randint(1000, 9999)
    return f"Success: New track '{track_id}' perfectly added to TUTOR_MEMORY.md. Random number: {random_number}"

if __name__ == "__main__":
    mcp.run()