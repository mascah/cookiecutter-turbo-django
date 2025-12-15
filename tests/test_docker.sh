#!/bin/sh
# this is a very simple script that tests the docker configuration for the Platform Django template
# it is meant to be run from the root directory of the repository, eg:
# sh tests/test_docker.sh

set -o errexit
set -x
set -e

finish() {
  # Your cleanup code here
  docker compose -f docker-compose.local.yml down --remove-orphans
  docker volume rm platform_django_platform_django_local_postgres_data

}
# the cleanup doesn't work in the github actions
if [ -z "$GITHUB_ACTIONS" ]; then
  trap finish EXIT
fi


# create a cache directory
mkdir -p .cache/docker
cd .cache/docker

sudo rm -rf platform_django

# Build data arguments for copier (convert key=value to -d key=value)
DATA_ARGS=""
for arg in "$@"; do
  DATA_ARGS="$DATA_ARGS -d $arg"
done

# create the project using the default settings in copier.yaml
uv run copier copy ../../ platform_django --trust --defaults $DATA_ARGS
cd platform_django

# make sure all images build
docker compose -f docker-compose.local.yml build

docker compose -f docker-compose.local.yml run django uv lock

docker compose -f docker-compose.local.yml build

# run the project's type checks
docker compose -f docker-compose.local.yml run --rm django mypy platform_django

# run the project's tests
docker compose -f docker-compose.local.yml run --rm django pytest

# return non-zero status code if there are migrations that have not been created
docker compose -f docker-compose.local.yml run --rm django python manage.py makemigrations --check || { echo "ERROR: there were changes in the models, but migration listed above have not been created and are not saved in version control"; exit 1; }

# Test support for translations
docker compose -f docker-compose.local.yml run --rm django python manage.py makemessages --all

# Build frontend assets (required for production checks)
if [ -f "package.json" ]
then
    pnpm install
    pnpm run build
fi

# Make sure the check doesn't raise any warnings
docker compose -f docker-compose.local.yml run --rm \
  -e DJANGO_SECRET_KEY="$(openssl rand -base64 64)" \
  -e REDIS_URL=redis://redis:6379/0 \
  -e DJANGO_AWS_ACCESS_KEY_ID=x \
  -e DJANGO_AWS_SECRET_ACCESS_KEY=x \
  -e DJANGO_AWS_STORAGE_BUCKET_NAME=x \
  -e DJANGO_ADMIN_URL=x \
  -e MAILGUN_API_KEY=x \
  -e MAILGUN_DOMAIN=x \
  -e SENTRY_DSN=https://key@o123.ingest.sentry.io/123 \
  django python manage.py check --settings=config.settings.production --deploy --database default --fail-level WARNING

# Generate the HTML for the documentation
docker compose -f docker-compose.docs.yml run --rm docs make html

docker build -f ./docker/production/django/Dockerfile -t django-prod .

docker run --rm \
--env-file .env \
--network platform_django_default \
-e DJANGO_SECRET_KEY="$(openssl rand -base64 64)" \
-e REDIS_URL=redis://redis:6379/0 \
-e DJANGO_AWS_ACCESS_KEY_ID=x \
-e DJANGO_AWS_SECRET_ACCESS_KEY=x \
-e DJANGO_AWS_STORAGE_BUCKET_NAME=x \
-e DJANGO_ADMIN_URL=x \
-e MAILGUN_API_KEY=x \
-e MAILGUN_DOMAIN=x \
-e SENTRY_DSN=https://key@o123.ingest.sentry.io/123 \
django-prod python manage.py check --settings=config.settings.production --deploy --database default --fail-level WARNING
