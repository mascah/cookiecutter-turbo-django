Service Layer Patterns
======================

This guide explains how to organize business logic in your Django modules using the services and selectors pattern. This approach, popularized by the `HackSoft Django Styleguide <https://github.com/HackSoftware/Django-Styleguide>`_, creates a clear separation between read and write operations.

Overview
--------

In a typical Django project, business logic ends up scattered across views, serializers, model methods, signals, and management commands. This makes code hard to test, reuse, and reason about.

The services/selectors pattern establishes a simple rule: **all business logic lives in services (writes) or selectors (reads)**. Everything else—views, serializers, signals—becomes thin glue code that delegates to these functions.

The Core Principle
------------------

**Services** handle write operations:

- Create, update, or delete data
- Trigger side effects (emails, events, external APIs)
- Enforce business rules on mutations

**Selectors** handle read operations:

- Query and filter data
- Apply access control to queries
- Return data without side effects

.. code-block:: python

    # {project_slug}/users/services.py - Write operations
    def user_create(*, email: str, name: str) -> User:
        """Create a new user with profile."""
        user = User(email=email)
        user.full_clean()  # Validate before save
        user.save()

        profile_create(user=user, name=name)
        send_welcome_email.delay(user_id=user.id)

        return user

    # {project_slug}/users/selectors.py - Read operations
    def user_list(*, fetched_by: User) -> QuerySet[User]:
        """Return users visible to the requesting user."""
        if fetched_by.is_staff:
            return User.objects.all()
        return User.objects.filter(is_active=True)

Where Business Logic Should NOT Live
------------------------------------

The pattern is as much about where logic **doesn't** go as where it does:

**Not in views**

Views handle HTTP concerns only: parsing requests, calling services/selectors, returning responses.

.. code-block:: python

    # BAD - business logic in view
    class UserCreateView(APIView):
        def post(self, request):
            email = request.data["email"]
            if User.objects.filter(email=email).exists():
                raise ValidationError("Email taken")
            user = User.objects.create(email=email)
            Profile.objects.create(user=user)
            send_welcome_email.delay(user.id)
            return Response(UserSerializer(user).data)

    # GOOD - view delegates to service
    class UserCreateView(APIView):
        def post(self, request):
            serializer = UserCreateInputSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user = user_create(**serializer.validated_data)

            return Response(UserSerializer(user).data)

**Not in serializers**

Serializers handle validation and transformation, not business logic.

.. code-block:: python

    # BAD - business logic in serializer
    class UserSerializer(serializers.ModelSerializer):
        def create(self, validated_data):
            user = User.objects.create(**validated_data)
            Profile.objects.create(user=user)  # Side effect!
            return user

    # GOOD - serializer only validates
    class UserCreateInputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        name = serializers.CharField(max_length=100)

**Not in signals**

Signals create hidden coupling. Use explicit service calls or domain events instead.

.. code-block:: python

    # BAD - hidden side effect in signal
    @receiver(post_save, sender=User)
    def create_profile_on_user_create(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    # GOOD - explicit in service
    def user_create(*, email: str, name: str) -> User:
        user = User.objects.create(email=email)
        profile_create(user=user, name=name)  # Explicit, testable
        return user

**Not in model save()**

Overriding ``save()`` for business logic makes models unpredictable and hard to test.

.. code-block:: python

    # BAD - side effects in save()
    class User(models.Model):
        def save(self, *args, **kwargs):
            is_new = self.pk is None
            super().save(*args, **kwargs)
            if is_new:
                send_welcome_email.delay(self.id)  # Surprise!

    # GOOD - model is just data
    class User(models.Model):
        email = models.EmailField(unique=True)
        # No custom save() with side effects

Model Properties: The Exception
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Model properties are acceptable for **simple, non-relational computations**:

.. code-block:: python

    class User(models.Model):
        first_name = models.CharField(max_length=100)
        last_name = models.CharField(max_length=100)

        @property
        def full_name(self) -> str:
            """Simple computation from own fields - OK as property."""
            return f"{self.first_name} {self.last_name}"

        @property
        def is_adult(self) -> bool:
            """Simple business rule from own fields - OK as property."""
            return self.age >= 18

But move it to a selector if it:

- Queries related objects
- Has complex business rules
- Needs to be reused across modules

Writing Services
----------------

Services should be explicit about their inputs and outputs.

Function Signature Pattern
^^^^^^^^^^^^^^^^^^^^^^^^^^

Use keyword-only arguments (``*``) to force explicit parameter names at call sites:

.. code-block:: python

    # Forces callers to write: user_create(email="...", name="...")
    # Instead of: user_create("...", "...")
    def user_create(*, email: str, name: str) -> User:
        ...

Return DTOs for Cross-Module Communication
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When services are called from other modules, return data transfer objects instead of model instances:

.. code-block:: python

    from dataclasses import dataclass

    @dataclass(frozen=True)
    class UserDTO:
        id: int
        email: str
        name: str

    def user_get_by_id(user_id: int) -> UserDTO | None:
        """Public interface for other modules."""
        try:
            user = User.objects.get(id=user_id)
            return UserDTO(id=user.id, email=user.email, name=user.name)
        except User.DoesNotExist:
            return None

This prevents other modules from depending on your model internals.

Atomic Transactions
^^^^^^^^^^^^^^^^^^^

Wrap services that make multiple changes in ``transaction.atomic()``:

.. code-block:: python

    from django.db import transaction

    @transaction.atomic
    def order_create(*, user_id: int, items: list[dict]) -> Order:
        """Create order with items atomically."""
        order = Order.objects.create(user_id=user_id, status="pending")

        for item in items:
            OrderItem.objects.create(
                order=order,
                product_id=item["product_id"],
                quantity=item["quantity"],
            )

        return order

Writing Selectors
-----------------

Selectors return querysets or model instances, never triggering side effects.

Filtering with Access Control
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Selectors often need to filter based on who's asking:

.. code-block:: python

    def order_list(*, fetched_by: User) -> QuerySet[Order]:
        """Return orders visible to the requesting user."""
        if fetched_by.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user_id=fetched_by.id)

    def order_get(*, order_id: int, fetched_by: User) -> Order:
        """Get a specific order if the user can access it."""
        queryset = order_list(fetched_by=fetched_by)
        return queryset.get(id=order_id)

Avoid N+1 Queries
^^^^^^^^^^^^^^^^^

Selectors should handle query optimization:

.. code-block:: python

    def order_list_with_items(*, fetched_by: User) -> QuerySet[Order]:
        """Return orders with items pre-fetched."""
        return (
            order_list(fetched_by=fetched_by)
            .prefetch_related("items", "items__product")
            .select_related("shipping_address")
        )

Module Structure
----------------

Organize services and selectors as modules grow:

Small Module
^^^^^^^^^^^^

.. code-block:: text

    {project_slug}/users/
    ├── models.py
    ├── services.py      # All services in one file
    ├── selectors.py     # All selectors in one file
    └── ...

Large Module
^^^^^^^^^^^^

.. code-block:: text

    {project_slug}/orders/
    ├── models.py
    ├── services/
    │   ├── __init__.py  # Re-export public functions
    │   ├── order.py     # order_create, order_update, order_cancel
    │   ├── payment.py   # payment_process, payment_refund
    │   └── shipping.py  # shipping_calculate, shipping_create
    ├── selectors/
    │   ├── __init__.py
    │   ├── order.py
    │   └── analytics.py
    └── ...

Re-export public functions from ``__init__.py`` for a clean API:

.. code-block:: python

    # {project_slug}/orders/services/__init__.py
    from .order import order_create, order_update, order_cancel
    from .payment import payment_process, payment_refund

Common Pitfalls
---------------

Over-engineering small projects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For a simple CRUD app, services/selectors add overhead without benefit. Use this pattern when:

- Multiple modules need to call the same business logic
- Business rules are complex enough to warrant isolation
- You want clear seams for future module extraction

N+1 queries across modules
^^^^^^^^^^^^^^^^^^^^^^^^^^

Without foreign keys (see :doc:`module-boundary-enforcement`), cross-module queries can multiply:

.. code-block:: python

    # BAD - N+1 queries
    def order_list_with_users(fetched_by: User) -> list[dict]:
        orders = order_list(fetched_by=fetched_by)
        return [
            {
                "order": order,
                "user": user_get_by_id(order.user_id),  # Query per order!
            }
            for order in orders
        ]

    # BETTER - batch fetch
    def order_list_with_users(fetched_by: User) -> list[dict]:
        orders = list(order_list(fetched_by=fetched_by))
        user_ids = [o.user_id for o in orders]
        users = user_get_by_ids(user_ids)  # Single query
        users_by_id = {u.id: u for u in users}

        return [
            {"order": order, "user": users_by_id.get(order.user_id)}
            for order in orders
        ]

Unclear public interfaces
^^^^^^^^^^^^^^^^^^^^^^^^^

Document which services/selectors are part of the module's public API:

.. code-block:: python

    # {project_slug}/users/services.py

    # === PUBLIC API ===
    # These functions can be called from other modules

    def user_create(...): ...
    def user_update(...): ...
    def user_exists(user_id: int) -> bool: ...

    # === INTERNAL ===
    # These are implementation details, not for external use

    def _validate_email_domain(email: str) -> bool: ...
    def _send_verification_email(user: User) -> None: ...

Testing Services and Selectors
------------------------------

Services and selectors are easy to unit test because they're plain functions:

.. code-block:: python

    import pytest
    from {project_slug}.users.services import user_create
    from {project_slug}.users.selectors import user_list

    @pytest.mark.django_db
    def test_user_create():
        user = user_create(email="test@example.com", name="Test User")

        assert user.email == "test@example.com"
        assert user.profile.name == "Test User"

    @pytest.mark.django_db
    def test_user_list_filters_inactive_for_non_staff(user_factory):
        staff = user_factory(is_staff=True)
        regular = user_factory(is_staff=False)
        inactive = user_factory(is_active=False)

        # Staff sees everyone
        assert inactive in user_list(fetched_by=staff)

        # Regular user doesn't see inactive
        assert inactive not in user_list(fetched_by=regular)

See Also
--------

- `HackSoft Django Styleguide <https://github.com/HackSoftware/Django-Styleguide>`_ — Original source for these patterns
- :doc:`module-boundary-enforcement` — Enforcing boundaries between modules
- :doc:`event-driven-architecture` — Cross-module communication
- :doc:`adding-modules` — Creating new modules
