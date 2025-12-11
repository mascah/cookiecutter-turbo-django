The Modular Monolith
====================

This page explains the core architectural philosophy behind this template.

What is a Modular Monolith?
---------------------------

A modular monolith is an architectural approach that combines the deployment simplicity of a monolith with the organizational benefits of well defined modules.

ThoughtWorks calls it:

    "A set of modules with specific functionality, which can be independently developed and tested, while the entire application is deployed as a single unit."

Definition and Key Characteristics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A modular monolith is:

- A **single deployable unit** that can be built, tested, and deployed as one artifact
- Organized into **domain modules** with clear boundaries and responsibilities
- Built with **explicit interfaces** between modules rather than implicit dependencies
- Designed so modules can be **independently developed and tested** even though they deploy together

Single Deployable Unit, Multiple Domain Modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You ship one application, but internally it's organized by business domain:

- Users and authentication
- Billing and subscriptions
- Core product features
- Notifications and messaging

Each domain is a module with its own models, services, and APIs.

Clear Boundaries, Shared Infrastructure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modules share infrastructure (database connections, caching, web server) but maintain clear boundaries in business logic. Cross-cutting concerns like authentication, logging, and error handling are handled at the infrastructure level.

Why Not Microservices (Yet)?
----------------------------

Microservices are powerful for large organizations with mature platform teams. For most teams, they're premature.

Distributed Computing Complexity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

DHH emphasizes in `The Majestic Monolith`_ that distribution should be avoided unless absolutely necessary:

    "If you can keep it all in one app, you have a much better chance of keeping it all in your head too."

Microservices introduce distributed computing challenges:

- Network failures between services
- Data consistency across service boundaries
- Complex deployment orchestration
- Service discovery and load balancing

These aren't insurmountable, but they require investment in tooling and expertise.

Operational Overhead
^^^^^^^^^^^^^^^^^^^^

Running microservices means:

- Multiple deployment pipelines
- Distributed logging and tracing
- Cross-service debugging
- Version compatibility management

A small team managing a dozen services spends more time on operations than features. DHH notes that Basecamp's small team serves millions of users without microservices.

When Microservices Make Sense
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ThoughtWorks identifies when microservices become valuable:

- Different parts of your system need to **scale independently**
- Teams are large enough to **own separate services**
- You need **different technology stacks** for different problems
- Your **domain boundaries are well understood** and stable

The modular monolith lets you discover these boundaries before committing to distribution.

Why Not a Traditional Monolith?
-------------------------------

A traditional monolith without internal structure creates its own problems.

Spaghetti Dependencies
^^^^^^^^^^^^^^^^^^^^^^

Dan Manges describes the danger at Root Insurance in `The Modular Monolith: Rails Architecture`_:

    "We've heard of teams ending up with a Distributed Monolith: code in independent services that is as difficult to work with as a Monolith. One underlying cause of that is poor architecture."

Without clear boundaries, code depends on code arbitrarily. A change in the billing module breaks authentication because someone took a shortcut. The dependency graph becomes a tangled mess.

Difficulty Onboarding New Developers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

New team members can't understand a slice of the system—they have to understand everything to change anything. Onboarding takes weeks, and developers are afraid to make changes.

Scaling Team Becomes Scaling Problems
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Adding developers doesn't increase velocity because everyone is stepping on each other. Merge conflicts are constant. Coordination overhead dominates.

The Best of Both Worlds
-----------------------

The modular monolith gives you the best of both approaches.

Modularity Without Distribution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You get clear boundaries and separation of concerns without the operational complexity of distributed systems. Modules communicate through well-defined interfaces, but those calls are in-process, not over the network.

In practice, this means using an **in-memory event bus**: modules publish domain events when significant things happen, and other modules subscribe to react. The event bus is a simple pub-sub mechanism that routes events to registered handlers, all within the same process.

ThoughtWorks notes the modular monolith is "significantly easier to design, deploy and manage" because modules ship together with optimized inter module communication.

The same event contracts that work in-memory can later be routed through RabbitMQ, AWS SNS, or other message brokers when you need independent scaling or service extraction. Your handlers stay the same. Only the transport changes.

Strong Boundaries Enable Future Extraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Manges emphasizes this at Root:

    "Our goal was to identify good architectural boundaries before they extracted code out into independent services. This would set them up to be able to migrate to microservices in the future."

When you do need to extract a service (because it needs independent scaling, or a separate team will own it), you have a clean seam. The module already has a defined interface. Extraction is straightforward, not a multi-month rewrite.

Grow Your Architecture With Your Team
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Start simple. Add modules as your domain expands. Extract services when the organizational or technical need is clear. Your architecture evolves with your business rather than constraining it.

As Manges summarizes:

    "The Modular Monolith is simple in its concepts, but powerful in enabling us to scale our team and software."

Further Reading
---------------

- `The Majestic Monolith`_ — DHH on why small teams should embrace monoliths
- `The Modular Monolith: Rails Architecture`_ — Dan Manges on structuring code by domain at Root Insurance
- `Modular Monolith: A Better Way to Build Software`_ — ThoughtWorks on the modular monolith as a middle ground

.. _The Majestic Monolith: https://signalvnoise.com/svn3/the-majestic-monolith/
.. _The Modular Monolith\: Rails Architecture: https://medium.com/@dan_manges/the-modular-monolith-rails-architecture-fb1023826fc4
.. _Modular Monolith\: A Better Way to Build Software: https://www.thoughtworks.com/en-us/insights/blog/microservices/modular-monolith-better-way-build-software
