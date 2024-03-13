import sys
import unittest
from unittest.mock import patch, MagicMock

from parameterized import parameterized

from gpiowrapper.util import IndexableProperty, RequiresOptionalImport, replace_none_in_slice, \
    subtract_offset_from_slice
from gpiowrapperTests.useful_test_util import ExtendedTestCase


class IndexablePropertyUser:
    def __init__(self, array):
        self._my_list = array

    @IndexableProperty
    def my_property(self, item):
        return self._my_list[item]

    @my_property.itemsetter
    def my_property(self, key, value):
        self._my_list[key] = value


class IndexablePropertyTests(unittest.TestCase):
    def test_get_property__Always__ReturnsIndexablePropertyObject(self):
        # Arrange
        user = IndexablePropertyUser([i for i in range(100)])

        # Act
        actual = user.my_property

        # Assert
        self.assertIsInstance(actual, IndexableProperty)

    def test_set_property__Always__RaisesAttributeError(self):
        # Arrange
        user = IndexablePropertyUser([i for i in range(100)])

        # Act & Act
        with self.assertRaises(AttributeError):
            user.my_property = []

    def test_getitem__All__ReturnsCompleteList(self):
        # Arrange
        user = IndexablePropertyUser([i for i in range(100)])

        # Act
        actual = user.my_property[:]

        # Assert
        self.assertIsInstance(actual, list)
        self.assertListEqual(actual, [i for i in range(100)])

    def test_getitem__Sliced__ReturnsCompleteList(self):
        # Arrange
        user = IndexablePropertyUser([i for i in range(100)])

        # Act
        actual = user.my_property[10:40]

        # Assert
        self.assertIsInstance(actual, list)
        self.assertListEqual(actual, [i for i in range(10, 40)])

    def test_setitem__All__ReturnsCompleteList(self):
        # Arrange
        user = IndexablePropertyUser([i for i in range(100)])

        # Act
        user.my_property[:] = [1 for _ in range(100)]

        # Assert
        self.assertListEqual(user._my_list, [1 for _ in range(100)])

    def test_setitem__Sliced__ReturnsCompleteList(self):
        # Arrange
        user = IndexablePropertyUser([i for i in range(100)])

        # Act
        user.my_property[10:40] = [1 for _ in range(10, 40)]

        # Assert
        self.assertListEqual(user._my_list, [1 if 10 <= i < 40 else i for i in range(100)])


class RequiresOptionalImportTests(ExtendedTestCase):
    def setUp(self):
        if 'a' in sys.modules:
            sys.modules.pop('a')
        if 'b' in sys.modules:
            sys.modules.pop('b')
        if 'c' in sys.modules:
            sys.modules.pop('c')

    def test_ImportStatement__NotImportedAndUnused__NoError(self):
        # Arrange
        assert 'a' not in sys.modules[self.__module__].__dict__

        # Act & Assert
        with self.assertNotRaised():
            @RequiresOptionalImport(import_='a.b.c')
            def method_requires_import():
                pass

    @patch.dict(sys.modules[IndexablePropertyUser.__module__].__dict__, {'a': MagicMock()})
    def test_ImportStatement__ImportedAndUnused__NoError(self):
        # Arrange
        assert 'a' in sys.modules[self.__module__].__dict__

        # Act & Assert
        with self.assertNotRaised():
            @RequiresOptionalImport(import_='a.b.c')
            def method_requires_import():
                pass

    def test_ImportStatement__NotImportedAndUsed__RaisesRuntimeError(self):
        # Arrange
        msg = 'Test MSG'
        assert 'a' not in sys.modules[self.__module__].__dict__

        # Act & Assert
        with self.assertRaisesRegex(RuntimeError, msg):
            @RequiresOptionalImport(import_='a.b.c', msg=msg)
            def method_requires_import():
                pass

            method_requires_import()

    @patch.dict(sys.modules[IndexablePropertyUser.__module__].__dict__, {'a': MagicMock()})
    def test_ImportStatement__ImportedAndUsed__NoError(self):
        # Arrange
        assert 'a' in sys.modules[self.__module__].__dict__

        # Act
        with self.assertNotRaised():
            @RequiresOptionalImport(import_='a.b.c')
            def method_requires_import():
                pass

            method_requires_import()

    @patch.dict(sys.modules[IndexablePropertyUser.__module__].__dict__, {'a': MagicMock()})
    def test_FromImportStatement__NotImportedAndUnused__NoError(self):
        # Arrange
        assert 'd' not in sys.modules[self.__module__].__dict__

        # Act & Assert
        with self.assertNotRaised():
            @RequiresOptionalImport(from_='a.b.c', import_='d')
            def method_requires_import():
                pass

    @patch.dict(sys.modules[IndexablePropertyUser.__module__].__dict__, {'a': MagicMock, 'd': MagicMock()})
    def test_FromImportStatement__ImportedAndUnused__NoError(self):
        # Arrange
        assert 'd' in sys.modules[self.__module__].__dict__

        # Act & Assert
        with self.assertNotRaised():
            @RequiresOptionalImport(from_='a.b.c', import_='d')
            def method_requires_import():
                pass

    @patch.dict(sys.modules[IndexablePropertyUser.__module__].__dict__, {'a': MagicMock()})
    def test_FromImportStatement__NotImportedAndUsed__RaisesRuntimeError(self):
        # Arrange
        msg = 'Test MSG'
        assert 'd' not in sys.modules[self.__module__].__dict__

        # Act & Assert
        with self.assertRaisesRegex(RuntimeError, msg):
            @RequiresOptionalImport(from_='a.b.c', import_='d', msg=msg)
            def method_requires_import():
                pass

            method_requires_import()

    @patch.dict(sys.modules[IndexablePropertyUser.__module__].__dict__, {'a': MagicMock, 'd': MagicMock()})
    def test_FromImportStatement__ImportedAndUsed__NoError(self):
        # Arrange
        assert 'd' in sys.modules[self.__module__].__dict__

        # Act & Assert
        with self.assertNotRaised():
            @RequiresOptionalImport(from_='a.b.c', import_='d')
            def method_requires_import():
                pass

            method_requires_import()

    @patch.dict(sys.modules[IndexablePropertyUser.__module__].__dict__, {'d': MagicMock()})
    def test_FromImportAsStatement__NotImportedAndUnused__NoError(self):
        # Arrange
        assert 'e' not in sys.modules[self.__module__].__dict__

        # Act & Assert
        try:
            @RequiresOptionalImport(from_='a.b.c', import_='d', as_='e')
            def method_requires_import():
                pass
        except Exception as e:
            self.fail(f'Exception thrown! {e}')

    @patch.dict(sys.modules[IndexablePropertyUser.__module__].__dict__, {'d': MagicMock, 'e': MagicMock()})
    def test_FromImportAsStatement__ImportedAndUnused__NoError(self):
        # Arrange
        assert 'e' in sys.modules[self.__module__].__dict__

        # Act & Assert
        with self.assertNotRaised():
            @RequiresOptionalImport(from_='a.b.c', import_='d', as_='e')
            def method_requires_import():
                pass

    @patch.dict(sys.modules[IndexablePropertyUser.__module__].__dict__, {'d': MagicMock()})
    def test_FromImportAsStatement__NotImportedAndUsed__RaisesRuntimeError(self):
        # Arrange
        msg = 'Test MSG'
        assert 'e' not in sys.modules[self.__module__].__dict__

        # Act & Assert
        with self.assertRaisesRegex(RuntimeError, msg):
            @RequiresOptionalImport(from_='a.b.c', import_='d', as_='e', msg=msg)
            def method_requires_import():
                pass

            method_requires_import()

    @patch.dict(sys.modules[IndexablePropertyUser.__module__].__dict__, {'d': MagicMock, 'e': MagicMock()})
    def test_FromImportAsStatement__ImportedAndUsed__NoError(self):
        # Arrange
        assert 'e' in sys.modules[self.__module__].__dict__

        # Act & Assert
        with self.assertNotRaised():
            @RequiresOptionalImport(from_='a.b.c', import_='d', as_='e')
            def method_requires_import():
                pass

            method_requires_import()


class ReplaceNoneInSliceTests(unittest.TestCase):
    def test_replace_none_in_slice__AllNone__SliceOverAllElements(self):
        # Arrange
        item = slice(None, None, None)

        # Act
        new_item = replace_none_in_slice(item=item)

        # Assert
        self.assertEqual(new_item, slice(0, sys.maxsize, 1))

    def test_replace_none_in_slice__StartNone__SetStartToZero(self):
        # Arrange
        item = slice(None, 10, 2)

        # Act
        new_item = replace_none_in_slice(item=item)

        # Assert
        self.assertEqual(new_item, slice(0, 10, 2))

    def test_replace_none_in_slice__StopNone__SetStopToMaxsize(self):
        # Arrange
        item = slice(4, None, 2)

        # Act
        new_item = replace_none_in_slice(item=item)

        # Assert
        self.assertEqual(new_item, slice(4, sys.maxsize, 2))

    def test_replace_none_in_slice__StepNone__SetStepToOne(self):
        # Arrange
        item = slice(4, 30, None)

        # Act
        new_item = replace_none_in_slice(item=item)

        # Assert
        self.assertEqual(new_item, slice(4, 30, 1))


class AddOffsetToSliceTests(unittest.TestCase):
    @parameterized.expand([[slice(3, 6, 1)], [slice(-3, 13, 2)], [slice(13, -3, -1)], [slice(-13, -6, 1)]])
    def test_add_offset_to_slice__WithoutOffset__ReturnsUnchanged(self, item: slice):
        # Arrange
        offset = 0

        # Act
        new_item = subtract_offset_from_slice(item=item, offset=offset)

        # Assert
        self.assertEqual(new_item, item)

    def test_add_offset_to_slice__AllHigherThanOffset__ReturnsOffsetSubtracted(self):
        # Arrange
        item = slice(6, 30, 1)
        offset = 5

        # Act
        new_item = subtract_offset_from_slice(item=item, offset=offset)

        # Assert
        self.assertEqual(new_item, slice(1, 25, 1))

    def test_add_offset_to_slice__StartLowerThanOffset__ReturnsStartZero(self):
        # Arrange
        item = slice(3, 30, 1)
        offset = 5

        # Act
        new_item = subtract_offset_from_slice(item=item, offset=offset)

        # Assert
        self.assertEqual(new_item, slice(0, 25, 1))

    def test_add_offset_to_slice__StartStopLowerThanOffset__ReturnsStartStopZero(self):
        # Arrange
        item = slice(1, 4, 1)
        offset = 5

        # Act
        new_item = subtract_offset_from_slice(item=item, offset=offset)

        # Assert
        self.assertEqual(new_item, slice(0, 0, 1))

    def test_iadd_offset_to_slice__NegativeStart__ReturnsStartUnchanged(self):
        # Arrange
        item = slice(-1, 30, 1)
        offset = 5

        # Act
        new_item = subtract_offset_from_slice(item=item, offset=offset)

        # Assert
        self.assertEqual(new_item, slice(-1, 25, 1))

    def test_add_offset_to_slice__NegativeStop__ReturnsStopUnchanged(self):
        # Arrange
        item = slice(6, -5, 1)
        offset = 5

        # Act
        new_item = subtract_offset_from_slice(item=item, offset=offset)

        # Assert
        self.assertEqual(new_item, slice(1, -5, 1))

    def test_add_offset_to_slice__NegativeStartStop__ReturnsUnchanged(self):
        # Arrange
        item = slice(-6, -5, 1)
        offset = 5

        # Act
        new_item = subtract_offset_from_slice(item=item, offset=offset)

        # Assert
        self.assertEqual(new_item, slice(-6, -5, 1))