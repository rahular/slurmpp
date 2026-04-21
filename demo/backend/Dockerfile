FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# System deps: Python 3.12 via deadsnakes PPA + Slurm client + munge client
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common curl ca-certificates gnupg \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.12 python3.12-venv python3-pip \
        slurm-client \
        munge libmunge2 \
        gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Make python3.12 the default
RUN ln -sf /usr/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/bin/python3 /usr/bin/python

# Install pip for 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

WORKDIR /app

# Install Python dependencies directly
RUN python3 -m pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.32.0" \
    "httpx>=0.28.0" \
    "sqlalchemy[asyncio]>=2.0.0" \
    "aiosqlite>=0.20.0" \
    "alembic>=1.14.0" \
    "pyjwt>=2.10.0" \
    "bcrypt>=4.2.0" \
    "ldap3>=2.9.1" \
    "apscheduler>=3.10.4" \
    "pydantic-settings>=2.7.0" \
    "python-multipart>=0.0.20"

COPY ../../backend/app/ app/

# munge socket will be mounted from slurm-node at /var/run/munge
# slurm.conf will be mounted from slurm-node at /etc/slurm
RUN mkdir -p /var/run/munge /etc/slurm /data

# Pre-create the same cluster users as the Slurm node so UID lookups work
RUN useradd -u 1000 -m alice && \
    useradd -u 1001 -m bob && \
    useradd -u 1002 -m charlie && \
    useradd -u 1003 -m dana && \
    useradd -u 1004 -m eve

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
