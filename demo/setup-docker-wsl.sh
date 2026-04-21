#!/bin/bash
set -e

# Install to user bin (no sudo needed)
mkdir -p ~/bin
cp /tmp/docker/docker ~/bin/
cp /tmp/docker/dockerd ~/bin/
cp /tmp/docker/containerd ~/bin/
cp /tmp/docker/containerd-shim-runc-v2 ~/bin/
cp /tmp/docker/docker-proxy ~/bin/
cp /tmp/docker/docker-init ~/bin/
cp /tmp/docker/runc ~/bin/
chmod +x ~/bin/docker*
chmod +x ~/bin/containerd* ~/bin/runc

# Also install to /usr/local/bin via tee trick (avoids dpkg lock issue)
cat /tmp/docker/docker | sudo tee /usr/local/bin/docker > /dev/null
cat /tmp/docker/dockerd | sudo tee /usr/local/bin/dockerd > /dev/null
sudo chmod +x /usr/local/bin/docker /usr/local/bin/dockerd
sudo chmod +x ~/bin/containerd*

# Start dockerd in background (needs iptables)
sudo mkdir -p /var/run
sudo dockerd --data-root /tmp/docker-data &>/tmp/dockerd.log &
sleep 2

echo "Docker CLI:"
docker --version 2>/dev/null || ~/bin/docker --version
echo "dockerd running: $(pgrep dockerd > /dev/null && echo yes || echo no)"
