Module Boundary Enforcement
===========================

This guide explains how to enforce module boundaries in your modular monolith using static analysis tools and database design patterns. Without enforcement, well-intentioned boundaries erode over time as developers take shortcuts.

Overview
--------

The modular monolith architecture depends on clear boundaries between modules. Philosophy alone isn't enough—you need **tooling** that fails the build when boundaries are violated and **database patterns** that make violations impossible.

This guide covers three enforcement layers:

1. **Import enforcement**: Prevent code in one module from importing internal code from another
2. **Database enforcement**: Prevent direct foreign key relationships between modules
3. **CI integration**: Catch violations before they reach production

Import Enforcement with import-linter
-------------------------------------

`import-linter <https://import-linter.readthedocs.io/>`_ analyzes your Python import graph and checks it against defined contracts. It uses `grimp <https://grimp.readthedocs.io/>`_ to build a complete picture of how modules depend on each other.

Installation
^^^^^^^^^^^^

Add import-linter to your dev requirements:

.. code-block:: text

    # requirements/local.txt
    import-linter==2.0

Configuration
^^^^^^^^^^^^^

Create a ``.importlinter`` file at your repository root:

.. code-block:: ini

    [importlinter]
    root_package = {project_slug}

    # Contract 1: Domain modules cannot import from each other
    [importlinter:contract:module-independence]
    name = Domain modules are independent
    type = independence
    modules =
        {project_slug}.users.domain
        {project_slug}.orders.domain
        {project_slug}.billing.domain
        {project_slug}.inventory.domain

    # Contract 2: No direct model imports across modules
    [importlinter:contract:no-cross-module-models]
    name = No direct cross-module model imports
    type = forbidden
    source_modules =
        {project_slug}.orders
        {project_slug}.billing
    forbidden_modules =
        {project_slug}.users.models
        {project_slug}.inventory.models

    # Contract 3: Layered architecture within modules
    [importlinter:contract:layers]
    name = Layers are respected
    type = layers
    layers =
        {project_slug}.orders.api
        {project_slug}.orders.services
        {project_slug}.orders.models

Contract Types
^^^^^^^^^^^^^^

**Independence contracts** prevent modules from importing each other, even transitively. If module A imports module B which imports module C, and A and C are in an independence contract, the check fails.

**Forbidden contracts** block specific imports. Use these for finer-grained rules like "the orders module cannot import user models directly."

**Layers contracts** enforce hierarchical architecture where higher layers can import lower layers but not vice versa. This prevents circular dependencies within a module.

Running import-linter
^^^^^^^^^^^^^^^^^^^^^

Check your contracts manually:

.. code-block:: bash

    # From Docker
    docker compose -f docker-compose.local.yml run --rm django lint-imports

    # Or directly
    lint-imports

If violations exist, you'll see output like:

.. code-block:: text

    BROKEN CONTRACTS:

    No direct cross-module model imports
    ------------------------------------

    {project_slug}.orders.services -> {project_slug}.users.models.User (l. 5)

        {project_slug}.orders.services imports {project_slug}.users.models

CI Integration
^^^^^^^^^^^^^^

Add import-linter to your CI pipeline. In GitHub Actions:

.. code-block:: yaml

    # .github/workflows/ci.yml
    - name: Check import boundaries
      run: |
        docker compose -f docker-compose.local.yml run --rm django lint-imports

The command returns exit code 1 on violations, failing the build.

Programmatic Testing with grimp
-------------------------------

For custom architectural rules beyond what import-linter contracts support, use ``grimp`` directly in pytest:

.. code-block:: python

    # tests/test_architecture.py
    import pytest
    from grimp import build_graph

    @pytest.fixture(scope="session")
    def import_graph():
        """Build import graph once per test session."""
        return build_graph("{project_slug}")

    def test_no_circular_dependencies(import_graph):
        """Verify no circular dependencies exist between top-level modules."""
        modules = ["users", "orders", "billing", "inventory"]

        for module_a in modules:
            for module_b in modules:
                if module_a != module_b:
                    chain = import_graph.find_shortest_chain(
                        importer=f"{{project_slug}}.{module_a}",
                        imported=f"{{project_slug}}.{module_b}"
                    )
                    if chain:
                        reverse = import_graph.find_shortest_chain(
                            importer=f"{{project_slug}}.{module_b}",
                            imported=f"{{project_slug}}.{module_a}"
                        )
                        assert not reverse, (
                            f"Circular dependency: {module_a} <-> {module_b}"
                        )

    def test_domain_events_only_import_from_allowed_modules(import_graph):
        """Verify domain_events only imports from standard library and base classes."""
        details = import_graph.find_modules_that_directly_import(
            "{project_slug}.domain_events"
        )
        # Custom assertion logic here

Lightweight Enforcement with Ruff
---------------------------------

For simpler projects, Ruff's ``flake8-tidy-imports`` rules provide lightweight enforcement without a full import graph:

.. code-block:: toml

    # pyproject.toml
    [tool.ruff.lint]
    select = ["TID"]

    [tool.ruff.lint.flake8-tidy-imports.banned-api]
    "{project_slug}.users.models".msg = "Import from {project_slug}.users.services instead"
    "{project_slug}.orders.models".msg = "Import from {project_slug}.orders.services instead"

This catches common violations but won't detect transitive imports or complex dependency chains.

Database Boundary Enforcement
-----------------------------

Import boundaries prevent code coupling, but database foreign keys create a different kind of coupling. When module A has a foreign key to module B's model, you can't:

- Extract module B to a separate service without complex migrations
- Test module A in true isolation
- Scale module B's database independently

The No-FK Pattern
^^^^^^^^^^^^^^^^^

The Makimo pattern enforces module independence at the database level: **no foreign keys between modules**. Modules reference each other by ID only and communicate through service functions.

.. code-block:: python

    # {project_slug}/orders/models.py
    from django.db import models

    class Order(models.Model):
        # Reference user by ID, not FK
        user_id = models.IntegerField(db_index=True)

        # NOT this:
        # user = models.ForeignKey("users.User", on_delete=models.CASCADE)

        created_at = models.DateTimeField(auto_now_add=True)
        status = models.CharField(max_length=50)

Cross-Module Queries
^^^^^^^^^^^^^^^^^^^^

Without foreign keys, you query across modules through service functions:

.. code-block:: python

    # {project_slug}/orders/services.py
    from {project_slug}.users.services import user_exists, user_get_by_id

    def order_create(*, user_id: int, items: list[dict]) -> Order:
        """Create an order for a user."""
        # Validate user exists through service, not FK constraint
        if not user_exists(user_id):
            raise ValidationError("User does not exist")

        order = Order.objects.create(user_id=user_id)
        # ... create order items
        return order

    def order_with_user_details(order_id: int) -> dict:
        """Get order with user details for display."""
        order = Order.objects.get(id=order_id)
        user = user_get_by_id(order.user_id)

        return {
            "order_id": order.id,
            "status": order.status,
            "user_name": user.name if user else "Unknown",
            "user_email": user.email if user else None,
        }

Trade-offs
^^^^^^^^^^

The no-FK pattern has real costs:

**Lost Django ORM features**:

- No ``select_related()`` across modules
- No ``prefetch_related()`` across modules
- No cascading deletes (handle manually or via events)

**More queries**:

Cross-module operations may require additional queries. Mitigate with caching or denormalization where appropriate.

**Benefits**:

- True module independence—extract any module to a service
- Clear ownership—each module owns its data completely
- Testable in isolation—mock the service interface, not the database
- Explicit contracts—the service function signature is the API

When to Apply
^^^^^^^^^^^^^

Apply the no-FK pattern between **bounded contexts**—modules that represent different business domains. Within a single module, foreign keys are fine.

.. code-block:: text

    {project_slug}/
    ├── users/           # User module - FKs within are OK
    │   ├── models.py    # User, Profile, UserPreferences all interlinked
    │   └── ...
    ├── orders/          # Orders module - FKs within are OK
    │   ├── models.py    # Order, OrderItem, OrderNote all interlinked
    │   └── ...          # BUT: Order.user_id is an integer, not FK

Combining Enforcement Layers
----------------------------

For maximum architectural integrity, combine all three layers:

1. **import-linter contracts** catch import violations at commit time
2. **grimp tests** enforce custom rules in your test suite
3. **No-FK pattern** ensures database independence

A typical CI job runs:

.. code-block:: yaml

    - name: Architectural checks
      run: |
        lint-imports                    # import-linter
        pytest tests/test_architecture.py  # grimp tests

The no-FK pattern is enforced by code review and the constraint that ``ForeignKey`` to cross-module models simply doesn't work without the import.

See Also
--------

- :doc:`/0-introduction/the-modular-monolith-cited` — Philosophy behind the modular monolith
- :doc:`adding-modules` — How to create new modules
- :doc:`event-driven-architecture` — Cross-module communication without imports
- :doc:`service-layer-patterns` — Organizing business logic
