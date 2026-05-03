"""Django plugin for testsweet.

Provides ``session()`` and ``unit(name)`` for the testsweet plugin
protocol, plus user-facing ``savepoint()`` and ``TestCase`` for opt-in
per-test transaction rollback.
"""
import os
import warnings
from contextlib import AbstractContextManager, contextmanager
from typing import Iterator

import django
from django.conf import settings
from django.db import transaction
from django.test.utils import (
    setup_databases,
    setup_test_environment,
    teardown_databases,
    teardown_test_environment,
)

__all__ = ['TestCase', 'savepoint', 'session', 'unit']


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


@contextmanager
def savepoint() -> Iterator[None]:
    """Wrap the block in a transaction that is rolled back on exit.

    Outermost calls open a real transaction; nested calls become
    savepoints. Either way, all writes inside the block are reverted
    when the block exits — whether normally or via exception.
    """
    with transaction.atomic():
        try:
            yield
        finally:
            transaction.set_rollback(True)


class TestCase(AbstractContextManager):
    """Class-scope rollback fixture for ``@test`` classes.

    Inherit from ``TestCase`` to wrap the entire class lifecycle in a
    ``savepoint()``. ``__test_context__`` opens a nested savepoint per
    method, so per-method writes are rolled back without losing
    class-level setup.
    """

    def __enter__(self):
        self._savepoint = savepoint()
        self._savepoint.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        return self._savepoint.__exit__(exc_type, exc, tb)

    @contextmanager
    def __test_context__(self):
        with savepoint():
            yield
