.. _testing:

Testing
========

Build tests for your application. As best practice, write tests immediately after documenting, before starting on code.

Pytest
------

This project uses Pytest_, a framework for building simple and scalable tests.
After you have set up to `develop locally`_, run the following commands to make sure the testing environment is ready: ::

    $ pytest

You will get a readout of the `users` app that has already been set up with tests. If you do not want to run the `pytest` on the entire project, you can target a particular app by typing in its location: ::

   $ pytest <path-to-app-in-project/app>

If you set up your project to `develop locally with docker`_, run the following command: ::

   $ docker compose -f docker-compose.local.yml run --rm django pytest

Targeting particular apps for testing in ``docker`` follows a similar pattern as previously shown above.

Coverage
--------

You should build your tests to provide the highest level of **code coverage**. You can run the ``pytest`` with code ``coverage`` by typing in the following command: ::

   $ coverage run -m pytest

Once the tests are complete, in order to see the code coverage, run the following command: ::

   $ coverage report

If you're running the project locally with Docker, use these commands instead: ::

   $ docker compose -f docker-compose.local.yml run --rm django coverage run -m pytest
   $ docker compose -f docker-compose.local.yml run --rm django coverage report

.. note::

   At the root of the project folder, you will find the `pytest.ini` file. You can use this to customize_ the ``pytest`` to your liking.

   The configuration for ``coverage`` can be found in ``pyproject.toml``. You can find out more about `configuring`_ ``coverage``.

Testing Event-Driven Code
-------------------------

The event-driven architecture (see :doc:`event-driven-architecture`) needs specific testing patterns because events are published inside ``transaction.on_commit()`` callbacks.

Testing transaction.on_commit()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Django's ``TestCase`` wraps each test in a transaction that never commits, so ``on_commit()`` callbacks never fire. Django 3.2+ provides ``captureOnCommitCallbacks()`` to solve this:

.. code-block:: python

    from django.test import TestCase
    from {project_slug}.orders.services import order_create

    class OrderServiceTests(TestCase):
        def test_event_published_after_commit(self):
            # Capture callbacks and execute them synchronously
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                order = order_create(user_id=1, items=[{"product_id": 1}])

            # Callbacks were captured and executed
            self.assertEqual(len(callbacks), 1)
            # Event handlers ran synchronously during the test

The key is ``execute=True``, which runs the callbacks immediately instead of just capturing them.

**With pytest-django**, use the ``django_capture_on_commit_callbacks`` fixture:

.. code-block:: python

    import pytest
    from {project_slug}.orders.services import order_create

    @pytest.mark.django_db
    def test_event_published(django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True) as callbacks:
            order = order_create(user_id=1, items=[{"product_id": 1}])

        assert len(callbacks) == 1

For integration tests that need full transaction behavior, use ``TransactionTestCase`` or ``@pytest.mark.django_db(transaction=True)``.

The FakeEventBus Pattern
^^^^^^^^^^^^^^^^^^^^^^^^

Unit testing event handlers in isolation requires a test double that captures published events without triggering other handlers:

.. code-block:: python

    # {project_slug}/domain_events/testing.py
    from typing import Type

    class FakeEventBus:
        """Test double for the event bus that captures events without handling them."""

        def __init__(self):
            self.published_events = []
            self._subscribers = {}

        def publish(self, event):
            """Capture the event without dispatching to handlers."""
            self.published_events.append(event)

        def subscribe(self, event_type, handler):
            """Record subscriptions (for verification if needed)."""
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)

        def assert_event_published(self, event_type: Type, **attrs):
            """Assert an event of the given type was published with matching attributes."""
            for event in self.published_events:
                if isinstance(event, event_type):
                    if all(getattr(event, k, None) == v for k, v in attrs.items()):
                        return True
            raise AssertionError(
                f"Event {event_type.__name__} with {attrs} not found. "
                f"Published: {[type(e).__name__ for e in self.published_events]}"
            )

        def assert_no_events_published(self):
            """Assert no events were published."""
            if self.published_events:
                raise AssertionError(
                    f"Expected no events, but found: "
                    f"{[type(e).__name__ for e in self.published_events]}"
                )

        def clear(self):
            """Clear captured events between tests."""
            self.published_events.clear()

**Using the FakeEventBus in tests:**

.. code-block:: python

    import pytest
    from unittest.mock import patch
    from {project_slug}.domain_events.testing import FakeEventBus
    from {project_slug}.domain_events.events import OrderCreatedEvent
    from {project_slug}.orders.services import order_create

    @pytest.fixture
    def fake_event_bus():
        bus = FakeEventBus()
        with patch("{project_slug}.domain_events.bus.event_bus", bus):
            yield bus

    @pytest.mark.django_db
    def test_order_create_publishes_event(fake_event_bus, django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True):
            order = order_create(user_id=42, items=[{"product_id": 1}])

        fake_event_bus.assert_event_published(
            OrderCreatedEvent,
            order_id=order.id,
            user_id=42,
        )

Contract Testing with Pydantic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Domain events form contracts between modules. Use Pydantic to validate event schemas and catch breaking changes:

.. code-block:: python

    # {project_slug}/domain_events/contracts.py
    from pydantic import BaseModel, ConfigDict

    class OrderCreatedEventContract(BaseModel):
        """Contract for OrderCreatedEvent - validates structure and types."""
        model_config = ConfigDict(extra="forbid")  # Reject unknown fields

        order_id: int
        user_id: int
        items: list[dict]
        total_amount: str  # Decimal serialized as string

    class PrescriptionApprovedEventContract(BaseModel):
        model_config = ConfigDict(extra="forbid")

        prescription_id: int
        patient_id: int
        provider_id: int
        approved_at: str  # ISO datetime string

**Testing events against contracts:**

.. code-block:: python

    import pytest
    from pydantic import ValidationError
    from {project_slug}.domain_events.events import OrderCreatedEvent
    from {project_slug}.domain_events.contracts import OrderCreatedEventContract

    def test_order_created_event_matches_contract():
        """Verify event can be serialized to match the contract."""
        event = OrderCreatedEvent(
            order_id=1,
            user_id=42,
            items=[{"product_id": 1, "quantity": 2}],
            total_amount="99.99",
        )

        # This raises ValidationError if event doesn't match contract
        contract = OrderCreatedEventContract(
            order_id=event.order_id,
            user_id=event.user_id,
            items=event.items,
            total_amount=event.total_amount,
        )

        assert contract.order_id == 1

    def test_contract_rejects_extra_fields():
        """Verify contract catches unexpected fields (breaking changes)."""
        with pytest.raises(ValidationError):
            OrderCreatedEventContract(
                order_id=1,
                user_id=42,
                items=[],
                total_amount="0.00",
                unexpected_field="oops",  # This should fail
            )

This pattern catches breaking changes when:

- A required field is removed from an event
- A field type changes
- An unexpected field is added (which other modules might not handle)

Test Organization
-----------------

Organize tests within each module:

.. code-block:: text

    {project_slug}/orders/
    ├── tests/
    │   ├── __init__.py
    │   ├── conftest.py        # Module-specific fixtures
    │   ├── factories.py       # Model factories (Factory Boy)
    │   ├── test_models.py     # Model unit tests
    │   ├── test_services.py   # Service layer tests
    │   ├── test_selectors.py  # Selector tests
    │   ├── test_handlers.py   # Event handler tests
    │   └── test_api.py        # API endpoint tests

**conftest.py for module-specific fixtures:**

.. code-block:: python

    # {project_slug}/orders/tests/conftest.py
    import pytest
    from {project_slug}.orders.tests.factories import OrderFactory

    @pytest.fixture
    def order(db):
        return OrderFactory()

    @pytest.fixture
    def completed_order(db):
        return OrderFactory(status="completed")

See Also
--------

- :doc:`event-driven-architecture` — Event bus and transaction.on_commit() patterns
- :doc:`service-layer-patterns` — Testing services and selectors
- :doc:`module-boundary-enforcement` — Architectural testing with grimp

.. seealso::

   For unit tests, run: ::

      $ python manage.py test

   Since this is a fresh install, and there are no tests built using the Python `unittest`_ library yet, you should get feedback that says there were no tests carried out.

.. _Pytest: https://docs.pytest.org/en/latest/example/simple.html
.. _develop locally: ./developing-locally.html
.. _develop locally with docker: ./developing-locally-docker.html
.. _customize: https://docs.pytest.org/en/latest/customize.html
.. _unittest: https://docs.python.org/3/library/unittest.html#module-unittest
.. _configuring: https://coverage.readthedocs.io/en/latest/config.html
