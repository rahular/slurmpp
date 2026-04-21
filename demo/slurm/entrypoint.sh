#!/bin/bash
set -e

echo "=== slurm++ demo cluster startup ==="

# ── Munge setup ──────────────────────────────────────────────────────────────
# Use shared munge key if provided via volume, else generate one
if [ ! -f /etc/munge/munge.key ]; then
    echo "[munge] Generating munge key..."
    dd if=/dev/urandom bs=1 count=1024 > /etc/munge/munge.key 2>/dev/null
fi
chown munge:munge /etc/munge/munge.key
chmod 400 /etc/munge/munge.key
chown munge:munge /var/run/munge
chmod 755 /var/run/munge

# ── Slurm state dirs ─────────────────────────────────────────────────────────
mkdir -p /var/spool/slurmctld /var/spool/slurmd /var/log/slurm /var/run/slurm
chown slurm:slurm /var/spool/slurmctld /var/spool/slurmd /var/log/slurm /var/run/slurm

# ── Create demo users ─────────────────────────────────────────────────────────
for user in alice bob charlie; do
    id "$user" &>/dev/null || useradd -m -s /bin/bash "$user"
done
echo "Demo users created: alice, bob, charlie"

# ── Start supervisor (manages munged + slurmctld + slurmd) ───────────────────
echo "Starting Slurm services via supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/slurm.conf
