from contextlib import contextmanager

from django.contrib.auth.models import User

import testsweet_django
from testsweet import catch_exceptions, test
from testsweet._plugins import Plugin
from testsweet_django import TestCase, savepoint, session, unit


@test
class PluginConformance:
    def module_satisfies_plugin_protocol(self):
        # testsweet's load_plugins() runs isinstance(plugin, Plugin)
        # at startup; failing this check means the plugin won't load.
        assert isinstance(testsweet_django, Plugin)

    def session_returns_context_manager(self):
        cm = session()
        assert hasattr(cm, '__enter__')
        assert hasattr(cm, '__exit__')

    def unit_returns_context_manager(self):
        cm = unit('some.test')
        assert hasattr(cm, '__enter__')
        assert hasattr(cm, '__exit__')

    def unit_is_a_noop(self):
        with unit('some.test'):
            pass

    def session_actually_set_up_the_database(self):
        # If session() didn't run setup_databases(), the auth_user
        # table wouldn't exist and every other test in this file
        # would have failed with OperationalError. Assert the schema
        # is present explicitly so the implicit dependency is named.
        from django.db import connection
        tables = connection.introspection.table_names()
        assert 'auth_user' in tables


@test
class SavepointBehavior:
    def writes_are_rolled_back(self):
        before = User.objects.count()
        with savepoint():
            User.objects.create(username='sp-x')
            assert User.objects.filter(username='sp-x').exists()
        assert User.objects.count() == before
        assert not User.objects.filter(username='sp-x').exists()

    def nested_savepoints_isolate_inner_writes(self):
        before = User.objects.count()
        with savepoint():
            User.objects.create(username='sp-outer')
            with savepoint():
                User.objects.create(username='sp-inner')
                assert User.objects.count() == before + 2
            # Inner savepoint rolled back; outer's row remains.
            assert User.objects.filter(username='sp-outer').exists()
            assert not User.objects.filter(username='sp-inner').exists()
        # Outer rolled back too.
        assert User.objects.count() == before

    def exception_inside_savepoint_still_rolls_back(self):
        before = User.objects.count()
        with catch_exceptions() as excs:
            with savepoint():
                User.objects.create(username='sp-doomed')
                raise RuntimeError('boom')
        assert len(excs) == 1
        assert isinstance(excs[0], RuntimeError)
        assert User.objects.count() == before


@test
class TestCaseClassScope(TestCase):
    def __enter__(self):
        self = super().__enter__()
        self.class_user = User.objects.create(username='tc-class')
        return self

    def class_scope_user_is_visible(self):
        assert User.objects.filter(username='tc-class').exists()

    def writes_made_in_first_method(self):
        # __test_context__ provides a per-method savepoint, so this
        # write must not leak into writes_dont_leak_into_next_method.
        User.objects.create(username='tc-leak')
        assert User.objects.filter(username='tc-leak').exists()

    def writes_dont_leak_into_next_method(self):
        assert not User.objects.filter(username='tc-leak').exists()
        # Class-scope user is still visible across methods.
        assert User.objects.filter(username='tc-class').exists()


@test
class TestCaseSubclassChain(TestCase):
    @contextmanager
    def __test_context__(self):
        with super().__test_context__():
            User.objects.create(username='tc-chain')
            yield

    def subclass_test_context_creates_user(self):
        # Created inside the nested savepoint; visible within the
        # method.
        assert User.objects.filter(username='tc-chain').count() == 1

    def previous_methods_chain_user_was_rolled_back(self):
        # If the previous method's tc-chain hadn't rolled back, this
        # method's __test_context__ would create a second one and we'd
        # see count == 2.
        assert User.objects.filter(username='tc-chain').count() == 1
