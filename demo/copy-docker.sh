#!/bin/bash
# No sudo - copy to user bin only
mkdir -p ~/bin
for f in docker dockerd containerd containerd-shim-runc-v2 docker-proxy docker-init runc; do
  cp /tmp/docker/$f ~/bin/ 2>/dev/null && echo "copied $f"
done
chmod +x ~/bin/*
echo "PATH: ~/bin/docker --version:"
~/bin/docker --version
