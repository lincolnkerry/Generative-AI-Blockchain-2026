#!/bin/bash
# Hermes Agent demo startup script
# Installs Hermes Agent and configures it with Privacy Router

echo "=== Hermes Agent + Privacy Router Demo ==="
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
echo "Hermes Agent is configured to use Privacy Router as its LLM provider."
echo "Config: /root/.hermes/config.yaml"
echo ""
echo "Integration points:"
echo "  1. Custom endpoint: ${PRIVACY_ROUTER_URL}/v1 (OpenAI-compatible)"
echo "  2. MCP server: privacy-router tools (classify, process)"
echo ""
echo "Test classify via MCP:"
echo "  Use the 'process' tool with action='classify'"
echo ""
echo "Test generate via API:"
echo "  curl -X POST ${PRIVACY_ROUTER_URL}/v1/chat/completions \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'Authorization: Bearer pr-demo-key' \\"
echo "    -d '{\"model\": \"openrouter/google/gemini-3.1-flash-lite\", \"messages\": [{\"role\": \"user\", \"content\": \"주민등록번호 901212-1234567을 포함한 이메일을 작성해줘\"}]}'"
echo ""

# Keep container running
tail -f /dev/null
