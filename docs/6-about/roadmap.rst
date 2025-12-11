Roadmap: Features Documented But Not Yet Implemented
=====================================================

This page tracks advanced features and patterns that are documented in the guides but not yet implemented in the generated template. These represent opportunities for future template enhancements or manual additions to your project.

.. note::

    The guides provide complete implementation instructions for all these features. This page serves as a quick reference for what ships with the template versus what requires manual setup.

Module Boundary Enforcement
---------------------------

**import-linter configuration**
    Static analysis tool to enforce module boundaries. See :doc:`/4-guides/module-boundary-enforcement`.

    - ``.importlinter`` configuration file
    - CI integration for boundary checking
    - Independence, forbidden, and layers contracts

**grimp architectural tests**
    Programmatic pytest-based import graph analysis for custom architectural rules.

Production Patterns
-------------------

**django-pg-zero-downtime-migrations**
    PostgreSQL-specific migrations that respect table locks for zero-downtime deployments. See :doc:`/4-guides/production-patterns`.

**django-waffle feature flags**
    Feature flag library with percentage rollouts, user/group targeting, and A/B testing support.

**delay_on_commit() (Celery 5.4+)**
    Celery helper that ensures tasks are only enqueued after Django transactions commit.

Observability
-------------

**django-guid correlation IDs**
    Middleware for automatic correlation ID propagation across requests and event chains. See :doc:`/4-guides/observability-logging`.

**Dead Letter Queue pattern**
    Infrastructure for capturing and reprocessing failed events.

Testing
-------

**FakeEventBus test fixture**
    Test double for the event bus that captures published events without triggering handlers. See :doc:`/4-guides/testing`.

**Pydantic event contracts**
    Schema validation for domain events using Pydantic models with strict validation.

Type Safety
-----------

**oasdiff for breaking change detection**
    CI integration for detecting breaking API changes by diffing OpenAPI schemas. See :doc:`/4-guides/type-safe-api-integration`.

Developer Experience
--------------------

**Just (justfile)**
    Modern Makefile alternative with better UX for polyglot task running.

**cruft/copier for template updates**
    Tools for tracking template versions and applying upstream changes to generated projects.

Contributing
------------

If you implement any of these features in a way that could be generalized, consider contributing them back to the template. See the :doc:`maintainer-guide` for contribution guidelines.
