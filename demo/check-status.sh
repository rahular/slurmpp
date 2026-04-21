#!/bin/bash
echo "=== Running processes ==="
ps aux | grep -E "apt|dpkg|dockerd" | grep -v grep

echo ""
echo "=== Docker binary ==="
~/bin/docker --version 2>/dev/null || echo "not in ~/bin"
which docker 2>/dev/null || echo "not in PATH"

echo ""
echo "=== Node.js ==="
node --version 2>/dev/null || echo "node not in PATH"
