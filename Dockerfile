# Fast API - Single Worker Process -- Dockerfile

# pull docker image
FROM python:3.11.1-slim

# set work directory
WORKDIR /code

# copy requirements
COPY ./requirements.txt /code/requirements.txt

# pip install
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy 
COPY ./app /code/app

# 
ENTRYPOINT ["uvicorn", "app.server:APP", "--root-path", "/search-api", "--host", "0.0.0.0", "--port", "80"]