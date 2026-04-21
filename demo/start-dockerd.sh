#!/bin/bash
# Start dockerd using sudo (daemon needs root for networking)
# Kill any existing
sudo pkill dockerd 2>/dev/null; sleep 1

# Start daemon
sudo ~/bin/dockerd \
  --data-root /var/lib/docker \
  --host unix:///var/run/docker.sock \
  --pidfile /var/run/docker.pid \
  &>/tmp/dockerd.log &

sleep 3

# Check it's running
if sudo ~/bin/docker --host unix:///var/run/docker.sock version 2>/dev/null | grep -q "Server"; then
  echo "dockerd is running"
  # Allow group access
  sudo chmod 666 /var/run/docker.sock
  ~/bin/docker version
else
  echo "dockerd failed to start"
  tail -20 /tmp/dockerd.log
fi
