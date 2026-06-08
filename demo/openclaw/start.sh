#!/bin/bash
# OpenClaw demo startup script
# Installs OpenClaw and starts it with Privacy Router as provider

echo "=== OpenClaw + Privacy Router Demo ==="
echo "Privacy Router: ${PRIVACY_ROUTER_URL}"
echo ""

# Wait for Privacy Router to be ready
echo "Waiting for Privacy Router..."
for i in $(seq 1 30); do
    if curl -s "${PRIVACY_ROUTER_URL}/docs" > /dev/null 2>&1; then
        echo "Privacy Router is ready!"
        break
    fi
    sleep 2
done

echo ""
echo "OpenClaw is configured to use Privacy Router as its LLM provider."
echo "Config: /root/.openclaw/config.json"
echo ""
echo "To test manually:"
echo "  curl -X POST ${PRIVACY_ROUTER_URL}/v1/chat/completions \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'Authorization: Bearer pr-demo-key' \\"
echo "    -d '{\"model\": \"openrouter/google/gemini-3.1-flash-lite\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}'"
echo ""

# Keep container running
tail -f /dev/null
