# Platform Django

[![Build Status](https://github.com/mascah/platform-django-template/actions/workflows/ci.yml/badge.svg)](https://github.com/mascah/platform-django-template/actions)
[![Documentation Status](https://readthedocs.org/projects/platform-django-template/badge/?version=latest)](https://platform-django-template.readthedocs.io/)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-green.svg)](https://www.djangoproject.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A [Copier](https://copier.readthedocs.io/) template for building production-ready **modular monolith** Django applications with modern frontend tooling. Get the operational simplicity of a single deployable unit with the organizational clarity of well-defined domain boundaries.

Heavily inspired by [cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django).

## Features

- **Modular monolith architecture** - Domain-driven Django apps with event-driven communication
- **Django 5.2 + Python 3.13** - Latest stable versions with uv for fast dependency management
- **Turborepo + pnpm workspaces** - React SPA and Astro landing page with shared UI components
- **Docker-first development** - PostgreSQL, Redis, and all services containerized
- **Production-ready defaults** - Sentry, structured logging, type checking with mypy
- **Optional integrations** - Django REST Framework with OpenAPI, Celery task queue, async/ASGI support, Heroku deployment
- **Template updates** - Copier can update existing projects to newer template versions

## Quick Start

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Generate your project using uvx (runs copier without installing)
uvx --with jinja2-time copier copy gh:mascah/platform-django-template my_project --trust

# Follow the prompts, then see your generated project's README
```

### Updating an Existing Project

One of Copier's key advantages is the ability to update existing projects:

```bash
cd my_project
uvx --with jinja2-time copier update --trust
```

## Documentation

Full documentation is available at **[platform-django-template.readthedocs.io](https://platform-django-template.readthedocs.io/)**

- [Why This Template?](https://platform-django-template.readthedocs.io/en/latest/0-introduction/why-this-template-cited.html) - The modular monolith philosophy
- [Project Generation Options](https://platform-django-template.readthedocs.io/en/latest/1-getting-started/project-generation-options.html) - All template configuration options
- [Local Development](https://platform-django-template.readthedocs.io/en/latest/2-local-development/developing-locally-docker.html) - Docker-based development workflow
- [Deployment](https://platform-django-template.readthedocs.io/en/latest/3-deployment/deployment-on-heroku.html) - Heroku and AWS deployment guides

## Generated Project Structure

```
my_project/
├── apps/                    # Frontend applications (Turborepo workspaces)
│   ├── landing/             # Astro static site
│   └── my_project/          # Vite + React SPA
├── packages/                # Shared frontend packages
│   ├── ui/                  # Shared React components (Radix UI)
│   ├── eslint-config/       # Shared ESLint config
│   └── typescript-config/   # Shared TypeScript configs
├── config/settings/         # Django settings (base, local, production, test)
├── my_project/              # Django modular monolith container
│   └── users/               # User domain module (add more modules here)
└── docker/                  # Docker configurations
```

## Template Options

| Option | Default | Description |
|--------|---------|-------------|
| `use_drf` | true | Django REST Framework with OpenAPI |
| `use_celery` | true | Celery + Redis task queue |
| `use_async` | false | ASGI support with Uvicorn |
| `use_sentry` | true | Sentry error tracking |
| `use_heroku` | false | Heroku deployment configuration |
| `username_type` | username | Authentication type (username or email) |

See [all options](https://platform-django-template.readthedocs.io/en/latest/1-getting-started/project-generation-options.html) in the documentation.

## Acknowledgments

This project builds upon the excellent work of [cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django) and extends it with a modular monolith architecture and modern frontend tooling.
