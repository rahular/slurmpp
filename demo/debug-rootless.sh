#!/bin/bash
export PATH="$HOME/bin:$PATH"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
mkdir -p "$XDG_RUNTIME_DIR" 2>/dev/null || true

echo "=== System info ==="
uname -r
cat /proc/sys/kernel/unprivileged_userns_clone 2>/dev/null || echo "no unprivileged_userns_clone"

echo "=== uidmap tools ==="
which newuidmap 2>/dev/null || echo "newuidmap not found"
which newgidmap 2>/dev/null || echo "newgidmap not found"

echo "=== /etc/subuid for rahul ==="
grep rahul /etc/subuid 2>/dev/null || echo "no subuid entry"
grep rahul /etc/subgid 2>/dev/null || echo "no subgid entry"

echo "=== Try starting rootless daemon ==="
~/bin/dockerd-rootless.sh 2>&1 &
sleep 3
kill %1 2>/dev/null
