#!/bin/bash
# Install static Docker binaries into WSL2
sudo cp /tmp/docker/docker /usr/local/bin/
sudo cp /tmp/docker/dockerd /usr/local/bin/
sudo cp /tmp/docker/containerd /usr/local/bin/
sudo cp /tmp/docker/containerd-shim-runc-v2 /usr/local/bin/
sudo cp /tmp/docker/docker-proxy /usr/local/bin/
sudo cp /tmp/docker/docker-init /usr/local/bin/
sudo cp /tmp/docker/runc /usr/local/bin/
sudo chmod +x /usr/local/bin/docker*
echo "Docker installed:"
docker --version
