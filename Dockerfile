# syntax = docker/dockerfile:1.2

FROM python:3.12-slim-bookworm

LABEL version="0.0.1"

ARG TEST_MODE=${TEST_MODE:-0}

# Set env vars
ENV FLASK_APP="${FLASK_APP}"
ENV FLASK_DEBUG="${FLASK_DEBUG}"

# Disable auto-cleanup after install:
RUN rm /etc/apt/apt.conf.d/docker-clean

# Install updates and cache across builds
ENV DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/var/cache/apt,id=apt \
    apt-get update \
    && apt-get -y upgrade \
    && apt-get install -y --no-install-recommends \
    curl sqlite3 libsqlite3-dev procps \
    && if [ "$TEST_MODE" = "1" ]; then apt-get install -y --no-install-recommends chromium-driver libnss3 libasound2; fi \
    && rm -rf /var/lib/apt/lists/*

# Create user and work dir
RUN useradd --create-home app
USER app
WORKDIR /home/app/log-my-time
RUN mkdir --parents /home/app/log-my-time
RUN mkdir --parents /home/app/log-my-time/db/

# Configure sqlite
COPY config/sqliterc /home/app/.sqliterc

# Set PATH
ENV PATH="/home/app/.local/bin/:${PATH}"
ENV PROJECT_ROOT='/home/app/log-my-time'

# Install python deps
RUN pip install pipenv
COPY --chown=app ./requirements.txt ./
RUN pip install -r requirements.txt

# Install playwright
RUN bash -c '[[ $TEST_MODE == 1 && ! -d ~/.cache/ms-playwright/chromium* ]] && python -m playwright install chromium || true'

# Get traceback for C crashes
ENV PYTHONFAULTHANDLER=1

# Copy the source code
COPY --chown=app:app . ./

# Run
EXPOSE 5000

# Blank entrypoint allows passing custom commands via `docker run`
ENTRYPOINT [  ]

CMD [ "./entrypoint.sh" ]
