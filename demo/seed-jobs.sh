#!/bin/bash
# Seed demo jobs into the Slurm cluster
# Runs inside a container that has slurm-client and shares munge socket

set -e

echo "=== Seeding demo jobs ==="

# Wait for munge socket to be ready
for i in $(seq 1 20); do
    if [ -S /var/run/munge/munge.socket.2 ]; then
        echo "Munge socket ready."
        break
    fi
    echo "Waiting for munge socket... ($i/20)"
    sleep 2
done

# Test munge works
munge -n | unmunge > /dev/null 2>&1 && echo "Munge auth OK" || echo "Munge warning (may still work)"

# Create demo users in this container
for user in alice bob charlie; do
    id "$user" &>/dev/null || useradd -m -s /bin/bash "$user" 2>/dev/null || true
done

# Wait a bit more for Slurm to be fully ready
sleep 5

# Test squeue works
echo "Testing squeue..."
squeue --json > /dev/null && echo "squeue OK" || { echo "squeue failed, exiting"; exit 0; }

# ── Submit demo jobs ──────────────────────────────────────────────────────────

# Helper: submit a batch script as a given user
submit_job() {
    local user="$1"
    local jobname="$2"
    local partition="$3"
    local cpus="$4"
    local time="$5"
    local script="$6"

    local tmpfile=$(mktemp /tmp/job-XXXXXX.sh)
    cat > "$tmpfile" << EOF
#!/bin/bash
#SBATCH --job-name=$jobname
#SBATCH --partition=$partition
#SBATCH --cpus-per-task=$cpus
#SBATCH --time=$time
#SBATCH --output=/tmp/slurm-%j.out

$script
EOF
    su - "$user" -c "sbatch $tmpfile" 2>&1 | tail -1
    rm -f "$tmpfile"
}

echo ""
echo "--- Submitting RUNNING jobs ---"

# Alice: 2 GPU simulation jobs (long running)
submit_job alice "gpu-train-resnet" general 2 "02:00:00" "
echo 'Starting ResNet training simulation...'
echo 'Epoch 1/50: loss=2.3156'
sleep 3600
"

submit_job alice "gpu-train-bert" general 4 "04:00:00" "
echo 'Fine-tuning BERT model...'
echo 'Loading tokenizer and model weights'
sleep 7200
"

# Bob: data processing job
submit_job bob "data-preprocess" general 2 "01:00:00" "
echo 'Preprocessing genomics dataset...'
echo 'Reading FASTQ files from /data/raw/'
sleep 3600
"

# Bob: MPI simulation
submit_job bob "mpi-md-sim" general 4 "03:00:00" "
echo 'Running molecular dynamics simulation'
echo 'Timestep 0/10000000'
sleep 10800
"

# Charlie: smaller job
submit_job charlie "postprocess" debug 1 "00:30:00" "
echo 'Running postprocessing pipeline'
sleep 1800
"

echo ""
echo "--- Submitting PENDING jobs (resource contention) ---"

# Request more CPUs than available to force pending
submit_job alice "large-sweep" general 8 "08:00:00" "
echo 'Hyperparameter sweep'
sleep 28800
"

submit_job bob "waiting-job" general 8 "02:00:00" "
echo 'Batch inference job'
sleep 7200
"

echo ""
echo "--- Submitting quick jobs (will complete soon) ---"

submit_job charlie "quick-test" debug 1 "00:05:00" "
echo 'Running unit tests...'
echo 'Tests passed: 47/47'
sleep 10
echo 'Done.'
"

echo ""
echo "=== Job seeding complete ==="
squeue -o "%.10i %.20j %.8u %.9P %.8T %.10M %.6D %R"
