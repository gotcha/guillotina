from collections import UserDict
from guillotina import configure
from guillotina.db.orm.base import BaseObject
from guillotina.interfaces import IAnnotations
from guillotina.interfaces import IResource


class AnnotationData(BaseObject, UserDict):
    """
    store data on basic dictionary object but also inherit from base object
    """


@configure.adapter(
    for_=IResource,
    provides=IAnnotations)
class AnnotationsAdapter(object):
    """Store annotations on an object
    """

    def __init__(self, obj):
        self.obj = obj

    def get(self, key, default=None):
        """
        non-async variant
        """
        annotations = self.obj.__annotations__
        if key in annotations:
            return annotations[key]
        return default

    async def async_get(self, key, default=None):
        annotations = self.obj.__annotations__
        element = annotations.get(key, default)
        if element is None:
            # Get from DB
            if self.obj._p_jar is not None:
                try:
                    obj = await self.obj._p_jar.get_annotation(self.obj, key)
                except KeyError:
                    obj = None
                if obj:
                    annotations[key] = obj
        if key in annotations:
            return annotations[key]
        return default

    async def async_keys(self):
        return await self.obj._p_jar.get_annotation_keys(self.obj._p_oid)

    async def async_set(self, key, value):
        if not isinstance(value, BaseObject):
            raise KeyError('Not a valid object as annotation')
        annotations = self.obj.__annotations__
        value.id = key  # make sure id is set...
        annotations[key] = value
        value.__of__ = self.obj._p_oid
        value.__name__ = key
        # we register the value
        value._p_jar = self.obj._p_jar
        value._p_jar.register(value)

    async def async_del(self, key):
        raise NotImplemented()
