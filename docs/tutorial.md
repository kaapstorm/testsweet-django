# testsweet-django tutorial

This tutorial walks through the two patterns testsweet-django gives
you for keeping database state out of each other's way: the
`savepoint()` context manager for one-off blocks, and the `TestCase`
base class for class-scoped fixtures. Both rely on the same
underlying mechanism — a transaction that is rolled back on exit —
so writes inside a test never reach the next test.

Before any of this works, set `DJANGO_SETTINGS_MODULE` so testsweet's
session hook can call `django.setup()` and create the test database:

```
DJANGO_SETTINGS_MODULE=myproject.settings testsweet
```

## A function-scoped fixture with `savepoint()`

`savepoint()` opens a transaction (or a nested savepoint, if one is
already open) and rolls it back when the block exits. That makes it a
natural building block for fixture context managers:

```python
from contextlib import contextmanager

from django.contrib.auth.models import User

from testsweet import test
from testsweet_django import savepoint


@contextmanager
def user_fixture():
    with savepoint():
        user = User.objects.create(username='graham', password='Passw0rd!')
        yield user


@test
def example_func_with_model_fixture():
    with user_fixture() as user:
        graham = User.objects.get(username='graham')
        assert user == graham
    assert not User.objects.exists()
```

## A class-scoped fixture with `TestCase`

When several test methods need to share setup, inherit from
`TestCase`. The class itself is a context manager: testsweet enters
it once around the whole class, so anything you build in `__enter__`
lives for the lifetime of every method on the class.

`TestCase` also implements `__test_context__`, which testsweet enters
*per method*. The base implementation opens a nested savepoint, so
each method's writes are rolled back without disturbing the
class-scope state.

```python
from contextlib import contextmanager

from django.contrib.auth.models import User

from testsweet import test
from testsweet_django import TestCase


@test
class ExampleClassWithModelFixture(TestCase):
    def __enter__(self):
        self = super().__enter__()
        self.user = User.objects.create(username='john', password='Passw0rd!')
        return self

    @contextmanager
    def __test_context__(self):
        with super().__test_context__():
            User.objects.create(username='terry', password='Passw0rd!')
            yield

    def check_class_context(self):
        assert User.objects.filter(username='john').exists()

    def check_method_context(self):
        assert User.objects.filter(username='terry').exists()
```

What happens when testsweet runs this class:

1. `__enter__` runs once. `super().__enter__()` opens the
   class-scope savepoint, then `john` is created inside it.
2. For each method, `__test_context__` runs. `super().__test_context__()`
   opens a *nested* savepoint, then `terry` is created inside it.
3. The method body runs. Both `john` and `terry` are visible.
4. `__test_context__` exits — the nested savepoint rolls back, so
   `terry` and any writes the method made vanish. `john` is
   untouched.
5. After every method, `__exit__` runs. The class-scope savepoint
   rolls back, taking `john` with it.

## Choosing between the two

- One test, one fixture: write a `@contextmanager` that uses
  `savepoint()` and call it inline.
- Several tests, shared setup: subclass `TestCase`. Use `__enter__`
  for class-scope state and override `__test_context__` for
  per-method state.

If a test never touches the database, you don't need either — the
plugin's per-test hook is a no-op, so opt-in is a deliberate choice
rather than a default.
