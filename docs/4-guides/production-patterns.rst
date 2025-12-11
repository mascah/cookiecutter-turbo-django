Production Patterns
===================

Patterns for running your modular monolith safely in production: zero-downtime migrations, feature flags for gradual rollouts, and Celery task patterns for reliability.

Zero-Downtime Migrations
------------------------

Standard Django migrations can lock tables during deployments, causing downtime. `django-pg-zero-downtime-migrations <https://github.com/tbicr/django-pg-zero-downtime-migrations>`_ applies migrations with PostgreSQL-aware locking strategies.

Installation
^^^^^^^^^^^^

.. code-block:: text

    # requirements/production.txt
    django-pg-zero-downtime-migrations==0.14

Configuration
^^^^^^^^^^^^^

Replace the default database backend in production settings:

.. code-block:: python

    # config/settings/production.py
    DATABASES = {
        "default": {
            "ENGINE": "django_zero_downtime_migrations.backends.postgres",
            # ... other settings
        }
    }

    # Fail migrations that could cause downtime
    ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE = True

With ``RAISE_FOR_UNSAFE=True``, migrations that would acquire exclusive locks on large tables will fail with an explanation of how to fix them.

Unsafe Operations
^^^^^^^^^^^^^^^^^

The following operations can cause downtime without the library:

**Adding a column with a default**

.. code-block:: python

    # UNSAFE - rewrites entire table in standard Django
    migrations.AddField(
        model_name="order",
        name="priority",
        field=models.IntegerField(default=0),
    )

The library handles this safely by adding a nullable column, setting the default at the database level, and then making it non-nullable.

**Adding an index**

.. code-block:: python

    # UNSAFE - locks table during index build
    migrations.AddIndex(
        model_name="order",
        index=models.Index(fields=["created_at"], name="order_created_idx"),
    )

The library creates indexes with ``CONCURRENTLY``, which doesn't block writes.

**Adding a NOT NULL constraint**

.. code-block:: python

    # UNSAFE - scans entire table
    migrations.AlterField(
        model_name="order",
        name="customer_id",
        field=models.IntegerField(),  # Was nullable, now NOT NULL
    )

The library adds a check constraint first (non-blocking), validates it, then converts to NOT NULL.

The Expand-Contract Pattern
^^^^^^^^^^^^^^^^^^^^^^^^^^^

For complex schema changes, use the expand-contract pattern:

1. **Expand**: Add new structure (backward compatible)
2. **Migrate**: Populate new structure with data
3. **Contract**: Remove old structure (after code no longer uses it)

Example: Renaming a column from ``customer_id`` to ``user_id``:

**Step 1: Expand** (deploy new column alongside old)

.. code-block:: python

    # Migration 1: Add new column
    class Migration(migrations.Migration):
        operations = [
            migrations.AddField(
                model_name="order",
                name="user_id",
                field=models.IntegerField(null=True, db_index=True),
            ),
        ]

**Step 2: Migrate data** (backfill in batches)

.. code-block:: python

    # Run as management command or data migration
    Order.objects.filter(user_id__isnull=True).update(user_id=F("customer_id"))

**Step 3: Update code** (deploy code that uses new column)

.. code-block:: python

    # Model now uses user_id as the primary reference
    class Order(models.Model):
        customer_id = models.IntegerField(null=True)  # Deprecated
        user_id = models.IntegerField(db_index=True)

**Step 4: Contract** (remove old column after verification)

.. code-block:: python

    # Migration 2: Remove old column (weeks later, after verification)
    class Migration(migrations.Migration):
        operations = [
            migrations.RemoveField(model_name="order", name="customer_id"),
        ]

Feature Flags with django-waffle
--------------------------------

`django-waffle <https://waffle.readthedocs.io/>`_ enables gradual feature rollouts, A/B testing, and safe deployments.

Installation
^^^^^^^^^^^^

.. code-block:: text

    # requirements/base.txt
    django-waffle==4.1.0

Configuration
^^^^^^^^^^^^^

.. code-block:: python

    # config/settings/base.py
    INSTALLED_APPS = [
        # ...
        "waffle",
    ]

    MIDDLEWARE = [
        # ...
        "waffle.middleware.WaffleMiddleware",
    ]

Run migrations to create the waffle tables:

.. code-block:: bash

    python manage.py migrate waffle

Basic Usage
^^^^^^^^^^^

**In views:**

.. code-block:: python

    from waffle import flag_is_active

    def checkout_view(request):
        if flag_is_active(request, "new_checkout_flow"):
            return render(request, "checkout_v2.html")
        return render(request, "checkout.html")

**In templates:**

.. code-block:: django

    {% load waffle_tags %}

    {% flag "new_checkout_flow" %}
        <p>New checkout experience!</p>
    {% else %}
        <p>Original checkout</p>
    {% endflag %}

**In services:**

.. code-block:: python

    from waffle import flag_is_active

    def order_calculate_shipping(request, order: Order) -> Decimal:
        if flag_is_active(request, "free_shipping_experiment"):
            if order.total >= 50:
                return Decimal("0.00")
        return calculate_standard_shipping(order)

Rollout Strategies
^^^^^^^^^^^^^^^^^^

Create flags in Django admin or via management commands:

**Percentage rollout:**

.. code-block:: python

    from waffle.models import Flag

    Flag.objects.create(
        name="new_checkout_flow",
        percent=10,  # 10% of users
        rollout=True,  # Consistent per-user (sticky)
    )

**User/group targeting:**

.. code-block:: python

    flag = Flag.objects.create(name="beta_features", everyone=False)
    flag.groups.add(beta_testers_group)
    flag.users.add(specific_user)

**Staff only:**

.. code-block:: python

    Flag.objects.create(name="admin_analytics", staff=True)

Feature Flags in Events
^^^^^^^^^^^^^^^^^^^^^^^

When a feature flag affects event handling, include the flag state in the event payload:

.. code-block:: python

    from waffle import flag_is_active

    def order_create(*, request, user_id: int, items: list) -> Order:
        order = Order.objects.create(user_id=user_id)

        # Include flag state for event handlers
        def _publish_event():
            event = OrderCreatedEvent(
                order_id=order.id,
                user_id=user_id,
                use_new_fulfillment=flag_is_active(request, "new_fulfillment"),
            )
            event_bus.publish(event)

        transaction.on_commit(_publish_event)
        return order

This ensures handlers make consistent decisions even if the flag changes between event creation and handling.

Celery Patterns for Event-Driven Systems
----------------------------------------

Celery integrates with the event-driven architecture. These patterns ensure reliability.

Task Routing by Module
^^^^^^^^^^^^^^^^^^^^^^

Route tasks to module-specific queues to prevent one module's spike from affecting others:

.. code-block:: python

    # config/settings/base.py
    CELERY_TASK_ROUTES = {
        "{project_slug}.orders.tasks.*": {"queue": "orders"},
        "{project_slug}.billing.tasks.*": {"queue": "billing"},
        "{project_slug}.notifications.tasks.*": {"queue": "notifications"},
        "{project_slug}.analytics.tasks.*": {"queue": "analytics_low_priority"},
    }

Run workers for specific queues:

.. code-block:: bash

    # High-priority order processing
    celery -A config worker -Q orders -c 4

    # Low-priority analytics (fewer workers)
    celery -A config worker -Q analytics_low_priority -c 1

delay_on_commit() for Event-Driven Reliability
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Celery 5.4+** introduced ``delay_on_commit()``, which ensures tasks only enqueue after Django transactions commit:

.. code-block:: python

    from {project_slug}.orders.tasks import send_order_confirmation

    @transaction.atomic
    def order_create(*, user_id: int, items: list) -> Order:
        order = Order.objects.create(user_id=user_id, status="pending")

        # Task only queues if transaction commits successfully
        send_order_confirmation.delay_on_commit(order_id=order.id)

        return order

Without ``delay_on_commit()``, if the transaction rolls back, the task would still run and fail to find the order.

**For Celery < 5.4**, use the manual pattern:

.. code-block:: python

    @transaction.atomic
    def order_create(*, user_id: int, items: list) -> Order:
        order = Order.objects.create(user_id=user_id, status="pending")

        def _enqueue_task():
            send_order_confirmation.delay(order_id=order.id)

        transaction.on_commit(_enqueue_task)
        return order

Idempotent Tasks
^^^^^^^^^^^^^^^^

Tasks may be retried. Design them to be idempotent:

.. code-block:: python

    @shared_task(bind=True, max_retries=3)
    def send_order_confirmation(self, order_id: int):
        order = Order.objects.get(id=order_id)

        # Check if already processed
        if order.confirmation_sent_at:
            return  # Idempotent: skip if already done

        try:
            send_email(
                to=order.user_email,
                template="order_confirmation",
                context={"order": order},
            )
            order.confirmation_sent_at = timezone.now()
            order.save(update_fields=["confirmation_sent_at"])

        except EmailServiceError as e:
            raise self.retry(exc=e, countdown=60)

Task Visibility Timeout
^^^^^^^^^^^^^^^^^^^^^^^

For long-running tasks, set appropriate visibility timeouts:

.. code-block:: python

    @shared_task(
        bind=True,
        time_limit=3600,  # Hard limit: 1 hour
        soft_time_limit=3300,  # Soft limit: 55 minutes (raises exception)
    )
    def generate_large_report(self, report_id: int):
        try:
            # Long-running work
            ...
        except SoftTimeLimitExceeded:
            # Clean up and reschedule
            Report.objects.filter(id=report_id).update(status="timeout")
            raise

Combining Patterns
------------------

A production deployment typically combines all three patterns:

1. **Migrations**: Use django-pg-zero-downtime-migrations for all schema changes
2. **Feature flags**: Wrap new functionality in waffle flags for gradual rollout
3. **Task reliability**: Use ``delay_on_commit()`` for all Celery tasks triggered by events

Example: Rolling out a new notification system:

.. code-block:: python

    from waffle import flag_is_active
    from django.db import transaction

    @transaction.atomic
    def order_complete(request, order_id: int) -> Order:
        order = Order.objects.get(id=order_id)
        order.status = "complete"
        order.save()

        # Feature-flagged notification system
        if flag_is_active(request, "new_notification_system"):
            send_push_notification.delay_on_commit(
                user_id=order.user_id,
                message=f"Order {order.id} is complete!"
            )
        else:
            send_email_notification.delay_on_commit(order_id=order.id)

        # Event publishing (always happens)
        def _publish():
            event_bus.publish(OrderCompletedEvent(order_id=order.id))
        transaction.on_commit(_publish)

        return order

See Also
--------

- :doc:`event-driven-architecture` — Event bus and transaction.on_commit() patterns
- :doc:`/3-deployment/deployment-on-heroku` — Heroku-specific deployment
- :doc:`observability-logging` — Monitoring and tracing in production
