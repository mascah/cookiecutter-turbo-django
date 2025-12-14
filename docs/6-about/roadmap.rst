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

API Frameworks
--------------

**use_graphql template option**
    GraphQL support via graphene-django or strawberry-graphql as an alternative to REST. See :doc:`/4-guides/api-development`.

    - Schema generation and playground
    - Integration with service layer patterns
    - DataLoader configuration for N+1 prevention

**use_ninja template option**
    django-ninja as an alternative API framework for async-first applications.

    - FastAPI-style type-hint validation
    - Native async support
    - Pydantic schema integration

Developer Experience
--------------------

**Just (justfile)**
    Modern Makefile alternative with better UX for polyglot task running.

**cruft/copier for template updates**
    Tools for tracking template versions and applying upstream changes to generated projects.

Infrastructure as Code
----------------------

**Terraform/Terragrunt scaffolding**
    Pre-configured infrastructure templates for AWS deployment. See :doc:`/3-deployment/deployment-on-aws`.

    - ``infrastructure/`` directory with Terragrunt structure
    - VPC, RDS, ElastiCache, S3 module configurations
    - Environment hierarchy (dev/staging/production)
    - GitHub Actions workflow for ``terraform plan/apply``

**ECS deployment module**
    Terraform module for deploying Django + Celery on ECS Fargate.

    - ECS cluster, task definitions, services
    - ALB integration with health checks
    - Auto-scaling policies
    - Secrets Manager integration

**EKS deployment module**
    Terraform module for deploying on EKS with managed node groups.

    - EKS cluster with IRSA configuration
    - Kubernetes manifests or Kustomize overlays
    - AWS Load Balancer Controller integration

**Helm chart for Django app**
    Kubernetes Helm chart for the generated Django application.

    - Deployment, Service, Ingress templates
    - Celery worker and beat deployments
    - Values files for environment configuration
    - Integration with External Secrets Operator

**use_aws template option**
    Optional AWS infrastructure scaffolding during project generation.

    - Generates ``infrastructure/`` directory
    - Pre-configured for ECS or EKS based on selection
    - GitHub Actions CI/CD workflow for AWS deployment

Contributing
------------

If you implement any of these features in a way that could be generalized, consider contributing them back to the template. See the :doc:`maintainer-guide` for contribution guidelines.
