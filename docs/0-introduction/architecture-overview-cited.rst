Architecture Overview
=====================

This page connects the modular monolith philosophy to the concrete structure of generated projects.

Project Structure
-----------------

A generated project follows this high-level structure:

.. code-block:: text

    my_project/
    ├── apps/                    # Frontend applications (Turborepo workspaces)
    │   ├── landing/             # Astro static site
    │   └── my_project/          # Vite + React SPA
    ├── packages/                # Shared frontend packages
    │   ├── ui/                  # Shared React components
    │   ├── eslint-config/       # Shared ESLint config
    │   └── typescript-config/   # Shared TypeScript configs
    ├── config/                  # Django settings and configuration
    │   └── settings/            # Environment-specific settings
    ├── my_project/              # Django modular monolith container
    │   ├── users/               # User domain module
    │   └── [your modules]/      # Add domain modules here
    └── docker/                  # Docker configurations

The Modular Monolith Container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``{project_slug}/`` directory is the heart of the modular monolith. Each subdirectory is a Django app representing a domain module:

.. code-block:: text

    my_project/
    ├── users/           # User management, authentication
    ├── billing/         # Payments, subscriptions (you add this)
    ├── notifications/   # Email, push notifications (you add this)
    └── core/            # Core product domain (you add this)

Add new modules as sibling directories to ``users/``.

This structure follows what Dan Manges describes in `The Modular Monolith: Rails Architecture`_:

    "Our code is structured by domain concept, which especially helps new team members navigate and understand the project."

Django Apps as Domain Modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each module is a standard Django app with:

- ``models.py`` - Domain models
- ``views.py`` or ``api/`` - HTTP interfaces
- ``services.py`` - Business logic (recommended, see :doc:`/4-guides/service-layer-patterns`)
- ``tests/`` - Module-specific tests

Modules should be cohesive—everything related to a domain concept lives together.

Shared Infrastructure
^^^^^^^^^^^^^^^^^^^^^

Cross-cutting concerns live outside the domain modules:

- ``config/settings/`` - Django configuration
- ``docker/`` - Container definitions
- ``packages/`` - Shared frontend code

This separation reflects DHH's observation in `The Majestic Monolith`_ that a well-structured monolith lets developers "keep it all in their head."

Domain Boundaries
-----------------

How Modules Communicate
^^^^^^^^^^^^^^^^^^^^^^^

Modules should communicate through explicit interfaces, not by reaching into each other's internals. The primary mechanism is **domain events**—an in-memory pub-sub system where modules publish events when significant things happen, and other modules subscribe to react.

The pattern works like this:

.. code-block:: python

    # Publishing an event (in a service)
    def _publish_event():
        event = OrderPlacedEvent(order_uuid=str(order.uuid), ...)
        event_bus.publish(event)

    transaction.on_commit(_publish_event)  # Only publish after commit!

The critical detail is ``transaction.on_commit()``—events are only published after the database transaction commits successfully. This prevents handlers from processing events for data that might roll back.

Handlers are registered during app startup in ``AppConfig.ready()``, ensuring loose coupling between modules:

.. code-block:: python

    # In orders/apps.py
    def ready(self):
        from {project_slug}.domain_events.bus import event_bus
        from {project_slug}.domain_events.events import PrescriptionRequestApprovedEvent
        from {project_slug}.orders.handlers import handle_prescription_approved

        event_bus.subscribe(PrescriptionRequestApprovedEvent, handle_prescription_approved)

This approach provides:

- **Decoupling**: Publishers don't know about subscribers
- **Testability**: Modules can be tested in isolation
- **Scalability path**: Swap the in-memory bus for RabbitMQ/SNS when needed

For simple model lifecycle hooks within a single module, Django signals remain appropriate. Domain events are preferred for cross module communication.

See :doc:`/4-guides/event-driven-architecture` for comprehensive implementation details, code examples, and guidance on when to use signals vs events.

Manges describes the benefit:

    "The boundary between stateful and stateless logic helps them think about implementing some of their most complex business logic in pure Ruby [Python], completely separated from Rails [Django]."

**Avoid:**

- Importing models directly from other modules
- Accessing other modules' internal functions
- Shared mutable state

**Enforcing boundaries:**

Conventions aren't enough—boundaries erode without tooling. For enforcement strategies including import-linter contracts, architectural tests, and the no-FK database pattern, see :doc:`/4-guides/module-boundary-enforcement`.

What Belongs in a Module
^^^^^^^^^^^^^^^^^^^^^^^^

A module should contain everything needed to fulfill its domain responsibility:

- Models representing domain entities
- Business logic operating on those entities
- APIs exposing functionality to other modules or external clients
- Tests validating the module's behavior

Cross-Cutting Concerns
^^^^^^^^^^^^^^^^^^^^^^

Some concerns span modules:

- **Authentication/Authorization** - Handled at middleware/decorator level
- **Logging** - Configured at infrastructure level, used everywhere
- **Error Handling** - Consistent patterns, centralized reporting

These live in shared infrastructure, not duplicated in each module.

Scaling Pathways
----------------

Adding New Modules
^^^^^^^^^^^^^^^^^^

When your domain expands, add a new module:

1. Create a new directory under ``{project_slug}/``
2. Structure it as a Django app
3. Register it in ``INSTALLED_APPS``
4. Define its public interface (services, APIs)
5. Keep dependencies explicit

ThoughtWorks notes that with a modular monolith, teams can "make changes across services efficiently; it doesn't take 5 PRs across 5 projects with deployment order dependencies to implement a feature."

Extracting Modules to Services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a module needs independent scaling or team ownership:

1. The module already has a defined interface
2. Create a new service with that interface
3. Replace in process calls with network calls
4. Deploy independently

This is straightforward because boundaries are already clear. As Manges notes, Root "decided to first focus on making their app modular" before extracting services, which "set them up to be able to migrate to microservices in the future."

Horizontal Scaling the Monolith
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before extracting services, consider scaling the monolith:

- Multiple application instances behind a load balancer
- Database read replicas
- Caching layers
- Background job workers (Celery)

A well structured monolith can handle significant scale.

Further Reading
---------------

- `The Majestic Monolith`_ — DHH on why small teams should embrace monoliths
- `The Modular Monolith: Rails Architecture`_ — Dan Manges on structuring code by domain at Root Insurance
- `Modular Monolith: A Better Way to Build Software`_ — ThoughtWorks on the modular monolith as a middle ground

.. _The Majestic Monolith: https://signalvnoise.com/svn3/the-majestic-monolith/
.. _The Modular Monolith\: Rails Architecture: https://medium.com/@dan_manges/the-modular-monolith-rails-architecture-fb1023826fc4
.. _Modular Monolith\: A Better Way to Build Software: https://www.thoughtworks.com/en-us/insights/blog/microservices/modular-monolith-better-way-build-software
