# Hermes Agent — Privacy Router Demo
# Domain-specific demo environment with tools for real work
# Build: docker build -t hermes-privacy-demo -f hermes-agent/Dockerfile .
# =============================================================================
FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    git curl xz-utils npm jq ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Install Hermes Agent with MCP support
RUN git clone --depth 1 https://github.com/NousResearch/hermes-agent.git /opt/hermes \
    && cd /opt/hermes \
    && pip install --no-cache-dir -e '.[mcp]'

# Install MCP servers for tools
RUN npm install -g \
    @modelcontextprotocol/server-filesystem \
    @playwright/mcp@latest

# Install Playwright browsers for agent-browser
RUN npx playwright install --with-deps chromium

WORKDIR /opt/hermes

# Privacy Router MCP server (lightweight HTTP client)
COPY server/mcp/lightweight.py /opt/hermes/server/mcp/lightweight.py

# Demo workspace
RUN mkdir -p /workspace/demo /workspace/docs

# Hermes config is mounted at /root/.hermes/config.yaml
ENV HERMES_HOME=/root/.hermes
ENV HERMES_ALLOW_ROOT_GATEWAY=1
ENV GATEWAY_ALLOW_ALL_USERS=true

EXPOSE 7860

CMD ["hermes", "gateway", "run", "--accept-hooks"]
