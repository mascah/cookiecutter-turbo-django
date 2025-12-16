Adding Modules to the Modular Monolith
======================================

This guide explains how to add new modules (Django apps) to your modular monolith architecture. Each module represents a bounded domain context within your application.

Overview
--------

In the modular monolith pattern, your application is organized into **modules**: self-contained Django apps that encapsulate specific business domains. Unlike microservices, these modules run in the same process and share a database, but they maintain clear boundaries through explicit interfaces.

For background on why we use this architecture, see :doc:`/0-introduction/the-modular-monolith`.

Project Layout
--------------

This project uses the layout from "Two Scoops of Django" with a two-tier structure:

- **Top Level Repository Root** has config files, documentation, ``manage.py``, and more.
- **Second Level Django Project Root** (``{project_slug}/``) is where your modules live.
- **Second Level Configuration Root** (``config/``) holds settings and URL configurations.

The project layout looks something like this::

    <repository_root>/
    ├── config/
    │   ├── settings/
    │   │   ├── __init__.py
    │   │   ├── base.py
    │   │   ├── local.py
    │   │   └── production.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── {project_slug}/              # Modular monolith container
    │   ├── users/                   # User management module
    │   ├── core/                    # Shared utilities and base models
    │   ├── domain_events/           # Event bus infrastructure
    │   └── <your_new_module>/       # Add new modules here
    ├── manage.py
    ├── README.md
    └── ...

The ``{project_slug}/`` directory is the **modular monolith container**. Each subdirectory is a module (Django app) representing a distinct business domain.

Creating a New Module
---------------------

Follow these steps to add a new module:

#. **Create the app** using Django's ``startapp`` command, replacing ``<module_name>`` with your module name::

    docker compose -f docker-compose.local.yml run --rm django python manage.py startapp <module_name>

   Or from host (if using direnv)::

    python manage.py startapp <module_name>

#. **Move the app** to the Django Project Root to maintain the modular structure::

    mv <module_name> {project_slug}/

#. **Edit the app's apps.py** to update the module path. Change::

    name = '<module_name>'

   To::

    name = '{project_slug}.<module_name>'

#. **Register the module** by adding it to the ``LOCAL_APPS`` list in ``config/settings/base.py``::

    LOCAL_APPS = [
        "{project_slug}.users",
        "{project_slug}.core",
        "{project_slug}.domain_events",
        "{project_slug}.<module_name>",  # Add your new module
    ]

#. **Run migrations** if your module includes models::

    docker compose -f docker-compose.local.yml run --rm django python manage.py makemigrations
    docker compose -f docker-compose.local.yml run --rm django python manage.py migrate

Module Structure
----------------

A well-organized module typically contains::

    {project_slug}/<module_name>/
    ├── __init__.py
    ├── admin.py              # Django admin configuration
    ├── apps.py               # App configuration
    ├── models.py             # Domain models
    ├── services.py           # Business logic (optional)
    ├── managers.py           # Custom model managers (optional)
    ├── migrations/
    │   └── __init__.py
    ├── api/                  # API layer (if using DRF)
    │   ├── __init__.py
    │   ├── serializers.py
    │   └── views.py
    └── tests/
        ├── __init__.py
        ├── factories.py      # Test factories
        └── test_models.py

Best Practices
--------------

**Naming conventions:**

- Use lowercase, singular nouns for module names (e.g., ``billing``, ``notification``, ``inventory``)
- Keep names short but descriptive
- Avoid generic names like ``utils`` or ``helpers``—put shared code in ``core``

**When to create a new module:**

- The domain has its own distinct models and business rules
- The functionality could conceptually be developed by a separate team
- You want to enforce boundaries between areas of the codebase

**When to extend an existing module:**

- The new functionality is tightly coupled to existing models
- It's a minor extension of existing domain logic
- Creating a new module would require excessive cross-module dependencies

**Module communication:**

Modules should communicate through explicit interfaces rather than direct imports:

- Use **domain events** for loose coupling between modules (see :doc:`event-driven-architecture`)
- Import only from a module's public interface, not internal implementation details
- Avoid circular dependencies between modules

See Also
--------

- :doc:`/0-introduction/the-modular-monolith` — Philosophy behind the modular monolith
- :doc:`/0-introduction/architecture-overview` — Full architecture overview
- :doc:`event-driven-architecture` — Decoupling modules with domain events
- :doc:`multi-tenancy-organizations` — Example of adding an organizations module
