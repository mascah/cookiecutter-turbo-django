Why This Template?
==================

There are many ways to build great software. Rails is fantastic. So is Django. The "majestic monolith" pattern works in any number of frameworks.

This template exists because I use Python a lot, and I've seen the modular monolith pattern work firsthand at startups that scaled from early stage to acquisition in one case and IPO in the other. It's a proven approach, and I wanted a solid starting point I could reference and share.

It's also the foundation I reach for when it fits the need for freelance work, personal side projects and experimenting with new ideas. Making it a template makes my own life a little easier at the very least.

The Challenge of Platform Architecture
--------------------------------------

Building software platforms that scale from a handful of developers to dozens, and from thousands of users to millions, is hard. Two common patterns emerge when teams choose their architecture early on:

Starting with Distributed Services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Microservices solve real problems: independent scaling, technology flexibility, and team autonomy. But they come with operational overhead—network failures, deployment choreography, data consistency across services—that requires dedicated infrastructure and platform teams to manage well.

For organizations with mature platform engineering, this trade-off makes sense. For smaller teams, the overhead can slow you down more than it helps.

Monoliths Without Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Other teams start with a traditional monolith but without clear internal boundaries. As the codebase grows, dependencies become tangled, changes in one area break others, and onboarding new developers takes weeks instead of days. The monolith becomes a liability—what some call a "Distributed Monolith" even before any services are extracted.

The Middle Path
^^^^^^^^^^^^^^^

There's a better starting point for most teams: a **modular monolith**. You get a single deployable unit with clear domain boundaries. When you need to extract services later, you have clean seams to work with.

See :doc:`the-modular-monolith` for a deeper dive into this architectural approach.

What This Template Provides
---------------------------

Production-Ready Foundation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This template provides a production-ready Django + Turborepo monorepo with:

- Django backend with sensible defaults
- Modern frontend workspaces (React, Astro)
- Docker-based development and deployment
- CI/CD pipelines
- Testing infrastructure
- Observability (Sentry, logging)

Patterns That Scale
^^^^^^^^^^^^^^^^^^^

More importantly, the template establishes **architectural patterns** that scale:

- Modular Django apps as domain boundaries
- Event-driven communication between modules (in-memory bus that can grow to RabbitMQ/SNS)
- Shared infrastructure separate from business logic
- Clear conventions for adding new modules
- Pathways to extraction when you outgrow the monolith

Team Scalability
^^^^^^^^^^^^^^^^

The architecture scales not just technically (more requests, more data) but organizationally:

- New developers can understand and contribute to a single module without grasping the entire system
- Teams can own modules with clear interfaces
- Changes are localized, reducing coordination overhead
- The codebase remains navigable as it grows

DHH's Basecamp team demonstrates this: 12 developers serving millions of users across six platforms with a well-structured monolith.

Architectural Governance
^^^^^^^^^^^^^^^^^^^^^^^^

Good intentions aren't enough. Module boundaries erode without enforcement. The template documents patterns for maintaining integrity:

- **import-linter** analyzes your import graph and enforces contracts between modules
- **Architectural tests** with grimp catch violations in your test suite
- **Service layer patterns** make boundaries explicit in code

These tools transform "don't import from other modules" from a convention that developers may forget into a CI check that fails the build. See :doc:`/4-guides/module-boundary-enforcement` for implementation details.

Supporting Research
-------------------

This approach draws from several practitioners who've written about their experiences:

- **DHH (Basecamp)**: "The patterns that make sense for organizations orders of magnitude larger than yours, are often the exact opposite ones that'll make sense for you."
- **Dan Manges (Root Insurance)**: "If your application's dependency graph looks like spaghetti, understanding the impact of changes is difficult."

Further Reading
---------------

- `The Majestic Monolith`_ — DHH on why small teams should embrace monoliths
- `The Modular Monolith: Rails Architecture`_ — Dan Manges on structuring code by domain at Root Insurance
- `Modular Monolith: A Better Way to Build Software`_ — ThoughtWorks on the modular monolith as a middle ground

.. _The Majestic Monolith: https://signalvnoise.com/svn3/the-majestic-monolith/
.. _The Modular Monolith\: Rails Architecture: https://medium.com/@dan_manges/the-modular-monolith-rails-architecture-fb1023826fc4
.. _Modular Monolith\: A Better Way to Build Software: https://www.thoughtworks.com/en-us/insights/blog/microservices/modular-monolith-better-way-build-software
