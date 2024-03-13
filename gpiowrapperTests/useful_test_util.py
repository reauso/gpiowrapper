import unittest
from contextlib import contextmanager


class ExtendedTestCase(unittest.TestCase):
    @contextmanager
    def assertNotRaised(self, exc_type=Exception):
        try:
            yield None
        except exc_type as e:
            raise self.failureException(f'{type(e).__name__} (subclass of {exc_type.__name__}) raised')
