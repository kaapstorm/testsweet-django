from contextlib import contextmanager

from django.contrib.auth.models import User

from testsweet import test
from testsweet_django import TestCase, savepoint


@test
class ExampleClassWithModelFixture(TestCase):
    def __enter__(self):
        self = super().__enter__()
        self.user = User.objects.create(username='john', password='Passw0rd!')
        return self

    def __exit__(self, exc_type, exc, tb):
        self.user.delete()
        return super().__exit__(exc_type, exc, tb)

    @contextmanager
    def __test_context__(self):
        with super().__test_context__():
            terry = User.objects.create(username='terry', password='Passw0rd!')
            try:
                yield
            finally:
                terry.delete()

    def check_class_context(self):
        assert User.objects.filter(username='john').exists()

    def check_method_context(self):
        assert User.objects.filter(username='terry').exists()


@test
def example_func_with_model_fixture():
    with user_fixture() as user:
        graham = User.objects.get(username='graham')
        assert user == graham


@contextmanager
def user_fixture():
    with savepoint():
        user = User.objects.create(username='graham', password='Passw0rd!')
        try:
            yield user
        finally:
            user.delete()
