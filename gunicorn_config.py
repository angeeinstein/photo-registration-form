# Gunicorn configuration file
import multiprocessing
import os

# Server socket
# Change to "0.0.0.0:80" for network access (requires root or CAP_NET_BIND_SERVICE)
# Or "0.0.0.0:5000" for network access on non-privileged port
bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:5000")
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/photo-registration/access.log"
errorlog = "/var/log/photo-registration/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "photo-registration"

# Server mechanics
daemon = False
pidfile = "/var/run/photo-registration/gunicorn.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in the future)
# keyfile = None
# certfile = None
