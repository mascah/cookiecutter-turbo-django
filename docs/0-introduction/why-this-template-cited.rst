Why This Template?
==================

There are many ways to build great software. Rails is fantastic. So is Django. The "majestic monolith" pattern works in any number of frameworks.

This template exists because I use Python a lot, and I've seen the modular monolith pattern work firsthand at startups that scaled from early stage to acquisition in one case and IPO in the other. It's a proven approach, and
I wanted a solid starting point I could reference and share.

It's also the foundation I reach for when it fits the need for freelance work, personal side projects and experimenting with new ideas. Making it a template makes my own life a little easier at the very least.

The Problem with Platform Architecture
--------------------------------------

Building software platforms that scale from a handful of developers to dozens, and from thousands of users to millions is hard. Most teams make one of two common mistakes early on:

Premature Microservices Complexity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Teams adopt microservices before they need them, inheriting all the operational complexity of distributed systems without the organizational scale to manage it. As DHH articulates in `The Majestic Monolith`_:

    "The patterns that make sense for organizations orders of magnitude larger than yours, are often the exact opposite ones that'll make sense for you."

Network failures, deployment choreography, data consistency across services—these challenges require dedicated infrastructure and platform teams that startups don't have.

Monoliths That Become Unmaintainable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Other teams start with a traditional monolith but without clear internal boundaries. Dan Manges, CTO of Root Insurance, describes the consequence in `The Modular Monolith: Rails Architecture`_:

    "If your application's dependency graph looks like spaghetti, understanding the impact of changes is difficult."

As the codebase grows, dependencies become tangled, changes in one area break others, and onboarding new developers takes weeks instead of days. The monolith becomes a liability—what some call a "Distributed Monolith" even before any services are extracted.

The Middle Path
^^^^^^^^^^^^^^^

There's a better approach: start with a **modular monolith**. ThoughtWorks describes this as `a better way to build software`_:

    "A set of modules with specific functionality, which can be independently developed and tested, while the entire application is deployed as a single unit."

You get the operational simplicity of a single deployable unit with the organizational clarity of well defined domain boundaries. When (and if) you need to extract services, you have clean seams to work with.

What This Template Provides
---------------------------

Production ready foundation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This template provides a production ready Django + Turborepo monorepo with:

- Django backend with sensible defaults
- Modern frontend workspaces (React, Astro)
- Docker based development and deployment
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

As Manges describes the benefit at Root:

    "Our code is structured by domain concept, which especially helps new team members navigate and understand the project."

Team Scalability
^^^^^^^^^^^^^^^^

The architecture scales not just technically (more requests, more data) but organizationally:

- New developers can understand and contribute to a single module without grasping the entire system
- Teams can own modules with clear interfaces
- Changes are localized, reducing coordination overhead
- The codebase remains navigable as it grows

DHH's Basecamp team demonstrates this works: 12 developers serving millions of users across six platforms with a majestic monolith.

Further Reading
---------------

- `The Majestic Monolith`_ — DHH on why small teams should embrace monoliths
- `The Modular Monolith: Rails Architecture`_ — Dan Manges on structuring code by domain at Root Insurance
- `Modular Monolith: A Better Way to Build Software`_ — ThoughtWorks on the modular monolith as a middle ground

.. _The Majestic Monolith: https://signalvnoise.com/svn3/the-majestic-monolith/
.. _The Modular Monolith\: Rails Architecture: https://medium.com/@dan_manges/the-modular-monolith-rails-architecture-fb1023826fc4
.. _a better way to build software: https://www.thoughtworks.com/en-us/insights/blog/microservices/modular-monolith-better-way-build-software
.. _Modular Monolith\: A Better Way to Build Software: https://www.thoughtworks.com/en-us/insights/blog/microservices/modular-monolith-better-way-build-software
