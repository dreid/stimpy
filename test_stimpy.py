from twisted.trial import unittest

from mock import Mock
from stimpy import Statebox

def mockClock(maxTime=10):
    clock = Mock()

    returns = range(maxTime)
    def side_effect():
        return returns.pop(0)

    clock.side_effect = side_effect
    return clock


class StateboxTestCase(unittest.TestCase):
    def test_defaults(self):
        sb = Statebox(_clock=mockClock())
        self.assertEquals(sb.queue, [])
        self.assertEquals(sb.value, None)
        self.assertEquals(sb.last_modified, 0)


    def test_serializeEmpty(self):
        sb = Statebox(_clock=mockClock())
        self.assertEquals(sb.serialize(sort_keys=True),
            '{"last_modified": 0, "queue": [], "value": null}')


    def test_modifyValue(self):
        sb = Statebox(set(), _clock=mockClock())
        sb.modify(set.add, "foo")
        self.assertEquals(sb.value, set(["foo"]))
        self.assertEquals(sb.queue, [(1, set.add, ("foo",), {})])


    def test_mergeBoxes(self):
        clock = mockClock()
        sb1 = Statebox(set(), _clock=clock)
        sb2 = Statebox(set(), _clock=clock)

        sb1.modify(set.add, "foo")
        sb2.modify(set.add, "bar")
        sb1.modify(set.add, "baz")

        sb1.merge(sb2)

        self.assertEquals(sb1.value, set(["foo", "bar", "baz"]))
        self.assertEquals(sorted(sb1.queue),
            [(2, set.add, ("foo",), {}),
             (3, set.add, ("bar",), {}),
             (4, set.add, ("baz",), {})
            ])


    def test_serializeOps(self):
        sb = Statebox(set(), _clock=mockClock())
        sb.modify(set.add, "foo")

        self.assertEquals(sb.serialize(sort_keys=True),
            ('{"last_modified": 1, "queue": [[1, "__builtin__.set.add", ["foo"], {}]], '
             '"value": {"__set__": ["foo"]}}'))


    def test_unseralizeOps(self):
        sb = Statebox.unserialize(
            ('{"last_modified": 1, "queue": '
             '[[1, "__builtin__.set.add", ["foo"], {}]], '
             '"value": {"__set__": ["foo"]}}'))

        self.assertEquals(sb.value, set(["foo"]))
        self.assertEquals(sb.last_modified, 1)
        self.assertEquals(sb.queue, [(1, set.add, ["foo"], {})])
