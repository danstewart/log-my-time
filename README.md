# Log My Time

Basic time logging tool.

## Demo

![file](https://user-images.githubusercontent.com/10670565/168468584-cb9182ad-d82e-4fe5-aa96-c937a826611c.gif)

---

## Setup

#### Running with docker

First create the `config/app_config.py`, then start on http://localhost:4000/ via docker

```bash
# Dev mode
docker-compose up -d --build app

# Prod mode
docker compose -f docker-compose.yml up -d --build
```

#### Install dependencies locally

Requires python 3.10

```bash
# Install JS linter
npm install

# Install python deps with pipenv
pipenv install --categories="packages dev-packages local-packages"

# Start a pipenv shell
pipenv shell
```

#### Connecting to the database

```bash
./scripts/sql.sh
```

#### Running the tests

```bash
./scripts/ctl.sh test
```

#### Database migrations

```bash
docker exec -it log-my-time flask db migrate -m "Description of change"
docker exec -it log-my-time flask db upgrade
```

---

### Built with

-   [Flask](https://flask.palletsprojects.com/en/2.0.x/)
-   [SQLite](https://sqlite.org/index.html)
-   [Flask SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/quickstart/)
-   [SQLAlchemy](https://www.sqlalchemy.org/)
-   [Flask Migrate](https://flask-migrate.readthedocs.io/en/latest/index.html)
-   [Alembic](https://alembic.sqlalchemy.org/en/latest/)
-   [Arrow](https://arrow.readthedocs.io/en/latest/)
-   [Bootstrap 5](https://getbootstrap.com/)
-   [Spacetime](https://spacetime.how/)
