# For native Python runtime deploys on Render
web: gunicorn geneweb.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --chdir src
