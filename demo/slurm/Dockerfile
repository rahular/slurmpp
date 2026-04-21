FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    slurmctld slurmd slurm-client \
    munge \
    supervisor \
    python3 \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Create directories Slurm needs
RUN mkdir -p \
    /var/spool/slurmctld \
    /var/spool/slurmd \
    /var/log/slurm \
    /var/run/slurm \
    /var/run/munge \
    /etc/slurm

# Fix ownership
RUN chown slurm:slurm /var/spool/slurmctld /var/spool/slurmd /var/log/slurm /var/run/slurm
RUN chown munge:munge /var/run/munge

COPY slurm.conf /etc/slurm/slurm.conf
COPY cgroup.conf /etc/slurm/cgroup.conf
COPY supervisord.conf /etc/supervisor/conf.d/slurm.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 6817 6818

ENTRYPOINT ["/entrypoint.sh"]
