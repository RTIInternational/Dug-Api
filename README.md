# Dug Fast API

Skinny Dug API built with Fast API.  

Made specifically to be efficent as a kubneretes pod so it is ran as single worker process only allowing the cluster level to handle replication and load balancing.

## Start up

Configure the correct environment variables for your setup with ElasticSearch in the `.env`. In production the pod service name is `elasticsearch`.

Run `docker compose up -d` and view the test output at **localhost:5551/docs**

## Local Development

From the root `/dug-semantic-search-api` directory.

1) `python3 -m venv ~/.environments/dug-api`
2) `source ~/.environments/dug-api/bin/activate`
3) `pip install -r requirements.txt`
4) Configure the correct environment variables for your setup with ElasticSearch in the `.env`
5) `sh setup.sh`
6) `gunicorn -k uvicorn.workers.UvicornWorker app.server:APP`
7) Test the API by opening your browser at <http://127.0.0.1:8000/docs>
