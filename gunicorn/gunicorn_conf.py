# Socket Path
bind = "unix:/srv/rfam-batch-search/gunicorn.sock"

# Worker Options
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"

# Logging Options
loglevel = "debug"
accesslog = "/var/log/gunicorn/access_log"
errorlog = "/var/log/gunicorn/error_log"
