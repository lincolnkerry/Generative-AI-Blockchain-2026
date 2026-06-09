# Hermes Agent for Privacy Router demo
# Build: docker build -t hermes-privacy-router -f demo/hermes/Dockerfile .
# =============================================================================
FROM python:3.13-slim

RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Install Hermes Agent
RUN git clone --depth 1 https://github.com/NousResearch/hermes-agent.git /opt/hermes \
    && cd /opt/hermes \
    && pip install --no-cache-dir -e .

WORKDIR /opt/hermes

# Hermes config is mounted at /root/.hermes/config.yaml
ENV HERMES_HOME=/root/.hermes

EXPOSE 7860

CMD ["hermes", "gateway", "run"]
