Django plugin for Testsweet
===========================

Adds a `testsweet.plugins` entry point that:

* Sets up and tears down the Django test database for the run.
* Provides `savepoint()` and `TestCase` context managers that wrap test
  code in a transaction which is rolled back on exit, so tests using
  the database don't leak state.

## Install

```
pip install testsweet-django
```

## Usage

Set `DJANGO_SETTINGS_MODULE` before invoking testsweet:

```
DJANGO_SETTINGS_MODULE=myproject.settings testsweet
```

Inside tests, opt in to the database via `savepoint()` or by inheriting
`TestCase`:

```python
from testsweet import test
from testsweet_django import TestCase, savepoint


@test
def example():
    with savepoint():
        ...


@test
class Example(TestCase):
    def check_something(self):
        ...
```

See [`docs/tutorial.md`](docs/tutorial.md) for a walkthrough.
