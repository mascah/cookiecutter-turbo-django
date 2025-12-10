import logging

from django.contrib.staticfiles.management.commands import collectstatic
from django.core.management import call_command
from django.core.management.base import CommandError

logger = logging.getLogger(__name__)


class Command(collectstatic.Command):
    """
    Extends Django's collectstatic command to also build Tailwind CSS.

    This ensures that Tailwind CSS is built before collecting static files,
    making it available for deployment.
    """

    def handle(self, *args, **options):
        """Build Tailwind CSS and then collect static files."""
        verbosity = options.get("verbosity", 1)

        if verbosity >= 1:
            self.stdout.write("Building Tailwind CSS...")

        try:
            call_command("tailwind", "build")
            if verbosity >= 1:
                self.stdout.write(
                    self.style.SUCCESS("✓ Tailwind CSS built successfully"),
                )
        except CommandError as e:
            self.stderr.write(
                self.style.ERROR(f"Failed to build Tailwind CSS: {e}"),
            )
            raise
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f"Unexpected error building Tailwind CSS: {e}",
                ),
            )
            raise

        # Now run the standard collectstatic
        if verbosity >= 1:
            self.stdout.write("Collecting static files...")

        super().handle(*args, **options)
