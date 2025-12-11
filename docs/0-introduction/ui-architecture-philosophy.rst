UI Architecture Philosophy
==========================

This template provides a pragmatic, multi-tier approach to building user interfaces. Rather than forcing a single frontend paradigm, it gives you **the right tool for each job**—from dead-simple Django templates to fully interactive React applications.

The Core Principle
------------------

Not every page needs React. Not every page can get by with server rendered HTML. The key is matching your UI approach to the actual requirements:

- **Prototyping and simple pages**: Django templates with Tailwind CSS and optional Alpine.js
- **Highly interactive applications**: Vite-based SPAs (React, Vue) integrated via django-vite
- **Marketing and content pages**: Pre-rendered static assets (Astro) served through Django

Each approach is immediately available in this template. You choose based on your needs, not your tooling constraints.

Tier 1: Django Templates (Simple)
---------------------------------

For admin dashboards, forms, settings pages, and rapid prototyping, Django templates remain the simplest and most productive choice.

django-tailwind-cli
^^^^^^^^^^^^^^^^^^^

This template includes `django-tailwind-cli`_ for Tailwind CSS integration **without webpack, Node.js in production, or complex build pipelines**. The Tailwind binary runs directly—no npm required.

In development, a sidecar container watches for changes:

.. code-block:: yaml

    # docker-compose.local.yml
    tailwind_sidecar:
      command: python manage.py tailwind watch

For production, the custom ``collectstatic`` command automatically builds your CSS:

.. code-block:: bash

    python manage.py collectstatic  # Runs tailwind build first

Alpine.js for Interactivity
^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you need interactive behavior—dropdowns, modals, form validation—without a full JavaScript framework, `Alpine.js`_ is the recommended addition. Add it via CDN when needed:

.. code-block:: html

    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>

    <div x-data="{ open: false }">
      <button @click="open = !open">Toggle</button>
      <div x-show="open">Content here</div>
    </div>

Alpine.js is intentionally not included by default—add it when your page needs it. This keeps simple pages simple.

**Best for**: Admin interfaces, settings pages, forms, server-rendered content, rapid prototyping.

Tier 2: Vite-Based SPAs (Interactive)
-------------------------------------

When you need rich client-side interactivity—complex state management, real-time updates, data visualizations—reach for a proper frontend framework.

django-vite Integration
^^^^^^^^^^^^^^^^^^^^^^^

The template uses `django-vite`_ to bridge Django and Vite based frontends. This gives you:

- **Hot Module Replacement** in development
- **Manifest-based asset versioning** in production
- **Seamless Django template integration**

The Django template bootstraps your SPA:

.. code-block:: html+django

    {% load django_vite %}

    <!DOCTYPE html>
    <html lang="en">
      <head>
        {% vite_hmr_client app='myapp' %}
        {% vite_react_refresh app='myapp' %}
        {% vite_asset 'main.tsx' app='myapp' %}
      </head>
      <body>
        <div id="root"></div>
      </body>
    </html>

The ``vite_hmr_client`` and ``vite_react_refresh`` tags enable hot reloading during development. In production, ``vite_asset`` reads from Vite's manifest to include cache-busted asset URLs.

Vite Configuration
^^^^^^^^^^^^^^^^^^

The key Vite settings for Django integration:

.. code-block:: typescript

    // vite.config.ts
    export default defineConfig({
      base: '/static/myapp',  // Matches Django's static URL
      build: {
        manifest: 'manifest.json',  // Required for django-vite
        outDir: 'dist/myapp',
      },
    });

Django Settings
^^^^^^^^^^^^^^^

Configure the django-vite app in settings:

.. code-block:: python

    # settings/base.py
    DJANGO_VITE = {
        "myapp": {
            "dev_mode": DEBUG,
            "dev_server_port": 5173,
            "static_url_prefix": "myapp",
            "manifest_path": BASE_DIR / "apps/myapp/dist/myapp/manifest.json",
        },
    }

    STATICFILES_DIRS = [
        BASE_DIR / "apps/myapp/dist",  # Include built assets
    ]

**Best for**: Complex dashboards, real time applications, data-heavy UIs, anywhere React/Vue makes sense.

Tier 3: Pre-Built Static Assets (Marketing)
-------------------------------------------

For landing pages, marketing sites, and content heavy pages, pre-rendered static HTML offers the best performance and SEO. The template includes an Astro workspace for this purpose.

Astro Configuration
^^^^^^^^^^^^^^^^^^^

Astro generates static HTML with optional interactive islands:

.. code-block:: javascript

    // astro.config.mjs
    export default defineConfig({
      integrations: [react()],  // React islands for interactive components
      output: 'static',         // Pre-render everything
      outDir: './dist',
      base: '/static/',         // Django serves from here
    });

Serving from Django
^^^^^^^^^^^^^^^^^^^

Static pages can be served directly through Django's URL routing:

.. code-block:: python

    from django.http import FileResponse, Http404
    from django.conf import settings
    from pathlib import Path

    def serve_landing_page(request):
        """Serve pre-rendered Astro landing page."""
        if settings.DEBUG:
            html_path = Path(settings.BASE_DIR) / "apps/landing/dist/index.html"
        else:
            html_path = Path(settings.STATIC_ROOT) / "index.html"

        if html_path.exists():
            return FileResponse(html_path.open("rb"), content_type="text/html")
        raise Http404("Landing page not found. Run 'pnpm build' first.")

    urlpatterns = [
        path("", serve_landing_page, name="home"),
    ]

The Astro output directory is also added to ``STATICFILES_DIRS``, so ``collectstatic`` gathers all assets for production.

**Best for**: Landing pages, marketing sites, documentation, SEO-critical content.

Choosing the Right Approach
---------------------------

+---------------------------+----------------------+----------------------+----------------------+
| Requirement               | Django Templates     | Vite SPA             | Astro Static         |
+===========================+======================+======================+======================+
| Server-rendered HTML      | Yes                  | No                   | Yes (pre-rendered)   |
+---------------------------+----------------------+----------------------+----------------------+
| SEO-friendly              | Yes                  | Requires SSR         | Yes                  |
+---------------------------+----------------------+----------------------+----------------------+
| Complex client state      | No (use Alpine.js)   | Yes                  | Limited (islands)    |
+---------------------------+----------------------+----------------------+----------------------+
| Build step required       | No                   | Yes                  | Yes                  |
+---------------------------+----------------------+----------------------+----------------------+
| Hot module replacement    | No                   | Yes                  | Yes                  |
+---------------------------+----------------------+----------------------+----------------------+
| TypeScript support        | No                   | Yes                  | Yes                  |
+---------------------------+----------------------+----------------------+----------------------+
| Best for                  | Admin, forms,        | Dashboards, apps,    | Landing pages,       |
|                           | prototypes           | complex UIs          | marketing            |
+---------------------------+----------------------+----------------------+----------------------+

The Monorepo Advantage
----------------------

With Turborepo, all frontend approaches share:

- **Common component library** in ``packages/ui/`` (Radix UI + shadcn components)
- **Shared TypeScript, ESLint, and Prettier configs**
- **Single ``pnpm build`` command** builds everything
- **Unified dependency management** via pnpm workspaces

This means your landing page (Astro), main application (React), and Django admin can all use the same design system without duplication.

Further Reading
---------------

- `django-tailwind-cli`_ — Tailwind CSS without Node.js
- `django-vite`_ — Vite integration for Django
- `Alpine.js`_ — Minimal JavaScript framework
- `Astro`_ — Static site generator with islands architecture

.. _django-tailwind-cli: https://github.com/oliverandrich/django-tailwind-cli
.. _django-vite: https://github.com/MrBin99/django-vite
.. _Alpine.js: https://alpinejs.dev/
.. _Astro: https://astro.build/
