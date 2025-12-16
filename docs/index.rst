.. platform-django-template documentation master file.

Welcome to Platform Django
==========================

A project template for building **modular monolith** Django applications with modern frontend tooling.

This template establishes architectural patterns that work for small teams and large organizations. The modular monolith approach means deploying a single unit while keeping clear boundaries between domains.

**New here?** Start with :doc:`0-introduction/why-this-template` to understand the philosophy, or jump to :ref:`template-options` if you're ready to generate a project.

.. toctree::
   :maxdepth: 2
   :caption: Introduction

   0-introduction/why-this-template
   0-introduction/the-modular-monolith
   0-introduction/architecture-overview
   0-introduction/ui-architecture-philosophy

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   1-getting-started/project-generation-options
   1-getting-started/configuration
   1-getting-started/settings

.. toctree::
   :maxdepth: 2
   :caption: Local Development

   2-local-development/developing-locally-docker

.. toctree::
   :maxdepth: 2
   :caption: Deployment

   3-deployment/deployment-on-heroku
   3-deployment/deployment-on-aws

.. toctree::
   :maxdepth: 2
   :caption: Guides

   4-guides/adding-modules
   4-guides/django-admin-operator-panel
   4-guides/authentication
   4-guides/module-boundary-enforcement
   4-guides/service-layer-patterns
   4-guides/api-development
   4-guides/type-safe-api-integration
   4-guides/event-driven-architecture
   4-guides/production-patterns
   4-guides/observability-logging
   4-guides/model-auditing-history
   4-guides/product-analytics
   4-guides/multi-tenancy-organizations
   4-guides/code-quality
   4-guides/testing
   4-guides/e2e-testing-playwright
   4-guides/data-ingestion-integration
   4-guides/document
   4-guides/websocket
   4-guides/langchain-langgraph-integration

.. toctree::
   :maxdepth: 2
   :caption: AI Development

   5-ai-development/claude-code

.. toctree::
   :maxdepth: 2
   :caption: About

   6-about/maintainer-guide
   6-about/roadmap
   6-about/rust-faq

Indices and tables
------------------

* :ref:`genindex`
* :ref:`search`

.. At some point it would be good to have a module index of the high level things we are doing. Then we can * :ref:`modindex` back in.
