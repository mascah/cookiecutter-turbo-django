.. _template-options:

Project Generation Options
==========================

This page describes all the template options that will be prompted by the `Copier CLI`_ prior to generating your project.

.. _Copier CLI: https://copier.readthedocs.io/

project_name:
    Your project's human-readable name, capitals and spaces allowed.

project_slug:
    Your project's slug without dashes or spaces. Used to name your repo
    and in other places where a Python-importable version of your project name
    is needed.

description:
    Describes your project and gets used in places like ``README.rst`` and such.

author_name:
    This is you! The value goes into places like ``LICENSE`` and such.

email:
    The email address you want to identify yourself in the project.

username_type:
    The type of username you want to use in the project. This can be either
    ``username`` or ``email``. If you choose ``username``, the ``email`` field
    will be included. If you choose ``email``, the ``username`` field will be
    excluded. It is best practice to always include an email field, so there is
    no option for having just the ``username`` field.

domain_name:
    The domain name you plan to use for your project once it goes live.
    Note that it can be safely changed later on whenever you need to.

version:
    The version of the project at its inception.

open_source_license:
    A software license for the project. The choices are:

    1. MIT_
    2. BSD_
    3. GPLv3_
    4. `Apache Software License 2.0`_
    5. Not open source

timezone:
    The value to be used for the ``TIME_ZONE`` setting of the project.

mail_service:
    Select an email service that Django-Anymail provides

    1. Mailgun_
    2. `Amazon SES`_
    3. SendGrid_
    4. `Other SMTP`_

use_drf:
    Indicates whether the project should be configured to use `Django Rest Framework`_.

use_async:
    Indicates whether the project should use web sockets with Uvicorn + Gunicorn.

use_celery:
    Indicates whether the project should be configured to use Celery_.

use_mailpit:
    Indicates whether the project should be configured to use Mailpit_.

use_sentry:
    Indicates whether the project should be configured to use Sentry_.

use_whitenoise:
    Indicates whether the project should be configured to use WhiteNoise_.

use_heroku:
    Indicates whether the project should be configured so as to be deployable
    to Heroku_.

keep_local_envs_in_vcs:
    Indicates whether the project's ``.env.example`` file should be kept in VCS
    (comes in handy when working in teams where local environment
    reproducibility is strongly encouraged).

debug:
    Indicates whether the project should be configured for debugging.
    This option is relevant for template developers only.


.. _MIT: https://opensource.org/licenses/MIT
.. _BSD: https://opensource.org/licenses/BSD-3-Clause
.. _GPLv3: https://www.gnu.org/licenses/gpl.html
.. _Apache Software License 2.0: https://www.apache.org/licenses/LICENSE-2.0

.. _Amazon SES: https://aws.amazon.com/ses/
.. _Mailgun: https://www.mailgun.com
.. _SendGrid: https://sendgrid.com
.. _Other SMTP: https://anymail.readthedocs.io/en/stable/

.. _Django Rest Framework: https://github.com/encode/django-rest-framework/

.. _Celery: https://github.com/celery/celery

.. _Mailpit: https://github.com/axllent/mailpit

.. _Sentry: https://github.com/getsentry/sentry

.. _WhiteNoise: https://github.com/evansd/whitenoise

.. _Heroku: https://github.com/heroku/heroku-buildpack-python
