# create image to export requirements
FROM python:3.11-slim AS poetry

# build dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        gcc \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# install poetry
RUN python -m pip install --no-cache-dir --upgrade poetry==1.8.2

# copy dependencies
COPY poetry.lock pyproject.toml ./

# create a requirements file
RUN poetry export -f requirements.txt --without-hashes -o /tmp/requirements.txt


# create batch search image
FROM python:3.11-slim as batch-search

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME="/srv/rfam-batch-search"

# create folders and set work directory
RUN mkdir -p $HOME && mkdir /var/log/gunicorn
WORKDIR $HOME

# install requirements
COPY --from=poetry /tmp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . .

# run the FastAPI app
CMD [ "gunicorn", "-c", "gunicorn/gunicorn_conf.py", "-b", "0.0.0.0:8000", "main:app"]
