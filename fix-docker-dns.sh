#!/usr/bin/env bash
# Fix Docker DNS for institutional networks where the host DNS is unreachable from containers
set -e

echo "Fixing Docker DNS configuration..."

# Add Google DNS to Docker daemon
sudo tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
    "dns": ["8.8.8.8", "8.8.4.4"],
    "runtimes": {
        "nvidia": {
            "args": [],
            "path": "nvidia-container-runtime"
        }
    }
}
EOF

echo "Restarting Docker..."
sudo systemctl restart docker

echo "Done. Now run: docker compose up --build"
