Getting Up and Running Locally With Docker
==========================================

.. index:: Docker

Prerequisites
-------------

* Docker; if you don't have it yet, follow the `installation instructions`_;
* Docker Compose; refer to the official documentation for the `installation guide`_.
* Pre-commit; refer to the official documentation for the `pre-commit`_.
* Copier; install via ``pip install copier`` or ``pipx install copier``, see `Copier`_
* (Optional) direnv; for running management commands from your host machine, see `direnv`_.

.. _`installation instructions`: https://docs.docker.com/install/
.. _`installation guide`: https://docs.docker.com/compose/install/
.. _`pre-commit`: https://pre-commit.com/#install
.. _`Copier`: https://copier.readthedocs.io/
.. _`direnv`: https://direnv.net/

Before Getting Started
----------------------
.. include:: generate-project-block.rst

Build the Stack
---------------

This can take a while, especially the first time you run this particular command on your development system::

    docker compose -f docker-compose.local.yml build

For production deployments, see the deployment guides (:doc:`/3-deployment/deployment-on-heroku` or :doc:`/3-deployment/deployment-on-aws`) which use different deployment mechanisms rather than Docker Compose.

After we have created our initial image we need to generate a lockfile for our dependencies.
Docker cannot write to the host system during builds, so we have to run the command to generate the lockfile in the container.
This is important for reproducible builds and to ensure that the dependencies are installed correctly in the container.
Updating the lockfile manually is normally not necessary when you add packages through ``uv add <package_name>``::

    docker compose -f docker-compose.local.yml run --rm django uv lock

To be sure we are on the right track we need to build our image again::

    docker compose -f docker-compose.local.yml build

Before doing any git commit, `pre-commit`_ should be installed globally on your local machine, and then::

    git init
    pre-commit install

Failing to do so will result with a bunch of CI and Linter errors that can be avoided with pre-commit.

Run the Stack
-------------

This brings up both Django and PostgreSQL. The first time it is run it might take a while to get started, but subsequent runs will occur quickly.

Open a terminal at the project root and run the following for local development::

    docker compose -f docker-compose.local.yml up

You can also set the environment variable ``COMPOSE_FILE`` pointing to ``docker-compose.local.yml`` like this::

    export COMPOSE_FILE=docker-compose.local.yml

And then run::

    docker compose up

To run in a detached (background) mode, just::

    docker compose up -d

The site should start and be accessible at http://localhost:8000.

Execute Management Commands
---------------------------

From Docker Container
~~~~~~~~~~~~~~~~~~~~~

As with any shell command that we wish to run in our container, this is done using the ``docker compose -f docker-compose.local.yml run --rm`` command::

    docker compose -f docker-compose.local.yml run --rm django python manage.py migrate
    docker compose -f docker-compose.local.yml run --rm django python manage.py createsuperuser

Here, ``django`` is the target service we are executing the commands against.
Also, please note that the ``docker exec`` does not work for running management commands.

From Host Machine (using direnv)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While Docker is recommended for running the full stack, you can run Django management commands directly from your host machine. This is useful for quick commands without the Docker overhead.

1. Install `direnv`_ and allow the project's ``.envrc``::

    direnv allow

2. The ``.envrc`` file loads your ``.env`` and constructs ``DATABASE_URL`` to point at the Docker PostgreSQL container::

    dotenv
    export DATABASE_URL=postgres://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB

3. Ensure Docker services are running::

    docker compose -f docker-compose.local.yml up -d postgres

   If using Celery, also start Redis::

    docker compose -f docker-compose.local.yml up -d postgres redis

4. Run management commands directly from your host::

    python manage.py migrate
    python manage.py shell
    python manage.py createsuperuser

.. note::

    This approach requires Python and your project dependencies installed on your host machine.
    Use ``uv sync`` to install dependencies locally.

(Optionally) Designate your Docker Development Server IP
--------------------------------------------------------

When ``DEBUG`` is set to ``True``, the host is validated against ``['localhost', '127.0.0.1', '[::1]']``. This is adequate when running a ``virtualenv``. For Docker, in the ``config.settings.local``, add your host development server IP to ``INTERNAL_IPS`` or ``ALLOWED_HOSTS`` if the variable exists.

.. _envs:

Configuring the Environment
---------------------------

This project uses a single ``.env`` file for all environment configuration. When you generate a project, this file is automatically created with secure random values.

This is the excerpt from your project's ``docker-compose.local.yml``::

  services:
    django:
      # ...
      env_file:
        - ./.env

    postgres:
      image: docker.io/postgres:18
      # ...
      env_file:
        - ./.env

The ``.env`` file contains all configuration for both Django and PostgreSQL::

    # PostgreSQL
    POSTGRES_HOST=postgres
    POSTGRES_PORT=5432
    POSTGRES_DB=<your project slug>
    POSTGRES_USER=<auto-generated>
    POSTGRES_PASSWORD=<auto-generated>

    # Django
    DJANGO_READ_DOT_ENV_FILE=True
    USE_DOCKER=yes
    DJANGO_SECRET_KEY=<auto-generated>
    DJANGO_ADMIN_URL=<auto-generated>/

    # Redis (if Celery enabled)
    REDIS_URL=redis://redis:6379/0

    # Frontend
    VITE_API_URL=http://localhost:8000

For more details on configuration, see :doc:`/1-getting-started/configuration`.

.. seealso::

   Ready to add your first module? See :doc:`/4-guides/adding-modules` for a complete guide on adding new modules to your modular monolith.


Tips & Tricks
-------------

Add 3rd party python packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install a new 3rd party python package, you cannot use ``uv add <package_name>``, that would only add the package to the container. The container is ephemeral, so that new library won't be persisted if you run another container. Instead, you should modify the Docker image:
You have to modify pyproject.toml and either add it to project.dependencies or to tool.uv.dev-dependencies by adding::

    "<package_name>==<package_version>"

To get this change picked up, you'll need to rebuild the image(s) and restart the running container::

    docker compose -f docker-compose.local.yml build
    docker compose -f docker-compose.local.yml up

Debugging
~~~~~~~~~

ipdb
"""""

If you are using the following within your code to debug::

    import ipdb; ipdb.set_trace()

Then you may need to run the following for it to work as desired::

    docker compose -f docker-compose.local.yml run --rm --service-ports django


django-debug-toolbar
""""""""""""""""""""

In order for ``django-debug-toolbar`` to work designate your Docker Machine IP with ``INTERNAL_IPS`` in ``local.py``.


docker
""""""

The ``container_name`` from the yml file can be used to check on containers with docker commands, for example::

    docker logs <project_slug>_local_celeryworker
    docker top <project_slug>_local_celeryworker

Notice that the ``container_name`` is generated dynamically using your project slug as a prefix

Mailpit
~~~~~~~

When developing locally you can go with Mailpit_ for email testing provided ``use_mailpit`` was set to ``true`` during generation. To proceed,

#. make sure ``<project_slug>_local_mailpit`` container is up and running;

#. open up ``http://127.0.0.1:8025``.

.. _Mailpit: https://github.com/axllent/mailpit/

.. _`CeleryTasks`:

Celery tasks in local development
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When not using docker Celery tasks are set to run in Eager mode, so that a full stack is not needed. When using docker the task scheduler will be used by default.

If you need tasks to be executed on the main thread during development set ``CELERY_TASK_ALWAYS_EAGER = True`` in ``config/settings/local.py``.

Possible uses could be for testing, or ease of profiling with DJDT.

.. _`CeleryFlower`:

Celery Flower
~~~~~~~~~~~~~

`Flower`_ is a "real-time monitor and web admin for Celery distributed task queue".

Prerequisites:

* ``use_celery`` was set to ``true`` during project generation.

By default, it's enabled in local development (``docker-compose.local.yml``) through a ``flower`` service. For added security, ``flower`` requires its clients to provide authentication credentials specified in the ``.env`` file as ``CELERY_FLOWER_USER`` and ``CELERY_FLOWER_PASSWORD`` environment variables. Check out ``localhost:5555`` and see for yourself.

.. _`Flower`: https://github.com/mher/flower


Using Just for Docker Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We have included a ``justfile`` to simplify the use of frequent Docker commands for local development.

.. warning::
    Currently, "Just" does not reliably handle signals or forward them to its subprocesses. As a result,
    pressing CTRL+C (or sending other signals like SIGTERM, SIGINT, or SIGHUP) may only interrupt
    "Just" itself rather than its subprocesses.
    For more information, see `this GitHub issue <https://github.com/casey/just/issues/2473>`_.

First, install Just using one of the methods described in the `official documentation <https://just.systems/man/en/packages.html>`_.

Here are the available commands:

- ``just build``
  Builds the Python image using the local Docker Compose file.

- ``just up``
  Starts the containers in detached mode and removes orphaned containers.

- ``just down``
  Stops the running containers.

- ``just prune``
  Stops and removes containers along with their volumes. You can optionally pass an argument with the service name to prune a single container.

- ``just logs``
  Shows container logs. You can optionally pass an argument with the service name to view logs for a specific service.

- ``just manage <command>``
  Runs Django management commands within the container. Replace ``<command>`` with any valid Django management command, such as ``migrate``, ``createsuperuser``, or ``shell``.
