import os
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
    if not os.environ.get('DJANGO_SETTINGS_MODULE') and not settings.configured:
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
def unit(name: str) -> Iterator[None]:
    # No per-test isolation: tests opt in via savepoint()/TestCase.
    yield


@contextmanager
def savepoint() -> Iterator[None]:
    with transaction.atomic():
        try:
            yield
        finally:
            transaction.set_rollback(True)


class TestCase(AbstractContextManager):

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
