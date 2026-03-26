FROM python:3.12-slim

# Install curl for health check + Node.js 20 for Reclaim zkFetch + build tools for native modules
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl gnupg build-essential && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY worker_node/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies (Reclaim zkFetch)
COPY package.json package-lock.json* ./
RUN npm install --production --registry https://registry.npmmirror.com

# Download ZK proof files required by Reclaim zkFetch (optional, non-fatal)
RUN node node_modules/@reclaimprotocol/zk-fetch/scripts/download-files || echo "ZK files download skipped (non-fatal)"

# Copy worker code
COPY worker_node/ ./worker_node/
COPY schemas/ ./schemas/

# Copy bidding-agent for PCEG API (chain scanning + VeriRank)
COPY client_node/skills/bidding-agent/ ./client_node/skills/bidding-agent/

# Set Node.js memory limit for zkFetch Gnark prover
# NODE_PATH explicitly tells Node.js where to find modules (required for CVM overlay fs)
ENV NODE_OPTIONS="--max-old-space-size=4096"
ENV NODE_PATH="/app/node_modules"

# Expose FastAPI port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run Worker server
CMD ["python", "-m", "uvicorn", "worker_node.server:app", "--host", "0.0.0.0", "--port", "8001"]
