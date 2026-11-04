#!/bin/bash
set -e

# =============================================================================
# NIWI Adaptive Worker & System Safety Manager
# Dynamically adapts background worker concurrency based on host CPU cores
# while strictly reserving headroom so the VM, Nginx, and FastAPI never crash.
# =============================================================================

# 1. Detect total CPU cores visible to the container
TOTAL_CORES=$(nproc 2>/dev/null || echo 1)

# 2. Safety allocation formula:
# - 1 core: 1 worker (safety minimum)
# - 2 cores: 1 worker (leaves 1 core free for OS, Nginx & API)
# - 3 to 4 cores: (TOTAL_CORES - 1) workers (leaves 1 core free for OS, Nginx & API)
# - 5+ cores: (TOTAL_CORES - 2) workers (leaves 2 cores free for system headroom)
if [ "$TOTAL_CORES" -le 2 ]; then
    AUTO_WORKERS=1
elif [ "$TOTAL_CORES" -le 4 ]; then
    AUTO_WORKERS=$((TOTAL_CORES - 1))
else
    AUTO_WORKERS=$((TOTAL_CORES - 2))
fi

# 3. Allow manual override if WORKER_CONCURRENCY is set in environment, else use AUTO_WORKERS
WORKER_COUNT=${WORKER_CONCURRENCY:-$AUTO_WORKERS}

# Guard: Ensure at least 1 worker is always active
if [ "$WORKER_COUNT" -lt 1 ]; then
    WORKER_COUNT=1
fi

RESERVED_CORES=$((TOTAL_CORES - WORKER_COUNT))
if [ "$RESERVED_CORES" -lt 0 ]; then
    RESERVED_CORES=0
fi

echo "=========================================================="
echo "🚀 NIWI Adaptive Concurrency Manager"
echo "   Hardware detected : $TOTAL_CORES CPU core(s)"
echo "   Active workers    : $WORKER_COUNT worker process(es)"
echo "   System safety     : Reserved $RESERVED_CORES core(s) for OS, Nginx & API"
echo "=========================================================="

# 4. Dynamically configure supervisord numprocs for service_bus_worker
SUPERVISOR_CONF="/etc/supervisor/conf.d/supervisord.conf"
if [ -f "$SUPERVISOR_CONF" ]; then
    sed -i "s/^numprocs=.*/numprocs=$WORKER_COUNT/" "$SUPERVISOR_CONF"
fi

# 5. Hand over to supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

