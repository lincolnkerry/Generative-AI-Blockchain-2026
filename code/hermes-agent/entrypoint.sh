#!/bin/bash
# Start Hermes Gateway (foreground) and Dashboard (background)

# Start dashboard in background (builds web UI on first run)
echo "Starting Hermes Dashboard on port 9119..."
hermes dashboard --host 0.0.0.0 --port 9119 --insecure --no-open &

# Wait for dashboard to be ready
for i in $(seq 1 30); do
    if curl -s http://localhost:9119/ > /dev/null 2>&1; then
        echo "Dashboard ready on port 9119"
        break
    fi
    sleep 1
done

# Start gateway in foreground (keeps container alive)
echo "Starting Hermes Gateway..."
exec hermes gateway run --accept-hooks
