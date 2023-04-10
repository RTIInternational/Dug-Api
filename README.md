# Dug Fast API

Skinny Dug API built with Fast API.  

Made specifically to be efficent as a kubneretes pod so it is ran as single worker process only allowing the cluster level to handle replication and load balancing.

## Start up

Run `docker build -t dug-fast-api .` and wait for the build to finish

Run `docker run -d --name dug-api -p 80:80 dug-fast-api` and view the test output at **localhost**
