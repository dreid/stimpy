"""
STatebox In My PYthon.
"""

json = None
try:
    import simplejson
    json = simplejson
except ImportError:
    import json as stdjson
    json = stdjson

import time
import inspect
from twisted.python.reflect import namedAny
from twisted.python.reflect import fullyQualifiedName as txFullyQualifiedName

def fullyQualifiedName(obj):
    if inspect.ismethoddescriptor(obj):
        objclass = fullyQualifiedName(obj.__objclass__)

        return '%s.%s' % (objclass, obj.__name__)
    return txFullyQualifiedName(obj)


def statebox_object_hook(dct):
    if '__set__' in dct:
        return set(dct['__set__'])

    return dct


def statebox_default_encoder(obj):
    if isinstance(obj, set):
        return {'__set__': list(obj)}

    return obj


class Statebox(object):
    def __init__(self, value=None, last_modified=None, queue=None,
                 _clock=time.time):
        self._clock = _clock

        if last_modified is None:
            last_modified = self._clock()

        if queue is None:
            queue = []

        self._value = value
        self._last_modified = last_modified
        self._queue = queue


    def modify(self, op, *args, **kwargs):
        self._last_modified = now = self._clock()
        self._queue.append((now, op, args, kwargs))
        op(self._value, *args, **kwargs)


    def merge(self, *boxes):
        new_queue = []
        new_queue.extend(self._queue)

        for box in boxes:
            new_queue.extend(box.queue)

        for (t, op, args, kwargs) in sorted(new_queue):
            op(self._value, *args, **kwargs)

        self._queue = new_queue


    def expire(self, age):
        for op in self._queue:
            (t, _op, _args, _kwargs) = op
            if self._last_modified - age > t:
                self._queue.remove(op)


    def truncate(self, count):
        self._queue = list(sorted(self._queue))[:count]


    @property
    def last_modified(self):
        return self._last_modified


    @property
    def value(self):
        return self._value


    @property
    def queue(self):
        return self._queue


    @classmethod
    def unserialize(klass, json_str, _clock=time.time, **loadKwargs):
        raw = json.loads(json_str,
                         object_hook=statebox_object_hook, **loadKwargs)

        return klass(raw['value'], raw['last_modified'],
                     [(t, namedAny(op), args, kwargs)
                      for (t, op, args, kwargs) in raw['queue']],
                     _clock=_clock)


    def serialize(self, **dumpKwargs):
        return json.dumps({
            'value': self.value,
            'queue': [(t, fullyQualifiedName(op), args, kwargs)
                        for (t, op, args, kwargs) in self._queue],
            'last_modified': self.last_modified
        }, default=statebox_default_encoder, **dumpKwargs)
