"""Gunicorn config for Docker (TCP bind instead of UNIX socket)."""

import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
accesslog = "-"   # stdout
errorlog = "-"    # stderr
loglevel = "warning"
forwarded_allow_ips = "*"
proxy_allow_ips = "*"
