Event-Driven Architecture
=========================

Use domain events to decouple modules in your modular monolith. Modules publish events when something significant happens, and other modules subscribe to react.

Overview
--------

In a modular monolith, modules need to communicate without creating tight dependencies. Direct imports between modules lead to the "spaghetti dependencies" that make monoliths unmaintainable.

The solution: modules publish events when something happens, and other modules subscribe to react. This provides:

- **Decoupling**: Publishers don't know about subscribers
- **Testability**: Modules can be tested in isolation
- **Scalability path**: The same event contracts work with in-memory or external brokers

The Event Bus
-------------

At the heart of the system is a simple in-memory event bus that routes events to registered handlers.

.. code-block:: python

    # {project_slug}/domain_events/bus.py
    from collections import defaultdict

    class EventBus:
        """A simple in-memory pub-sub mechanism for domain events."""

        def __init__(self):
            self._subscribers = defaultdict(list)

        def subscribe(self, event_type, handler):
            """Register a handler for a given event type."""
            self._subscribers[event_type].append(handler)

        def publish(self, event):
            """Publish an event to all registered handlers."""
            event_type = type(event)
            for handler in self._subscribers.get(event_type, []):
                handler(event)

    # Module-level singleton
    event_bus = EventBus()

The event bus is instantiated once at module load time. All modules import the same ``event_bus`` singleton, ensuring a single registry of subscribers across the application.

Defining Events
---------------

Events are simple data classes that represent something that happened in your domain. They inherit from a marker base class:

.. code-block:: python

    # {project_slug}/domain_events/base.py
    from abc import ABC

    class DomainEvent(ABC):
        """Base class for all domain events."""
        pass

Concrete events store the data needed by handlers:

.. code-block:: python

    # {project_slug}/domain_events/events.py
    from {project_slug}.domain_events.base import DomainEvent

    class OrderPlacedEvent(DomainEvent):
        """Emitted when a new order is placed."""

        def __init__(
            self,
            order_uuid: str,
            user_id: int,
            product_dict: list[dict],
            fulfillment_state: str,
        ):
            self.order_uuid = order_uuid
            self.user_id = user_id
            self.product_dict = product_dict
            self.fulfillment_state = fulfillment_state


    class PrescriptionRequestApprovedEvent(DomainEvent):
        """Emitted when a provider approves a prescription request."""

        def __init__(
            self,
            prescription_request_id: int,
            prescription_id: int,
            encounter_id: int,
            order_uuid: str,
            order_item_uuid: str,
        ):
            self.prescription_request_id = prescription_request_id
            self.prescription_id = prescription_id
            self.encounter_id = encounter_id
            self.order_uuid = order_uuid
            self.order_item_uuid = order_item_uuid

**Naming conventions:**

- Use past tense: ``OrderPlacedEvent``, not ``PlaceOrderEvent``
- Include the domain context: ``PrescriptionRequestApprovedEvent``
- Be specific about what happened

**What data to include:**

- IDs and UUIDs needed to look up related entities
- Key state that handlers need without additional queries
- Avoid including full model instances (they may be stale)

Registering Handlers
--------------------

Handlers are registered during Django's app initialization using ``AppConfig.ready()``. This ensures registration happens after all apps are loaded, avoiding circular import issues.

.. code-block:: python

    # {project_slug}/orders/apps.py
    from django.apps import AppConfig

    class OrdersConfig(AppConfig):
        name = "{project_slug}.orders"
        verbose_name = "Orders"

        def ready(self) -> None:
            """Register event handlers when the app is ready."""
            # Lazy imports to avoid circular dependencies
            from {project_slug}.domain_events.bus import event_bus
            from {project_slug}.domain_events.events import (
                PrescriptionRequestApprovedEvent,
                PrescriptionRequestRejectedEvent,
                EncounterCompletedEvent,
            )
            from {project_slug}.orders.handlers import (
                handle_prescription_request_approved,
                handle_prescription_request_rejected,
                handle_encounter_completed,
            )

            # Register handlers
            event_bus.subscribe(
                PrescriptionRequestApprovedEvent,
                handle_prescription_request_approved,
            )
            event_bus.subscribe(
                PrescriptionRequestRejectedEvent,
                handle_prescription_request_rejected,
            )
            event_bus.subscribe(
                EncounterCompletedEvent,
                handle_encounter_completed,
            )

**Key points:**

- Use lazy imports inside ``ready()`` to avoid circular dependencies
- Handlers can be functions or class methods
- Multiple handlers can subscribe to the same event type

Handler Implementation
^^^^^^^^^^^^^^^^^^^^^^

Handlers receive the event and perform their logic:

.. code-block:: python

    # {project_slug}/orders/handlers.py
    import logging
    from django.db import transaction
    from {project_slug}.domain_events.events import PrescriptionRequestApprovedEvent
    from {project_slug}.orders.models import Order, OrderItem, OrderStatus

    logger = logging.getLogger(__name__)

    def handle_prescription_request_approved(event: PrescriptionRequestApprovedEvent) -> None:
        """Update order item status when a prescription is approved."""
        with transaction.atomic():
            try:
                order_item = OrderItem.objects.select_related("order").get(
                    uuid=event.order_item_uuid
                )
                order_item.status = "clinically_approved"
                order_item.save()

                # Check if all items are approved
                order = order_item.order
                if order.all_items_approved():
                    order.status = OrderStatus.READY_FOR_FULFILLMENT
                    order.save()

                    # Emit next event in the chain
                    def _publish():
                        emit_order_ready_for_fulfillment(order)
                    transaction.on_commit(_publish)

            except OrderItem.DoesNotExist:
                logger.exception(
                    "OrderItem not found for uuid=%s",
                    event.order_item_uuid,
                )

Publishing Events Safely
------------------------

**Always publish events after the transaction commits.**

If you publish before commit and the transaction rolls back, handlers will process an event for data that doesn't exist.

The solution is Django's ``transaction.on_commit()``:

.. code-block:: python

    # {project_slug}/ehr/services/prescriptions.py
    from django.db import transaction
    from {project_slug}.domain_events.bus import event_bus
    from {project_slug}.domain_events.events import PrescriptionRequestApprovedEvent

    class PrescriptionService:

        @classmethod
        @transaction.atomic
        def approve_request(
            cls,
            request_id: int,
            provider: "Provider",
            sig: str,
            refills: int = 0,
        ) -> Prescription:
            """Approve a prescription request and create a prescription."""
            request = PrescriptionRequest.objects.select_related(
                "encounter", "product"
            ).get(id=request_id)

            # Validate and create the prescription
            request.validate_can_modify(provider)
            prescription = Prescription.objects.create(
                patient=request.encounter.patient,
                provider=provider,
                # ... other fields
            )
            request.mark_as_approved(prescription)

            # Queue async task for external service
            create_erx_prescription.delay(prescription.id)

            # CRITICAL: Publish event ONLY after transaction commits
            def _publish_event():
                event = PrescriptionRequestApprovedEvent(
                    prescription_request_id=request.id,
                    prescription_id=prescription.id,
                    encounter_id=request.encounter.id,
                    order_uuid=str(request.encounter.order_uuid),
                    order_item_uuid=str(request.order_item_uuid),
                )
                event_bus.publish(event)

            transaction.on_commit(_publish_event)

            return prescription

The inner function ``_publish_event()`` captures local variables at definition time, so they're still available when ``on_commit()`` calls it later.

**What happens:**

1. Database changes are made within the ``@transaction.atomic`` block
2. ``transaction.on_commit(_publish_event)`` registers the callback
3. When the transaction commits successfully, Django calls ``_publish_event()``
4. The event is published and handlers execute
5. If the transaction rolls back, the callback is never called

**Without this pattern**, you risk:

- Handlers processing events for rolled-back data
- Race conditions where handlers query before data is visible
- Inconsistent state across modules

Integrating with Celery
-----------------------

The event-driven architecture integrates naturally with Celery for async work.

Queuing Tasks from Services
^^^^^^^^^^^^^^^^^^^^^^^^^^^

For external service calls that shouldn't block the request:

.. code-block:: python

    @classmethod
    @transaction.atomic
    def approve_request(cls, request_id: int, provider: "Provider", ...) -> Prescription:
        # ... create prescription ...

        # Queue async task (runs independently of event handlers)
        create_erx_prescription.delay(prescription.id)

        # Publish event for other modules
        def _publish_event():
            event = PrescriptionRequestApprovedEvent(...)
            event_bus.publish(event)
        transaction.on_commit(_publish_event)

        return prescription

Queuing Tasks from Event Handlers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Handlers can also queue Celery tasks for work that should happen asynchronously:

.. code-block:: python

    def handle_order_ready_for_fulfillment(event: OrderReadyForFulfillmentEvent) -> None:
        """Queue async task to process fulfillment."""
        process_fulfillment.delay(event.order_uuid)

When to Use Sync Events vs Async Tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Use synchronous events when:**

- The work is fast and doesn't call external services
- You need the result before responding to the request
- Failure should fail the whole operation

**Use Celery tasks when:**

- Calling external APIs (payment, email, third-party services)
- Processing that takes more than a few hundred milliseconds
- Work that can be retried independently
- You need to handle rate limits or backoff

Django Signals vs Domain Events
-------------------------------

Django provides built-in signals (``pre_save``, ``post_save``, etc.). When should you use them vs domain events?

When to Use Django Signals
^^^^^^^^^^^^^^^^^^^^^^^^^^

Django signals are appropriate for:

- **Model lifecycle hooks**: Auditing changes, updating timestamps
- **Single-model concerns**: Clearing caches when a model changes
- **Framework integrations**: Third-party packages that need to react to saves

.. code-block:: python

    from django.db.models.signals import post_save
    from django.dispatch import receiver

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

When to Use Domain Events
^^^^^^^^^^^^^^^^^^^^^^^^^

Domain events are preferred for:

- **Cross-module communication**: When the Orders module needs to know about EHR events
- **Business domain concepts**: Events that represent meaningful domain occurrences
- **Explicit contracts**: When you want clear, documented interfaces between modules
- **Future extraction**: When you might extract a module to a separate service

.. code-block:: python

    # Domain event - explicit, cross-module communication
    event_bus.publish(OrderPlacedEvent(
        order_uuid=str(order.uuid),
        user_id=order.user.id,
        # ... explicit contract
    ))

**Key differences:**

+------------------------+------------------+---------------------------+
| Aspect                 | Django Signals   | Domain Events             |
+========================+==================+===========================+
| Coupling               | Model-level      | Domain-level              |
+------------------------+------------------+---------------------------+
| Scope                  | Within Django    | Cross-module              |
+------------------------+------------------+---------------------------+
| Contract               | Implicit         | Explicit event classes    |
+------------------------+------------------+---------------------------+
| Extractability         | Hard             | Easy (change transport)   |
+------------------------+------------------+---------------------------+
| When fires             | Every save       | When you publish          |
+------------------------+------------------+---------------------------+

**Guidance:** Use Django signals for model-level concerns within a single module. Use domain events for anything that crosses module boundaries or represents a business domain concept.

Scaling the Event Bus
---------------------

The in-memory event bus handles most applications, even those with significant traffic. When you need to scale beyond a single process, you can swap in an external broker.

When In-Memory Works
^^^^^^^^^^^^^^^^^^^^

The in-memory bus is appropriate when:

- Your application runs as a single process (or multiple identical processes)
- Event handlers are fast and don't need independent scaling
- You don't need event persistence or replay

When to Consider External Brokers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider moving to RabbitMQ, AWS SNS/SQS, or similar when:

- You need to scale event consumers independently
- Events should persist if the application restarts
- You're extracting a module to a separate service
- You need guaranteed delivery with acknowledgment

Migration Path
^^^^^^^^^^^^^^

Because your events are explicit classes with clear contracts, migration is straightforward:

1. **Define an abstract interface** for the event bus
2. **Create a new implementation** that publishes to RabbitMQ/SNS
3. **Swap the implementation** via configuration
4. **Event classes remain unchanged** - they're just serialized differently

.. code-block:: python

    # Future: Abstract interface
    class BaseEventBus(ABC):
        @abstractmethod
        def subscribe(self, event_type, handler): pass

        @abstractmethod
        def publish(self, event): pass

    # Future: Settings-based selection
    # EVENT_BUS_BACKEND = "myproject.events.backends.RabbitMQEventBus"

Your **event contracts and handler logic stay the same**. Only the transport changes. Build with clear boundaries from day one, and extraction becomes straightforward.

Event Sourcing (and Why We Don't Use It)
----------------------------------------

When developers hear "event-driven architecture," many think of **event sourcing**. Here's what it actually is and why you probably don't need it.

What Event Sourcing Actually Is
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Event sourcing is a fundamentally different way of storing data:

- **Traditional approach**: Store current state. An ``Order`` table has columns for ``status``, ``total``, ``updated_at``. When state changes, you update the row.
- **Event sourcing**: Store events as the source of truth. Instead of an ``Order`` row, you store ``OrderPlaced``, ``ItemAdded``, ``PaymentReceived``, ``OrderShipped``. Current state is derived by replaying events.

.. code-block:: python

    # Traditional: Store current state
    order.status = "shipped"
    order.save()

    # Event sourcing: Append event, derive state
    event_store.append(OrderShippedEvent(order_id=order.id, shipped_at=now))
    # Current state = replay all events for this order

In event sourcing, **events are the database**. You don't have a separate ``Order`` table. You reconstruct order state by replaying its event stream.

What We're Doing Is Different
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The event-driven architecture in this guide is **not** event sourcing. We use events for **communication between modules**, not as the source of truth:

+---------------------------+----------------------------------+----------------------------------+
| Aspect                    | Event-Driven (This Guide)        | Event Sourcing                   |
+===========================+==================================+==================================+
| Source of truth           | Database tables (Django models)  | Event log                        |
+---------------------------+----------------------------------+----------------------------------+
| Events are                | Notifications after state change | The state changes themselves     |
+---------------------------+----------------------------------+----------------------------------+
| State reconstruction      | Query the database               | Replay event stream              |
+---------------------------+----------------------------------+----------------------------------+
| Can delete events?        | Yes (they're just notifications) | No (you'd lose history)          |
+---------------------------+----------------------------------+----------------------------------+
| Complexity                | Low to moderate                  | High                             |
+---------------------------+----------------------------------+----------------------------------+

With our approach:

1. You update the database (``prescription.status = "approved"``)
2. You publish an event to notify other modules (``PrescriptionRequestApprovedEvent``)
3. The database remains the source of truth

You get decoupling without the complexity of event sourcing.

Why Event Sourcing Is Often Misunderstood
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common misconceptions:

**"We're doing event sourcing because we publish events"**

Publishing events doesn't make you event-sourced. If your database tables are the source of truth and events are notifications, that's event-driven architecture—and that's probably what you want.

**"Event sourcing gives us an audit log"**

You can have a complete audit log without event sourcing. Store audit records alongside your regular data. Event sourcing is about deriving state from events, not about having history.

**"Event sourcing is more scalable"**

Event sourcing introduces significant complexity: event versioning, snapshot management, eventual consistency, complex queries (you can't just ``SELECT * FROM orders WHERE status = 'pending'``). For most applications, a well-indexed relational database scales better with far less complexity.

**"We might need to replay events someday"**

If you need to rebuild a read model or audit history, you can implement that specifically. You don't need to restructure your entire data model around event streams.

When Event Sourcing Actually Makes Sense
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Event sourcing is valuable in specific scenarios:

- **Audit-critical domains**: Financial systems, healthcare records, legal documents where you must prove exactly what happened and when
- **Complex domain logic**: When business rules depend heavily on the sequence of events, not just current state
- **Time-travel requirements**: Systems that need to answer "what was the state at time X?" frequently
- **Event-native domains**: Systems where events are the natural model (trading systems, IoT sensor streams)

Even then, consider applying event sourcing to **specific aggregates**, not your entire system.

The Complexity You're Signing Up For
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you choose event sourcing, be prepared for:

- **Event versioning**: What happens when ``OrderPlacedEvent`` v1 needs a new field? You need migration strategies.
- **Snapshots**: Replaying thousands of events is slow. You'll need snapshot strategies.
- **Querying**: "Show me all pending orders" requires either a read model (CQRS) or scanning event streams.
- **Eventual consistency**: Read models lag behind writes. Your UI must handle this.
- **Tooling**: Django's ORM doesn't support this pattern. You'll need specialized libraries or custom infrastructure.

What to Do Instead
^^^^^^^^^^^^^^^^^^

If someone says "I want event sourcing," ask what problem they're actually solving:

**"I need an audit trail"**
    Add an audit log table. Store who changed what and when. Django packages like ``django-auditlog`` or ``django-simple-history`` do this trivially.

**"I need to notify other systems when things change"**
    That's event-driven architecture—exactly what this guide covers. Publish domain events, let other modules react.

**"I need to rebuild read models"**
    Store events in an append-only log alongside your regular data. Replay when needed. You don't need full event sourcing.

**"I need to know the state at a point in time"**
    Add ``created_at``, ``updated_at``, and consider temporal tables or a history table pattern.

**"I've read that event sourcing is best practice"**
    It's a tool for specific problems. Most successful systems use traditional state-based persistence with event-driven communication between components.

If You Ever Need Event Sourcing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The patterns here position you well:

1. Your **domain events are already explicit classes** with clear contracts
2. Your **modules are decoupled** and communicate via events
3. You can **introduce event sourcing to specific aggregates** without rewriting everything

Start with event-driven architecture. Add event sourcing to specific aggregates only when the problem demands it.

Summary
-------

1. **Event Bus Singleton**: Single registry of subscribers, imported everywhere
2. **Events as Data Classes**: Simple classes representing domain occurrences
3. **Register in AppConfig.ready()**: Lazy imports, wired at startup
4. **Publish with transaction.on_commit()**: Never publish before data is committed
5. **Integrate with Celery**: Async tasks for external services and slow work
6. **Domain Events > Django Signals**: For cross-module communication
7. **Scalability Path**: Same contracts work with external brokers when needed
