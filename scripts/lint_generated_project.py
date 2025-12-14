#!/usr/bin/env python3
"""
Pre-commit hook to lint the generated Copier template.

Generates the template with default options, runs ruff check on the
generated project, and exits with non-zero if linting fails.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RESET = "\033[0m"


def main() -> int:
    """Generate template and run ruff check."""
    root_dir = Path(__file__).parent.parent

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        print(f"{YELLOW}Generating template with default options...{RESET}")

        env = os.environ.copy()
        env["COPIER_TEST_MODE"] = "1"

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"""
from copier import run_copy
run_copy(
    '{root_dir}',
    '{output_dir}',
    unsafe=True,
    vcs_ref='HEAD',
)
""",
                ],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )

            if result.returncode != 0:
                print(f"{RED}Failed to generate template:{RESET}")
                print(result.stderr)
                return 1

        except Exception as e:
            print(f"{RED}Error generating template: {e}{RESET}")
            return 1

        generated_dirs = list(output_dir.iterdir())
        if not generated_dirs:
            print(f"{RED}No project was generated{RESET}")
            return 1

        # Copier generates directly in output_dir, not in a subdirectory
        project_dir = output_dir
        print(f"{GREEN}Generated project in: {project_dir}{RESET}")

        print(f"{YELLOW}Running ruff check...{RESET}")

        try:
            result = subprocess.run(
                ["ruff", "check", "."],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                print(f"{RED}Ruff check failed:{RESET}")
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                return 1

            print(f"{GREEN}Ruff check passed!{RESET}")
            return 0

        except FileNotFoundError:
            print(f"{RED}ruff not found. Install with: uv sync{RESET}")
            return 1
        except Exception as e:
            print(f"{RED}Error running ruff: {e}{RESET}")
            return 1


if __name__ == "__main__":
    sys.exit(main())
