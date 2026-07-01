# HEARTBEAT PROTOCOL

When triggered by a system `HEARTBEAT` event (polling without user input):

1. **Passive State:** Do not initiate conversations or send lessons.
2. **Maintenance:** Silently review `TUTOR_MEMORY.md` via `fs_read` to ensure no corrupted JSON or markdown structures exist. 
3. **Quiet Hours:** If the current system time is between 23:00 and 08:00 KST, immediately yield a `HEARTBEAT_OK` state and terminate the execution cycle. Do not invoke external web searches or APIs during this window.