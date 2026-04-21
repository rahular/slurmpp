#!/bin/bash
RUNDIR="/mnt/c/Users/rahul/AppData/Local/Docker/run"
echo "Before:"
ls -la "$RUNDIR/"

for f in dockerInference userAnalyticsOtlpHttp.sock; do
  if [ -e "$RUNDIR/$f" ]; then
    rm -f "$RUNDIR/$f" && echo "Deleted: $f" || echo "Failed to delete: $f"
  fi
done

echo "After:"
ls -la "$RUNDIR/"
