# OpenClaw agent for Privacy Router demo
# Build: docker build -t openclaw-privacy-router -f demo/openclaw/Dockerfile .
FROM node:24-slim


RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install OpenClaw with pnpm
RUN git clone --depth 1 https://github.com/openclaw/openclaw.git /opt/openclaw \
    && cd /opt/openclaw \
    && corepack enable \
    && pnpm install \
    && pnpm build
WORKDIR /opt/openclaw

# OpenClaw config is mounted at /home/node/.openclaw/openclaw.json
ENV OPENCLAW_STATE_DIR=/home/node/.openclaw
ENV OPENCLAW_CONFIG_PATH=/home/node/.openclaw/openclaw.json

EXPOSE 18789 18790

CMD ["node", "dist/index.js", "gateway", "--bind", "lan", "--port", "18789"]
