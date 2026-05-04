"""Testsweet plugin protocol hooks."""
import os
import warnings
from contextlib import contextmanager
from typing import Iterator

import django
from django.conf import settings
from django.test.utils import (
    setup_databases,
    setup_test_environment,
    teardown_databases,
    teardown_test_environment,
)


@contextmanager
def session() -> Iterator[None]:
    """Set up and tear down the Django test database for the test run.

    Calls ``django.setup()`` and ``setup_databases()`` on entry, and
    the matching teardown on exit.

    If ``DJANGO_SETTINGS_MODULE`` is unset and Django settings are not
    already configured, emits a warning and yields without setting up
    the database. This keeps testsweet runs in non-Django projects
    from blowing up just because the plugin is installed, but it also
    means a misconfigured Django run silently loses DB isolation —
    the warning surfaces that case.
    """
    if not os.environ.get('DJANGO_SETTINGS_MODULE') and not settings.configured:
        warnings.warn(
            'testsweet-django: DJANGO_SETTINGS_MODULE is unset and '
            'Django is not configured; skipping test-database setup. '
            'savepoint() and TestCase will not provide isolation.',
            RuntimeWarning,
            stacklevel=2,
        )
        yield
        return
    django.setup()
    setup_test_environment()
    old_config = setup_databases(verbosity=0, interactive=False)
    try:
        yield
    finally:
        teardown_databases(old_config, verbosity=0)
        teardown_test_environment()


@contextmanager
def unit(_name: str) -> Iterator[None]:
    """No-op per-test hook required by the testsweet plugin protocol.

    testsweet-django doesn't auto-wrap every test in a transaction;
    isolation is opt-in via ``savepoint()`` and ``TestCase``. The
    ``_name`` argument is required by the protocol but unused here.
    """
    yield
