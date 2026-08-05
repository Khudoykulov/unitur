"""Gunicorn configuration for Unitur production server."""

import multiprocessing

# Server socket
bind = "unix:/run/unitur/gunicorn.sock"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/var/log/unitur/gunicorn_access.log"
errorlog = "/var/log/unitur/gunicorn_error.log"
loglevel = "warning"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# Process naming
proc_name = "unitur"

# Server mechanics
daemon = False
pidfile = "/run/unitur/gunicorn.pid"
# user = "unitur"
# group = "unitur"
umask = 0o007

# Graceful restart
graceful_timeout = 30
forwarded_allow_ips = "127.0.0.1"
proxy_allow_ips = "127.0.0.1"
