.. _product-analytics:

Product Analytics with PostHog
==============================

.. index:: analytics, PostHog, tracking, events, page views, sessions, heatmaps, session replay, feature flags

This guide explains how to implement comprehensive product and web analytics using PostHog. The template includes a production-ready setup with automatic page view tracking, custom event capture, user identification, and infrastructure for session replays, heatmaps, and feature flags.

Why PostHog?
------------

PostHog is an open-source product analytics platform that combines multiple tools in one:

- **Product Analytics**: Track user behavior, funnels, and retention
- **Web Analytics**: Page views, sessions, referrers, and geography
- **Session Replay**: Watch user sessions to understand behavior
- **Heatmaps**: Visualize where users click and scroll
- **Feature Flags**: Roll out features gradually and run A/B tests
- **Surveys**: Collect user feedback directly in-app

Unlike Google Analytics, PostHog is privacy-friendly and can be self-hosted. The all-in-one approach eliminates the need for multiple tools and simplifies your analytics stack.

Architecture Overview
---------------------

The template implements a dual-tracking approach with both frontend and backend analytics:

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────────┐
    │                         Browser                                  │
    │  ┌─────────────────┐                    ┌─────────────────────┐ │
    │  │   React App     │                    │   PostHog JS SDK    │ │
    │  │                 │ ──────────────────▶│                     │ │
    │  │  posthog.capture│                    │  Page views, events │ │
    │  └─────────────────┘                    └──────────┬──────────┘ │
    └────────────────────────────────────────────────────┼────────────┘
                                                         │
                                                         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    Django Backend                                │
    │  ┌─────────────────┐      ┌─────────────────────────────────┐   │
    │  │  Reverse Proxy  │◀─────│  /ph/* routes to PostHog Cloud  │   │
    │  │  (views.py)     │      └─────────────────────────────────┘   │
    │  └────────┬────────┘                                            │
    │           │                                                      │
    │  ┌────────▼────────┐      ┌─────────────────────────────────┐   │
    │  │  PostHog Python │──────│  Server-side event capture      │   │
    │  │  SDK            │      │  (transactions, subscriptions)   │   │
    │  └─────────────────┘      └─────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  PostHog Cloud  │
                  │  (us.posthog.com)│
                  └─────────────────┘

**Key architectural decisions:**

1. **Reverse Proxy**: All PostHog requests route through your domain (``/ph/*``) to bypass ad blockers that block ``posthog.com`` requests
2. **Dual Tracking**: Frontend SDK captures user interactions; backend SDK captures server-side events like payments and subscriptions
3. **User Linking**: Both frontend and backend identify users with the same ``distinct_id`` (user ID) for unified analytics

Environment Configuration
-------------------------

PostHog requires API keys to be configured in your environment. Add these to your ``.env`` file:

.. code-block:: bash

    # Backend (Django)
    POSTHOG_API_KEY=phc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    POSTHOG_HOST=https://us.i.posthog.com

    # Frontend (React)
    VITE_PUBLIC_POSTHOG_KEY=phc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

**Finding your API key:**

1. Log in to `PostHog <https://app.posthog.com>`_
2. Go to Project Settings → Project API Key
3. Copy the key (starts with ``phc_``)

**Regional endpoints:**

- US Cloud: ``https://us.i.posthog.com`` (default)
- EU Cloud: ``https://eu.i.posthog.com``
- Self-hosted: Your own PostHog instance URL

**Development vs Production:**

The template initializes PostHog differently based on environment:

- **Development**: Debug mode enabled for console logging
- **Production**: Full tracking enabled, debug disabled

If no API key is provided, PostHog is disabled automatically—no tracking occurs.

Frontend Setup
--------------

The React frontend uses a context provider to initialize PostHog and make it available throughout the app.

PostHog Provider
^^^^^^^^^^^^^^^^

Located at ``apps/{project_slug}/src/features/analytics/contexts/posthog-context.tsx``:

.. code-block:: tsx

    import { type ReactNode, createContext, useContext, useEffect } from 'react';
    import posthog from 'posthog-js';

    interface PostHogContextType {
      posthog: typeof posthog;
    }

    const PostHogContext = createContext<PostHogContextType | null>(null);

    export function PostHogProvider({ children }: { children: ReactNode }) {
      useEffect(() => {
        const apiKey = import.meta.env.VITE_PUBLIC_POSTHOG_KEY;

        if (apiKey) {
          posthog.init(apiKey, {
            api_host: '/ph',              // Reverse proxy path
            ui_host: 'https://us.i.posthog.com',
            person_profiles: 'always',    // Create person profiles for all users
            capture_pageview: true,       // Auto-capture page views
            capture_pageleave: true,      // Track when users leave pages
            disable_session_recording: true, // Disabled by default (see below)
            loaded: (posthog) => {
              if (import.meta.env.DEV) {
                posthog.debug();          // Enable debug logging in dev
              }
            },
          });
        }
      }, []);

      return (
        <PostHogContext.Provider value={{ posthog }}>
          {children}
        </PostHogContext.Provider>
      );
    }

    export function usePostHog() {
      const context = useContext(PostHogContext);
      if (!context) {
        throw new Error('usePostHog must be used within a PostHogProvider');
      }
      return context;
    }

**Key initialization options:**

- ``api_host: '/ph'``: Routes requests through your reverse proxy
- ``ui_host``: Where the PostHog UI is hosted (for toolbar/heatmap overlays)
- ``person_profiles: 'always'``: Creates profiles for anonymous users too
- ``capture_pageview: true``: Automatically tracks page views on navigation
- ``capture_pageleave: true``: Tracks time spent on pages

App Integration
^^^^^^^^^^^^^^^

The provider wraps your app in ``App.tsx``:

.. code-block:: tsx

    import { PostHogProvider } from '@/features/analytics';
    import { QueryClientProvider } from '@tanstack/react-query';
    import { AuthProvider } from '@/features/auth';

    function App() {
      return (
        <PostHogProvider>
          <QueryClientProvider client={queryClient}>
            <AuthProvider>
              {/* Your app content */}
            </AuthProvider>
          </QueryClientProvider>
        </PostHogProvider>
      );
    }

Backend Setup
-------------

The Django backend provides server-side analytics for events that shouldn't rely on client-side JavaScript.

Django Settings
^^^^^^^^^^^^^^^

In ``config/settings/base.py``:

.. code-block:: python

    # PostHog Analytics
    POSTHOG_API_KEY = env("POSTHOG_API_KEY", default="")
    POSTHOG_HOST = env("POSTHOG_HOST", default="https://us.i.posthog.com")

Analytics Module
^^^^^^^^^^^^^^^^

Located at ``{project_slug}/core/analytics.py``:

.. code-block:: python

    """PostHog analytics integration for server-side tracking."""

    from typing import TYPE_CHECKING
    import posthog
    from django.conf import settings

    if TYPE_CHECKING:
        from {project_slug}.users.models import User

    # Initialize PostHog client
    if settings.POSTHOG_API_KEY:
        posthog.api_key = settings.POSTHOG_API_KEY
        posthog.host = settings.POSTHOG_HOST
        posthog.debug = settings.DEBUG
    else:
        posthog.disabled = True


    def identify_user(user: "User") -> None:
        """Identify a user in PostHog with their properties."""
        if posthog.disabled or not user.is_authenticated:
            return

        posthog.identify(
            distinct_id=str(user.id),
            properties={
                "email": user.email,
                "name": user.name if hasattr(user, "name") else "",
            },
        )


    def capture_event(
        user: "User",
        event_name: str,
        properties: dict | None = None,
    ) -> None:
        """Capture a custom event for a user."""
        if posthog.disabled:
            return

        distinct_id = str(user.id) if user.is_authenticated else "anonymous"
        posthog.capture(
            distinct_id=distinct_id,
            event=event_name,
            properties=properties or {},
        )


    def shutdown() -> None:
        """Flush and shut down PostHog client gracefully."""
        if not posthog.disabled:
            posthog.shutdown()

**When to use server-side tracking:**

- Payment completions and subscription changes
- Background task completions
- Events that must be recorded even if the user closes the browser
- Sensitive events that shouldn't be visible in browser network tab

Reverse Proxy Configuration
---------------------------

Ad blockers commonly block requests to ``posthog.com`` domains. The reverse proxy routes PostHog traffic through your own domain, making it indistinguishable from your regular API calls.

Django Proxy View
^^^^^^^^^^^^^^^^^

Located at ``{project_slug}/core/views.py``:

.. code-block:: python

    """Reverse proxy for PostHog to avoid ad blockers."""

    import httpx
    from django.http import HttpRequest, HttpResponse
    from django.views.decorators.csrf import csrf_exempt

    POSTHOG_ENDPOINTS = {
        "default": "https://us.i.posthog.com",
        "assets": "https://us-assets.i.posthog.com",
    }


    @csrf_exempt
    def posthog_proxy(request: HttpRequest, path: str = "") -> HttpResponse:
        """
        Proxy requests from /ph/* to PostHog's US cloud endpoints.
        Static assets go to us-assets.i.posthog.com, everything else
        to us.i.posthog.com.
        """
        if path.startswith("static/"):
            target_host = POSTHOG_ENDPOINTS["assets"]
        else:
            target_host = POSTHOG_ENDPOINTS["default"]

        target_url = f"{target_host}/{path}"

        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in ("host", "content-length")
        }
        headers["Host"] = target_host.replace("https://", "")

        with httpx.Client(timeout=30.0) as client:
            try:
                response = client.request(
                    method=request.method or "GET",
                    url=target_url,
                    headers=headers,
                    content=request.body if request.body else None,
                    params=request.GET.dict() if request.GET else None,
                )
            except httpx.RequestError as e:
                return HttpResponse(
                    content=f"Proxy error: {e}",
                    status=502,
                    content_type="text/plain",
                )

        return HttpResponse(
            content=response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "application/json"),
        )

URL Configuration
^^^^^^^^^^^^^^^^^

In ``config/urls.py``:

.. code-block:: python

    from {project_slug}.core.views import posthog_proxy

    urlpatterns = [
        # ... other patterns
        path("ph/<path:path>", posthog_proxy, name="posthog_proxy"),
        path("ph/", posthog_proxy, {"path": ""}, name="posthog_proxy_root"),
    ]

Vite Development Proxy
^^^^^^^^^^^^^^^^^^^^^^

During development, Vite's dev server also needs to proxy PostHog requests. In ``apps/{project_slug}/vite.config.ts``:

.. code-block:: typescript

    export default defineConfig({
      // ... other config
      server: {
        proxy: {
          '/ph/static': {
            target: 'https://us-assets.i.posthog.com',
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/ph/, ''),
          },
          '/ph': {
            target: 'https://us.i.posthog.com',
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/ph/, ''),
          },
        },
      },
    });

**Why separate static routing?** PostHog serves JavaScript assets from a different subdomain (``us-assets.i.posthog.com``) than its API (``us.i.posthog.com``). The proxy handles both.

Automatic Tracking: Page Views & Sessions
-----------------------------------------

With ``capture_pageview: true`` and ``capture_pageleave: true``, PostHog automatically tracks:

**Page Views:**

- URL path and query parameters
- Referrer information
- UTM parameters (campaign tracking)
- Device and browser information

**Page Leave Events:**

- Time spent on page
- Scroll depth (how far user scrolled)
- Exit URL

**Sessions:**

PostHog automatically groups events into sessions:

- A session starts when a user first visits
- Sessions end after 30 minutes of inactivity
- All events within a session are linked together

**Viewing in PostHog:**

1. **Web Analytics Dashboard**: Overview of page views, sessions, and top pages
2. **Insights → Trends**: Custom charts for page view patterns
3. **Insights → Paths**: Visualize user navigation flows
4. **Insights → Funnels**: Track conversion through multi-step flows

User Identification
-------------------

User identification links anonymous activity to known users, enabling person-level analytics.

Frontend Identification
^^^^^^^^^^^^^^^^^^^^^^^

In the auth context (``features/auth/contexts/auth-context.tsx``):

.. code-block:: typescript

    import posthog from 'posthog-js';

    export function AuthProvider({ children }: { children: ReactNode }) {
      const { data: user } = useQuery({
        ...usersMeRetrieveOptions(),
        retry: false,
      });

      // Identify user in PostHog when authenticated
      useEffect(() => {
        if (user) {
          posthog.identify(String(user.id), {
            email: user.email,
            // Add any other properties you want to track
          });
        }
      }, [user]);

      const logout = () => {
        // Reset PostHog identity on logout
        posthog.reset();
        window.location.href = '/accounts/logout/';
      };

      // ... rest of provider
    }

**Key functions:**

- ``posthog.identify(id, properties)``: Links current session to a user ID
- ``posthog.reset()``: Clears user identity (important for shared devices)

Backend Identification
^^^^^^^^^^^^^^^^^^^^^^

For server-side events:

.. code-block:: python

    from {project_slug}.core.analytics import identify_user, capture_event

    def on_user_login(user):
        """Called when user logs in."""
        identify_user(user)
        capture_event(user, "user_logged_in")

**Properties to track:**

- ``email``: For identifying users in PostHog UI
- ``name``: Display name
- ``plan``: Subscription tier (for segmentation)
- ``company``: For B2B analytics
- Custom properties relevant to your app

Custom Event Tracking
---------------------

Beyond automatic page views, track specific user actions to understand product usage.

Frontend Events
^^^^^^^^^^^^^^^

Using the PostHog SDK directly:

.. code-block:: typescript

    import posthog from 'posthog-js';

    // Track button click
    function handlePurchase(productId: string, price: number) {
      posthog.capture('purchase_completed', {
        product_id: productId,
        price: price,
        currency: 'USD',
      });
    }

    // Track feature usage
    function handleFeatureUse(featureName: string) {
      posthog.capture('feature_used', {
        feature: featureName,
        timestamp: new Date().toISOString(),
      });
    }

    // Track form submission
    function handleFormSubmit(formName: string, success: boolean) {
      posthog.capture('form_submitted', {
        form: formName,
        success: success,
      });
    }

Using the ``usePostHog`` hook:

.. code-block:: tsx

    import { usePostHog } from '@/features/analytics';

    function MyComponent() {
      const { posthog } = usePostHog();

      const handleClick = () => {
        posthog.capture('button_clicked', { button: 'cta_hero' });
      };

      return <button onClick={handleClick}>Get Started</button>;
    }

Backend Events
^^^^^^^^^^^^^^

.. code-block:: python

    from {project_slug}.core.analytics import capture_event

    def complete_subscription(user, plan):
        """Called when user subscribes."""
        capture_event(
            user,
            "subscription_created",
            {
                "plan": plan.name,
                "price": float(plan.price),
                "billing_period": plan.billing_period,
            },
        )

    def process_payment(user, payment):
        """Called when payment is processed."""
        capture_event(
            user,
            "payment_processed",
            {
                "amount": float(payment.amount),
                "currency": payment.currency,
                "payment_method": payment.method,
            },
        )

Event Naming Conventions
^^^^^^^^^^^^^^^^^^^^^^^^

Use consistent, descriptive event names:

- Use ``snake_case`` for event names
- Start with a verb: ``clicked``, ``viewed``, ``submitted``, ``completed``
- Be specific: ``signup_form_submitted`` not just ``form_submitted``
- Group related events: ``checkout_started``, ``checkout_completed``, ``checkout_abandoned``

Session Replays & Heatmaps
--------------------------

Session replays let you watch how users interact with your app. Heatmaps visualize click patterns and scroll depth.

Enabling Session Recording
^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, session recording is disabled to minimize data collection. To enable it:

1. **Update PostHog initialization** in ``posthog-context.tsx``:

.. code-block:: typescript

    posthog.init(apiKey, {
      api_host: '/ph',
      ui_host: 'https://us.i.posthog.com',
      // Remove or set to false:
      disable_session_recording: false,
      // Optional: configure what gets recorded
      session_recording: {
        maskAllInputs: true,           // Mask input field values
        maskTextSelector: '.sensitive', // Mask elements with this class
      },
    });

2. **Enable in PostHog dashboard**: Go to Settings → Session Recording and enable recording.

Recording Options
^^^^^^^^^^^^^^^^^

Control what gets recorded for privacy:

.. code-block:: typescript

    posthog.init(apiKey, {
      session_recording: {
        // Privacy controls
        maskAllInputs: true,           // Replace input values with ***
        maskTextSelector: '.pii',       // Mask specific elements
        maskInputOptions: {
          password: true,
          email: true,
        },

        // Performance controls
        recordCrossOriginIframes: false,
        captureConsole: false,          // Don't record console logs
      },
    });

Heatmaps
^^^^^^^^

Heatmaps are automatically generated from session recordings and click events. No additional configuration needed—once recordings are enabled, heatmaps appear in the PostHog toolbar.

**Viewing heatmaps:**

1. Go to your site with PostHog toolbar enabled
2. Click the PostHog icon → Heatmap
3. View click density across the page

Privacy Considerations
^^^^^^^^^^^^^^^^^^^^^^

Session recordings capture user screens. Consider:

- **Mask sensitive data**: Use ``maskTextSelector`` for PII
- **Get consent**: Add a cookie banner for GDPR compliance
- **Limit recording**: Use ``session_recording.sampleRate`` to record a percentage of sessions
- **Review retention**: Configure data retention in PostHog settings

Feature Flags
-------------

Feature flags let you roll out features gradually and run A/B tests without deploying new code.

Creating a Feature Flag
^^^^^^^^^^^^^^^^^^^^^^^

1. Go to PostHog → Feature Flags → New Feature Flag
2. Set a key (e.g., ``new-checkout-flow``)
3. Configure rollout (percentage, user properties, etc.)
4. Save the flag

Frontend Usage
^^^^^^^^^^^^^^

Check if a flag is enabled:

.. code-block:: typescript

    import posthog from 'posthog-js';

    // Simple boolean check
    if (posthog.isFeatureEnabled('new-checkout-flow')) {
      return <NewCheckout />;
    }
    return <OldCheckout />;

    // With callback (for async flag loading)
    posthog.onFeatureFlags(() => {
      if (posthog.isFeatureEnabled('new-checkout-flow')) {
        setShowNewCheckout(true);
      }
    });

    // Get flag payload (for multivariate flags)
    const variant = posthog.getFeatureFlag('checkout-button-color');
    // Returns: 'blue' | 'green' | 'red' | false

React hook pattern:

.. code-block:: typescript

    import { useState, useEffect } from 'react';
    import posthog from 'posthog-js';

    function useFeatureFlag(flagKey: string): boolean | undefined {
      const [enabled, setEnabled] = useState<boolean | undefined>(undefined);

      useEffect(() => {
        // Check immediately if flags are loaded
        const value = posthog.isFeatureEnabled(flagKey);
        if (value !== undefined) {
          setEnabled(value);
        }

        // Also listen for flag changes
        posthog.onFeatureFlags(() => {
          setEnabled(posthog.isFeatureEnabled(flagKey) ?? false);
        });
      }, [flagKey]);

      return enabled;
    }

    // Usage
    function MyComponent() {
      const showNewFeature = useFeatureFlag('new-feature');

      if (showNewFeature === undefined) {
        return <Loading />;
      }

      return showNewFeature ? <NewFeature /> : <OldFeature />;
    }

Backend Usage
^^^^^^^^^^^^^

.. code-block:: python

    import posthog

    def get_pricing_page(request):
        """Show different pricing based on feature flag."""
        if posthog.feature_enabled(
            'new-pricing',
            str(request.user.id),
            person_properties={'email': request.user.email},
        ):
            return render(request, 'pricing_new.html')
        return render(request, 'pricing_old.html')

A/B Testing Example
^^^^^^^^^^^^^^^^^^^

1. **Create multivariate flag** in PostHog with variants: ``control``, ``variant_a``, ``variant_b``

2. **Implement in code:**

.. code-block:: typescript

    const variant = posthog.getFeatureFlag('checkout-experiment');

    switch (variant) {
      case 'variant_a':
        return <CheckoutWithTestimonials />;
      case 'variant_b':
        return <CheckoutWithTrustBadges />;
      default:
        return <CheckoutControl />;
    }

3. **Track conversion:** PostHog automatically correlates events with flag variants. Set a "Goal" in the experiment to track conversion.

Privacy & GDPR Compliance
-------------------------

PostHog provides tools for privacy compliance:

User Consent
^^^^^^^^^^^^

Disable tracking until consent is given:

.. code-block:: typescript

    // Initialize in opt-out mode
    posthog.init(apiKey, {
      opt_out_capturing_by_default: true,
    });

    // When user consents
    function handleConsentGiven() {
      posthog.opt_in_capturing();
    }

    // When user withdraws consent
    function handleConsentWithdrawn() {
      posthog.opt_out_capturing();
    }

Person Profile Modes
^^^^^^^^^^^^^^^^^^^^

Control how person profiles are created:

.. code-block:: typescript

    posthog.init(apiKey, {
      // 'always' - create profiles for anonymous users
      // 'identified_only' - only for identified users
      // 'never' - no person profiles
      person_profiles: 'identified_only',
    });

Data Retention
^^^^^^^^^^^^^^

Configure in PostHog dashboard:

1. Go to Settings → Data Management
2. Set retention period for events
3. Configure automatic anonymization

Summary
-------

**Key files:**

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Purpose
     - Location
   * - PostHog Provider (frontend)
     - ``apps/{project_slug}/src/features/analytics/contexts/posthog-context.tsx``
   * - User identification
     - ``apps/{project_slug}/src/features/auth/contexts/auth-context.tsx``
   * - Backend analytics
     - ``{project_slug}/core/analytics.py``
   * - Reverse proxy view
     - ``{project_slug}/core/views.py``
   * - Django settings
     - ``config/settings/base.py``
   * - URL routing
     - ``config/urls.py``
   * - Vite dev proxy
     - ``apps/{project_slug}/vite.config.ts``

**Quick reference:**

- Page views: Automatic with ``capture_pageview: true``
- Custom events: ``posthog.capture('event_name', { properties })``
- User identification: ``posthog.identify(userId, { email })``
- Session replays: Set ``disable_session_recording: false``
- Feature flags: ``posthog.isFeatureEnabled('flag-key')``

.. seealso::

   - `PostHog Documentation <https://posthog.com/docs>`_
   - `PostHog JavaScript SDK <https://posthog.com/docs/libraries/js>`_
   - `PostHog Python SDK <https://posthog.com/docs/libraries/python>`_
   - `Feature Flags Guide <https://posthog.com/docs/feature-flags>`_
   - `Session Recording Guide <https://posthog.com/docs/session-replay>`_
