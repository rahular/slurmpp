#!/bin/bash
# Rootless Docker - no root/sudo required
set -e

# Install rootless Docker extras
export PATH="$HOME/bin:$PATH"

# Download rootless extras if not present
if [ ! -f ~/bin/dockerd-rootless.sh ]; then
  curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-rootless-extras-27.5.1.tgz -o /tmp/docker-rootless.tgz
  tar -xzf /tmp/docker-rootless.tgz -C /tmp/
  cp /tmp/docker-rootless-extras/* ~/bin/
  chmod +x ~/bin/dockerd-rootless*
fi

# Ensure uidmap tools are available (for rootless)
export DOCKER_HOST="unix://$XDG_RUNTIME_DIR/docker.sock"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
mkdir -p "$XDG_RUNTIME_DIR"

# Kill existing
pkill -f dockerd-rootless 2>/dev/null; sleep 1

# Start rootless daemon
~/bin/dockerd-rootless.sh &>/tmp/dockerd-rootless.log &
sleep 5

# Test
if ~/bin/docker --host "unix://$XDG_RUNTIME_DIR/docker.sock" version 2>/dev/null | grep -q "Server"; then
  echo "Rootless Docker running!"
  echo "export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock" >> ~/.bashrc
  ~/bin/docker --host "unix://$XDG_RUNTIME_DIR/docker.sock" info 2>/dev/null | grep -E "Context|Docker Root Dir"
else
  echo "Failed to start rootless Docker"
  tail -30 /tmp/dockerd-rootless.log
fi
