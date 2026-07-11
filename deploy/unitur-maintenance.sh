#!/bin/bash
# =============================================================================
# unitur-maintenance — safe daily disk housekeeping
# Installed as /etc/cron.daily/unitur-maintenance (runs as root, once a day)
#
# Touches ONLY logs and the package cache. It NEVER touches:
#   - the PostgreSQL database (/var/lib/postgresql)
#   - uploaded media (/var/www/unitur/media)
#   - application code, .env, or static files
# Logs are event records, not data — trimming old ones is safe and standard.
# =============================================================================

# 1) Keep the systemd journal within 100 MB
journalctl --vacuum-size=100M >/dev/null 2>&1

# 2) Drop downloaded .deb package cache (re-downloadable)
apt-get clean >/dev/null 2>&1

# 3) Rotate/compress logs per the system logrotate rules
/usr/sbin/logrotate /etc/logrotate.conf >/dev/null 2>&1

# 4) Safety net: if the root disk is still ≥90% full, trim the volatile
#    system logs that tend to balloon during error storms (e.g. OOM spam).
USE=$(df --output=pcent / 2>/dev/null | tr -dc '0-9')
if [ "${USE:-0}" -ge 90 ]; then
    truncate -s 0 /var/log/syslog /var/log/kern.log 2>/dev/null
    journalctl --vacuum-size=50M >/dev/null 2>&1
    logger -t unitur-maintenance "emergency log trim — root disk was ${USE}%"
fi
