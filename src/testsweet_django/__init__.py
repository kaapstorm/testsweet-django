"""Django plugin for testsweet.

Provides ``session()`` and ``unit(name)`` for the testsweet plugin
protocol, plus user-facing ``savepoint()`` and ``TestCase`` for opt-in
per-test transaction rollback.
"""
from testsweet_django.isolation import TestCase, savepoint
from testsweet_django.plugin import session, unit

__all__ = ['TestCase', 'savepoint', 'session', 'unit']
