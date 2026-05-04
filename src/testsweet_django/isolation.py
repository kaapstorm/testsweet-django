"""Opt-in per-test transaction rollback for test isolation."""
from contextlib import AbstractContextManager, contextmanager
from typing import Iterator

from django.db import transaction


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
