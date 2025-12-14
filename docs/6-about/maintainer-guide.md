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
- `template/.nvmrc`
- `template/requirements/local.txt`

## Template testing

### Copier Python API

Template tests use the [Copier Python API](https://copier.readthedocs.io/) directly:

```python
# tests/test_copier_generation.py
from copier import run_copy

def test_project_generation(template_path, tmp_path, context):
    """Test template generation with default options."""
    run_copy(str(template_path), str(tmp_path), data=context, unsafe=True, vcs_ref="HEAD")
    assert tmp_path.is_dir()

def test_generation_with_celery(template_path, tmp_path, context):
    """Test template generation with Celery enabled."""
    context["use_celery"] = True
    run_copy(str(template_path), str(tmp_path), data=context, unsafe=True, vcs_ref="HEAD")
    assert (tmp_path / "config" / "celery_app.py").exists()

def test_generation_without_drf(template_path, tmp_path, context):
    """Test template generation without DRF."""
    context["use_drf"] = False
    run_copy(str(template_path), str(tmp_path), data=context, unsafe=True, vcs_ref="HEAD")
    assert not (tmp_path / "config" / "api_router.py").exists()
```

The `template_path` and `context` fixtures are defined in `conftest.py`.

### Matrix testing

We test multiple option combinations to catch interaction bugs. The CI runs tests across:

- **Operating systems**: Ubuntu, Windows, macOS
- **Feature combinations**: Default, Celery, async, Heroku

Example parametrized test:

```python
import pytest

@pytest.mark.parametrize("use_celery,use_async,use_heroku", [
    (False, False, False),  # Defaults
    (True, False, False),   # With Celery
    (False, True, False),   # With async
    (False, False, True),   # With Heroku
    (True, True, False),    # Celery + async
])
def test_combinations(template_path, tmp_path, context, use_celery, use_async, use_heroku):
    context.update({
        "use_celery": use_celery,
        "use_async": use_async,
        "use_heroku": use_heroku,
    })
    run_copy(str(template_path), str(tmp_path), data=context, unsafe=True, vcs_ref="HEAD")
    assert tmp_path.is_dir()
```

### Conditional file exclusion testing

Copier uses `_exclude` patterns in `copier.yaml` to conditionally exclude files. Tests verify this behavior:

```python
def test_celery_files_excluded_when_disabled(template_path, tmp_path, context):
    """Verify Celery files are excluded when use_celery=False."""
    context["use_celery"] = False
    run_copy(str(template_path), str(tmp_path), data=context, unsafe=True, vcs_ref="HEAD")

    # These files should be excluded by _exclude patterns in copier.yaml
    assert not (tmp_path / "config" / "celery_app.py").exists()
    assert not (tmp_path / "docker" / "local" / "django" / "celery").exists()

def test_post_generation_generates_secrets(template_path, tmp_path, context):
    """Verify post_generation.py generates random secrets in .env."""
    run_copy(str(template_path), str(tmp_path), data=context, unsafe=True, vcs_ref="HEAD")
    env_file = tmp_path / ".env"
    content = env_file.read_text()

    # Secret should be present and not a placeholder
    assert "DJANGO_SECRET_KEY=" in content
    assert "{{" not in content  # No unexpanded template vars
```

## Template updates with Copier

This template uses [Copier](https://copier.readthedocs.io/) for template management with built-in update support:

```bash
# In a generated project, update to the latest template version
copier update --trust

# Apply a specific template version
copier update --trust --vcs-ref v2.0.0
```

Copier stores template metadata in `.copier-answers.yml`, including the template URL and the commit hash used to generate the project.

**For maintainers**: When making breaking changes, consider using Copier's [migration scripts](https://copier.readthedocs.io/en/stable/migrations/) feature to handle upgrades automatically.
