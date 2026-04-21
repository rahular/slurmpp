#!/bin/bash
export PATH="$HOME/bin:$PATH"
ls ~/bin/dockerd-rootless* 2>/dev/null || echo "rootless binaries not found"
tail -20 /tmp/dockerd-rootless.log 2>/dev/null || echo "no log"
