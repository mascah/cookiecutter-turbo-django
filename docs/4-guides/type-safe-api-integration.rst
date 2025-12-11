Type-Safe API Integration
=========================

Achieve end-to-end type safety between your Django REST API and React frontend using OpenAPI code generation. When you change a serializer field in Django, TypeScript immediately flags any frontend code that needs updating.

Overview
--------

The integration pipeline works as follows:

1. **Django Serializers** define your API data structures
2. **drf-spectacular** generates an OpenAPI 3.0 schema from your serializers and viewsets
3. **@hey-api/openapi-ts** generates TypeScript types and React Query hooks from that schema
4. **Your React components** use those generated hooks with full type safety

Your frontend stays in sync with your backend. No more guessing field names, no more runtime type errors from API changes, and no manual type definitions to maintain.

Backend Setup
-------------

The template configures drf-spectacular automatically when ``use_drf`` is enabled. Here's what gets set up:

Django Settings
^^^^^^^^^^^^^^^

In ``config/settings/base.py``, drf-spectacular is configured as the default schema class:

.. code-block:: python

    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "rest_framework.authentication.SessionAuthentication",
            "rest_framework.authentication.TokenAuthentication",
        ),
        "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
        "DEFAULT_PAGINATION_CLASS": "myproject.core.pagination.DefaultPagination",
    }

    SPECTACULAR_SETTINGS = {
        "TITLE": "My Project API",
        "DESCRIPTION": "Documentation of API endpoints",
        "VERSION": "1.0.0",
        "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
        "SCHEMA_PATH_PREFIX": "/api/",
    }

URL Configuration
^^^^^^^^^^^^^^^^^

The OpenAPI schema is served at ``/api/schema/`` in ``config/urls.py``:

.. code-block:: python

    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns += [
        path("api/", include("config.api_router")),
        path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="api-schema"),
            name="api-docs",
        ),
    ]

Example ViewSet and Serializer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

drf-spectacular automatically generates schema from your serializers. No decorators required for basic cases:

.. code-block:: python

    # myproject/tasks/api/serializers.py
    from rest_framework import serializers
    from myproject.tasks.models import Task

    class TaskSerializer(serializers.ModelSerializer):
        class Meta:
            model = Task
            fields = ["id", "title", "description", "status", "created_at"]
            read_only_fields = ["id", "created_at"]


    # myproject/tasks/api/views.py
    from rest_framework import viewsets
    from myproject.tasks.models import Task
    from .serializers import TaskSerializer

    class TaskViewSet(viewsets.ModelViewSet):
        serializer_class = TaskSerializer
        queryset = Task.objects.all()

This generates TypeScript types like:

.. code-block:: typescript

    export type Task = {
        readonly id: number;
        title: string;
        description?: string;
        status: string;
        readonly created_at: string;
    };

Frontend Setup
--------------

The frontend uses ``@hey-api/openapi-ts`` to generate a typed API client from Django's OpenAPI schema.

Configuration
^^^^^^^^^^^^^

Each React app has an ``openapi-ts.config.ts`` configuration file:

.. code-block:: typescript

    // apps/myproject/openapi-ts.config.ts
    import { defaultPlugins, defineConfig } from '@hey-api/openapi-ts';

    export default defineConfig({
      input: 'http://localhost:8000/api/schema',
      output: 'src/services/myproject',
      plugins: [
        ...defaultPlugins,
        '@hey-api/client-fetch',
        {
          name: '@tanstack/react-query',
          infiniteQueryOptions: false,
        },
      ],
    });

**Key configuration options:**

- ``input``: URL to your Django OpenAPI schema endpoint
- ``output``: Directory where generated code will be written
- ``plugins``: Enables fetch client and React Query integration

Dependencies
^^^^^^^^^^^^

Your ``package.json`` needs these dependencies:

.. code-block:: json

    {
      "dependencies": {
        "@hey-api/client-fetch": "^0.9.0",
        "@tanstack/react-query": "^5.90.10"
      },
      "devDependencies": {
        "@hey-api/openapi-ts": "0.87.5"
      }
    }

Running Code Generation
^^^^^^^^^^^^^^^^^^^^^^^

With Django running, generate the client:

.. code-block:: bash

    cd apps/myproject
    pnpm openapi-ts

This creates several files in ``src/services/myproject/``:

- ``types.gen.ts`` - TypeScript interfaces for all API types
- ``sdk.gen.ts`` - Low-level API functions
- ``client.gen.ts`` - Configured HTTP client
- ``@tanstack/react-query.gen.ts`` - React Query hooks and mutation factories

Using Generated Code
--------------------

App Setup
^^^^^^^^^

Configure React Query in your app root:

.. code-block:: tsx

    // src/App.tsx
    import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
    import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 1000 * 60 * 5, // 5 minutes
          retry: 1,
        },
      },
    });

    function App() {
      return (
        <QueryClientProvider client={queryClient}>
          <YourAppContent />
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      );
    }

Client Configuration
^^^^^^^^^^^^^^^^^^^^

Configure the API client with your backend URL and CSRF handling:

.. code-block:: typescript

    // src/lib/api-client.ts
    import { client } from '@/services/myproject/client.gen';

    // Set base URL based on environment
    const apiBaseUrl = import.meta.env.PROD
      ? window.location.origin
      : 'http://localhost:8000';

    client.setConfig({ baseUrl: apiBaseUrl });

    // Add CSRF token to mutating requests
    client.interceptors.request.use((request) => {
      if (request.method !== 'GET') {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')
          ?.getAttribute('content');
        if (csrfToken) {
          request.headers.set('X-CSRFToken', csrfToken);
        }
      }
      return request;
    });

Import this file early in your app initialization to ensure the client is configured before any API calls.

Query Hooks
-----------

The generated code provides ``*Options`` functions for queries. These return configuration objects for ``useQuery()``.

Basic Query
^^^^^^^^^^^

Using the generated hook directly:

.. code-block:: tsx

    import { useQuery } from '@tanstack/react-query';
    import { tasksListOptions } from '@/services/myproject/@tanstack/react-query.gen';

    function TaskList() {
      const { data, isLoading, error } = useQuery(tasksListOptions());

      if (isLoading) return <div>Loading...</div>;
      if (error) return <div>Error: {error.message}</div>;

      return (
        <ul>
          {data?.results?.map((task) => (
            <li key={task.id}>{task.title}</li>
          ))}
        </ul>
      );
    }

Custom Hook Pattern
^^^^^^^^^^^^^^^^^^^

For reusability and cleaner component code, wrap generated hooks in custom hooks:

.. code-block:: typescript

    // src/features/tasks/hooks/useTasks.ts
    import { useQuery } from '@tanstack/react-query';
    import { tasksListOptions } from '@/services/myproject/@tanstack/react-query.gen';

    interface UseTasksProps {
      search?: string;
      page?: number;
      pageSize?: number;
      status?: string;
    }

    export const useTasks = ({
      search,
      page,
      pageSize = 10,
      status,
    }: UseTasksProps = {}) => {
      const queryOptions = tasksListOptions({
        query: {
          search,
          page,
          page_size: pageSize,
          status,
        },
      });

      const { data, isLoading, error, ...rest } = useQuery(queryOptions);

      return {
        tasks: data?.results ?? [],
        totalCount: data?.count ?? 0,
        hasNextPage: !!data?.next,
        hasPreviousPage: !!data?.previous,
        isLoading,
        error,
        ...rest,
      };
    };

Now components can use the simpler interface:

.. code-block:: typescript

    function TaskList() {
      const { tasks, isLoading, totalCount } = useTasks({
        status: 'pending',
        pageSize: 20,
      });

      // Clean, typed access to tasks
    }

Single Item Query
^^^^^^^^^^^^^^^^^

For retrieving a single item by ID:

.. code-block:: typescript

    // src/features/tasks/hooks/useTask.ts
    import { useQuery } from '@tanstack/react-query';
    import { tasksRetrieveOptions } from '@/services/myproject/@tanstack/react-query.gen';

    export const useTask = (id: number) => {
      return useQuery({
        ...tasksRetrieveOptions({ path: { id } }),
        enabled: !!id, // Only fetch when ID is provided
      });
    };

Mutation Hooks
--------------

The generated code provides ``*Mutation`` functions that return configuration objects for ``useMutation()``.

Basic Mutations
^^^^^^^^^^^^^^^

Create, update, and delete operations follow the same pattern:

.. code-block:: typescript

    // src/features/tasks/hooks/useTaskMutations.ts
    import { useMutation, useQueryClient } from '@tanstack/react-query';
    import {
      tasksCreateMutation,
      tasksPartialUpdateMutation,
      tasksDestroyMutation,
      tasksListQueryKey,
      tasksRetrieveQueryKey,
    } from '@/services/myproject/@tanstack/react-query.gen';
    import type { Task } from '@/services/myproject/types.gen';

    export const useCreateTask = () => {
      const queryClient = useQueryClient();

      return useMutation({
        ...tasksCreateMutation(),
        onSuccess: () => {
          // Invalidate list to refetch with new item
          queryClient.invalidateQueries({ queryKey: tasksListQueryKey() });
        },
      });
    };

    export const useUpdateTask = () => {
      const queryClient = useQueryClient();

      return useMutation({
        ...tasksPartialUpdateMutation(),
        onSuccess: (data: Task) => {
          // Invalidate both list and the specific item
          queryClient.invalidateQueries({ queryKey: tasksListQueryKey() });
          queryClient.invalidateQueries({
            queryKey: tasksRetrieveQueryKey({ path: { id: data.id } }),
          });
        },
      });
    };

    export const useDeleteTask = () => {
      const queryClient = useQueryClient();

      return useMutation({
        ...tasksDestroyMutation(),
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: tasksListQueryKey() });
        },
      });
    };

Using Mutations in Components
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: tsx

    function CreateTaskForm() {
      const createTask = useCreateTask();

      const handleSubmit = (formData: { title: string; description: string }) => {
        createTask.mutate(
          { body: formData },
          {
            onSuccess: () => {
              // Navigate or show success message
            },
            onError: (error) => {
              // Handle error
            },
          }
        );
      };

      return (
        <form onSubmit={handleSubmit}>
          {/* Form fields */}
          <button type="submit" disabled={createTask.isPending}>
            {createTask.isPending ? 'Creating...' : 'Create Task'}
          </button>
        </form>
      );
    }

Common Patterns
---------------

Error Handling
^^^^^^^^^^^^^^

React Query provides error state out of the box. Combine with a toast notification system:

.. code-block:: typescript

    import { toast } from 'sonner';

    export const useCreateTask = () => {
      const queryClient = useQueryClient();

      return useMutation({
        ...tasksCreateMutation(),
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: tasksListQueryKey() });
          toast.success('Task created successfully');
        },
        onError: (error) => {
          toast.error(`Failed to create task: ${error.message}`);
        },
      });
    };

Invalidating Related Queries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When mutations affect multiple query caches, invalidate all relevant queries:

.. code-block:: typescript

    export const useCompleteTask = () => {
      const queryClient = useQueryClient();

      return useMutation({
        ...tasksPartialUpdateMutation(),
        onSuccess: (data: Task) => {
          // Invalidate task queries
          queryClient.invalidateQueries({ queryKey: tasksListQueryKey() });
          queryClient.invalidateQueries({
            queryKey: tasksRetrieveQueryKey({ path: { id: data.id } }),
          });
          // Also invalidate dashboard stats that depend on task counts
          queryClient.invalidateQueries({ queryKey: ['dashboard', 'stats'] });
        },
      });
    };

Loading States
^^^^^^^^^^^^^^

Use React Query's loading states for UI feedback:

.. code-block:: tsx

    function TaskList() {
      const { tasks, isLoading, isFetching, error } = useTasks();

      // isLoading: true on first load (no cached data)
      // isFetching: true when fetching (including background refetch)

      if (isLoading) {
        return <LoadingSkeleton />;
      }

      return (
        <div>
          {isFetching && <RefreshIndicator />}
          <ul>
            {tasks.map((task) => (
              <TaskItem key={task.id} task={task} />
            ))}
          </ul>
        </div>
      );
    }

Development Workflow
--------------------

The typical development cycle when working with the API:

1. **Start Django** with ``just up`` or ``docker compose up``

2. **Modify Django API** - Add or change serializers, viewsets, or fields

3. **Regenerate client** - Run ``pnpm openapi-ts`` in your frontend app

4. **TypeScript catches mismatches** - Your IDE will immediately show errors where component code doesn't match the new types

5. **Update React code** - Fix any type errors and adapt to API changes

**When to regenerate:**

- After adding new API endpoints
- After changing serializer fields
- After modifying URL patterns
- After changing pagination or filter options

**Tip:** Consider adding a pre-commit hook or CI check to ensure the generated client stays in sync with the backend schema.

Alternative: Orval for Full Client Generation
----------------------------------------------

While ``@hey-api/openapi-ts`` provides types and query hooks, `Orval <https://orval.dev/>`_ is an alternative that generates more comprehensive clients with additional features.

Comparison
^^^^^^^^^^

+---------------------------+--------------------------------+--------------------------------+
| Feature                   | @hey-api/openapi-ts            | Orval                          |
+===========================+================================+================================+
| TypeScript types          | Yes                            | Yes                            |
+---------------------------+--------------------------------+--------------------------------+
| React Query hooks         | Yes                            | Yes                            |
+---------------------------+--------------------------------+--------------------------------+
| Runtime overhead          | Minimal                        | Slightly more                  |
+---------------------------+--------------------------------+--------------------------------+
| MSW mocks                 | No                             | Yes (built-in)                 |
+---------------------------+--------------------------------+--------------------------------+
| Zod schemas               | No                             | Yes (optional)                 |
+---------------------------+--------------------------------+--------------------------------+
| Custom templates          | Limited                        | Extensive                      |
+---------------------------+--------------------------------+--------------------------------+

**Choose @hey-api/openapi-ts when:**

- You want minimal runtime overhead
- You're comfortable writing your own fetch wrappers
- You prefer simpler generated code

**Choose Orval when:**

- You want MSW mocks generated automatically for testing
- You need Zod schemas for runtime validation
- You want more customization of generated code

Orval Configuration Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: typescript

    // orval.config.ts
    import { defineConfig } from "orval";

    export default defineConfig({
      api: {
        input: {
          target: "http://localhost:8000/api/schema/",
        },
        output: {
          client: "react-query",
          target: "./src/lib/api/generated.ts",
          mock: true,  // Generates MSW handlers
          override: {
            mutator: {
              path: "./src/lib/api/custom-fetch.ts",
              name: "customFetch",
            },
          },
        },
      },
    });

The generated MSW mocks can be used directly in tests:

.. code-block:: typescript

    // src/mocks/handlers.ts
    import { getTasksMock, getTasksHandler } from "../lib/api/generated.msw";

    export const handlers = [
      getTasksHandler(),
      // Add more handlers...
    ];

Breaking Change Detection with oasdiff
--------------------------------------

API changes can break frontend clients. `oasdiff <https://github.com/Tufin/oasdiff>`_ detects breaking changes by comparing OpenAPI schemas.

Installation
^^^^^^^^^^^^

.. code-block:: bash

    # macOS
    brew install oasdiff

    # Or via Go
    go install github.com/tufin/oasdiff@latest

    # Or via Docker
    docker pull tufin/oasdiff

Local Usage
^^^^^^^^^^^

Compare your current schema against a baseline:

.. code-block:: bash

    # Save current schema as baseline
    curl http://localhost:8000/api/schema/ > api-schema-baseline.json

    # After making changes, check for breaking changes
    oasdiff breaking api-schema-baseline.json http://localhost:8000/api/schema/

Breaking changes include:

- Removing or renaming endpoints
- Adding required parameters
- Removing response fields
- Changing field types

CI Integration
^^^^^^^^^^^^^^

Add oasdiff to your CI pipeline to catch breaking changes before they're merged:

.. code-block:: yaml

    # .github/workflows/ci.yml
    - name: Check for breaking API changes
      run: |
        # Fetch schema from main branch
        git fetch origin main
        git show origin/main:api-schema.json > base-schema.json || echo '{}' > base-schema.json

        # Generate current schema
        docker compose -f docker-compose.local.yml run --rm django \
          python manage.py spectacular --file /tmp/schema.json
        docker compose -f docker-compose.local.yml cp django:/tmp/schema.json ./current-schema.json

        # Compare schemas
        oasdiff breaking base-schema.json current-schema.json --fail-on-diff

The ``--fail-on-diff`` flag causes the command to exit with a non-zero code if breaking changes are detected.

Versioning Schema in Git
^^^^^^^^^^^^^^^^^^^^^^^^

Track your API schema in version control for easy diffing:

.. code-block:: yaml

    # .github/workflows/update-schema.yml
    name: Update API Schema

    on:
      push:
        branches: [main]
        paths:
          - "**/serializers.py"
          - "**/views.py"
          - "**/api_router.py"

    jobs:
      update-schema:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4

          - name: Generate schema
            run: |
              docker compose -f docker-compose.local.yml run --rm django \
                python manage.py spectacular --file api-schema.json

          - name: Commit updated schema
            run: |
              git config user.name "GitHub Actions"
              git config user.email "actions@github.com"
              git add api-schema.json
              git diff --staged --quiet || git commit -m "chore: update API schema"
              git push

Summary
-------

1. **drf-spectacular** generates OpenAPI schemas automatically from your DRF serializers
2. **@hey-api/openapi-ts** generates TypeScript types and React Query hooks from that schema
3. **Query hooks** use ``*Options`` functions with ``useQuery()`` for fetching data
4. **Mutation hooks** use ``*Mutation`` functions with ``useMutation()`` and invalidate caches on success
5. **Custom hooks** wrap generated code for cleaner component interfaces
6. **Regenerate** the client after any backend API changes to keep types in sync
