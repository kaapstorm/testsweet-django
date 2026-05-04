"""Tests that exercise the code shown in docs/tutorial.md.

Each scenario in the tutorial is reproduced here verbatim, then
extended with assertions that confirm the documented behavior — the
fixtures are visible inside their scope, and writes don't leak
between methods or between tests.
"""
from contextlib import contextmanager

from django.contrib.auth.models import User

from testsweet import test
from testsweet_django import TestCase, savepoint


# --- Function-scoped fixture with savepoint() -----------------------

@contextmanager
def user_fixture():
    with savepoint():
        user = User.objects.create(username='graham', password='Passw0rd!')
        yield user


@test
def tutorial_func_fixture_yields_user():
    with user_fixture() as user:
        graham = User.objects.get(username='graham')
        assert user == graham


@test
def tutorial_func_fixture_rolls_back():
    # Outside the fixture's savepoint, the row must not exist —
    # neither from this test nor from tutorial_func_fixture_yields_user.
    assert not User.objects.exists()
    with user_fixture():
        assert User.objects.filter(username='graham').exists()
    assert not User.objects.exists()


# --- Class-scoped fixture with TestCase -----------------------------

@test
class TutorialClassFixture(TestCase):
    def __enter__(self):
        self = super().__enter__()
        self.user = User.objects.create(username='john', password='Passw0rd!')
        return self

    @contextmanager
    def __test_context__(self):
        with super().__test_context__():
            terry = User.objects.create(username='terry', password='Passw0rd!')
            yield

    def check_class_context(self):
        # john was created in __enter__ and is visible here.
        assert User.objects.filter(username='john').exists()

    def check_method_context(self):
        # terry was created in __test_context__ for this method.
        assert User.objects.filter(username='terry').exists()

    def check_method_writes_dont_leak(self):
        # If check_class_context's write of an extra row had leaked
        # past its per-method savepoint we'd see it here. Use a
        # method-local sentinel to make the intent explicit.
        assert not User.objects.filter(username='tutorial-leak').exists()
        User.objects.create(username='tutorial-leak')

    def check_method_writes_dont_leak_followup(self):
        assert not User.objects.filter(username='tutorial-leak').exists()
        # Class-scope user is still around across methods.
        assert User.objects.filter(username='john').exists()


@test
def tutorial_class_fixture_rolled_back_after_class():
    # By the time this top-level test runs, the class above has
    # finished and its __exit__ rolled back the class-scope savepoint.
    assert not User.objects.filter(username='john').exists()
    assert not User.objects.filter(username='terry').exists()
