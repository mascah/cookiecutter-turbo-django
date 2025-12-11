# Maintainer guide

This document is intended for maintainers of the template.

## Automated updates

We use Dependabot to keep dependencies up-to-date, including Python packages, GitHub actions, npm packages, and Docker images.

## GitHub Actions workflows

### CI

`ci.yml`

The CI workflow runs on pushes to main and on pull requests. It covers two main aspects:

- **Tests job**: Runs pytest across Ubuntu, Windows, and macOS to validate template generation works correctly on all platforms.
- **Docker job**: Builds and tests Docker configurations for both the basic setup and with Celery enabled.

### Issue manager

`issue-manager.yml`

Uses [tiangolo/issue-manager](https://github.com/tiangolo/issue-manager) to automatically close issues and pull requests after a delay when labeled appropriately.

Runs daily at 00:12 UTC, and also triggers on issue comments, issue labeling, and PR labeling.

Configured labels and their behavior (all with 10-day delay):

| Label | Message |
|-------|---------|
| `answered` | Assuming the question was answered, this will be automatically closed now. |
| `solved` | Assuming the original issue was solved, it will be automatically closed now. |
| `waiting` | Automatically closing after waiting for additional info. To re-open, please provide the additional information requested. |
| `wontfix` | As discussed, we won't be implementing this. Automatically closing. |

### UV lock regeneration

`dependabot-uv-lock.yml`

Automatically regenerates `uv.lock` when `pyproject.toml` changes in PRs from Dependabot or PyUp. This ensures the lock file stays in sync with dependency updates.

Triggers on:
- Pull requests that modify `pyproject.toml` (from dependabot[bot] or pyup-bot)
- Manual workflow dispatch

### Align versions

`align-versions.yml`

Keeps version numbers synchronized across the template when Dependabot updates certain files. Runs the `scripts/node_version.py` and `scripts/ruff_version.py` scripts to propagate version changes.

Triggers on Dependabot PRs that modify:
- `{{cookiecutter.project_slug}}/.nvmrc`
- `{{cookiecutter.project_slug}}/requirements/local.txt`

## Template testing

### pytest-cookies

Template tests use [pytest-cookies](https://github.com/hackebrot/pytest-cookies), a pytest plugin for testing Cookiecutter templates:

```python
# tests/test_cookiecutter_generation.py
def test_bake_with_defaults(cookies):
    """Test template generation with default options."""
    result = cookies.bake()
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project_path.is_dir()

def test_bake_with_celery(cookies):
    """Test template generation with Celery enabled."""
    result = cookies.bake(extra_context={"use_celery": "y"})
    assert result.exit_code == 0
    assert (result.project_path / "config" / "celery_app.py").exists()

def test_bake_without_drf(cookies):
    """Test template generation without DRF."""
    result = cookies.bake(extra_context={"use_drf": "n"})
    assert result.exit_code == 0
    assert not (result.project_path / "config" / "api_router.py").exists()
```

The `cookies` fixture handles template rendering in temporary directories.

### Matrix testing

We test multiple option combinations to catch interaction bugs. The CI runs tests across:

- **Operating systems**: Ubuntu, Windows, macOS
- **Feature combinations**: Default, Celery, async, Heroku

Example parametrized test:

```python
import pytest

@pytest.mark.parametrize("use_celery,use_async,use_heroku", [
    ("n", "n", "n"),  # Defaults
    ("y", "n", "n"),  # With Celery
    ("n", "y", "n"),  # With async
    ("n", "n", "y"),  # With Heroku
    ("y", "y", "n"),  # Celery + async
])
def test_combinations(cookies, use_celery, use_async, use_heroku):
    result = cookies.bake(extra_context={
        "use_celery": use_celery,
        "use_async": use_async,
        "use_heroku": use_heroku,
    })
    assert result.exit_code == 0
```

### Post-generation hook testing

The hooks (`hooks/pre_gen_project.py` and `hooks/post_gen_project.py`) are tested by examining the generated project:

```python
def test_hook_removes_celery_files_when_disabled(cookies):
    """Verify post_gen hook removes Celery files when use_celery=n."""
    result = cookies.bake(extra_context={"use_celery": "n"})

    # These files should be removed by post_gen_project.py
    assert not (result.project_path / "config" / "celery_app.py").exists()
    assert not (result.project_path / "docker" / "celery" / "worker" / "start").exists()

def test_hook_generates_secrets(cookies):
    """Verify post_gen hook generates random secrets in .env."""
    result = cookies.bake()
    env_file = result.project_path / ".envs" / ".local" / ".django"
    content = env_file.read_text()

    # Secret should be present and not a placeholder
    assert "DJANGO_SECRET_KEY=" in content
    assert "{{" not in content  # No unexpanded template vars
```

## Template version tracking

### cruft

[cruft](https://cruft.github.io/cruft/) helps users keep their generated projects in sync with template updates:

```bash
# In a generated project, check if updates are available
cruft check

# Apply template updates with conflict resolution
cruft update
```

cruft stores template metadata in `.cruft.json`, including the template URL and the commit hash used to generate the project.

**For maintainers**: When making breaking changes, consider documenting migration steps in release notes so users can manually resolve conflicts during `cruft update`.

### Copier alternative

[Copier](https://copier.readthedocs.io/) is an alternative to Cookiecutter with built-in update support and migration scripts. Consider migrating to Copier if:

- The template evolves frequently
- Users struggle with manual upgrade conflicts
- You need migration scripts between template versions

Copier's update flow:

```bash
# In a generated project
copier update

# Apply a specific template version
copier update --vcs-ref v2.0.0
```

The main advantage over cruft is Copier's native support for migrations—scripts that run during updates to handle breaking changes automatically.
