"""
    sphinx.ext.autodoc.mock
    ~~~~~~~~~~~~~~~~~~~~~~~

    mock for autodoc

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import contextlib
import os
import sys
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from types import FunctionType, MethodType, ModuleType

from sphinx.util import logging

if False:
    # For type annotation
    from typing import Any, Generator, Iterator, List, Sequence, Tuple, Union  # NOQA

logger = logging.getLogger(__name__)


class _MockObject:
    """Used by autodoc_mock_imports."""

    __display_name__ = '_MockObject'

    def __new__(cls, *args, **kwargs):
        # type: (Any, Any) -> Any
        if len(args) == 3 and isinstance(args[1], tuple):
            superclass = args[1][-1].__class__
            if superclass is cls:
                # subclassing MockObject
                return _make_subclass(args[0], superclass.__display_name__,
                                      superclass=superclass, attributes=args[2])

        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        # type: (Any, Any) -> None
        self.__qualname__ = ''

    def __len__(self):
        # type: () -> int
        return 0

    def __contains__(self, key):
        # type: (str) -> bool
        return False

    def __iter__(self):
        # type: () -> Iterator
        return iter([])

    def __mro_entries__(self, bases):
        # type: (Tuple) -> Tuple
        return (self.__class__,)

    def __getitem__(self, key):
        # type: (str) -> _MockObject
        return _make_subclass(key, self.__display_name__, self.__class__)()

    def __getattr__(self, key):
        # type: (str) -> _MockObject
        return _make_subclass(key, self.__display_name__, self.__class__)()

    def __call__(self, *args, **kw):
        # type: (Any, Any) -> Any
        if args and type(args[0]) in [FunctionType, MethodType]:
            # Appears to be a decorator, pass through unchanged
            return args[0]
        return self

    def __repr__(self):
        # type: () -> str
        return self.__display_name__


def _make_subclass(name, module, superclass=_MockObject, attributes=None):
    # type: (str, str, Any, dict) -> Any
    attrs = {'__module__': module, '__display_name__': module + '.' + name}
    attrs.update(attributes or {})

    return type(name, (superclass,), attrs)


class _MockModule(ModuleType):
    """Used by autodoc_mock_imports."""
    __file__ = os.devnull

    def __init__(self, name):
        # type: (str) -> None
        super().__init__(name)
        self.__all__ = []  # type: List[str]
        self.__path__ = []  # type: List[str]

    def __getattr__(self, name):
        # type: (str) -> _MockObject
        return _make_subclass(name, self.__name__)()

    def __repr__(self):
        # type: () -> str
        return self.__name__


class MockLoader(Loader):
    """A loader for mocking."""
    def __init__(self, finder):
        # type: (MockFinder) -> None
        super().__init__()
        self.finder = finder

    def create_module(self, spec):
        # type: (ModuleSpec) -> ModuleType
        logger.debug('[autodoc] adding a mock module as %s!', spec.name)
        self.finder.mocked_modules.append(spec.name)
        return _MockModule(spec.name)

    def exec_module(self, module):
        # type: (ModuleType) -> None
        pass  # nothing to do


class MockFinder(MetaPathFinder):
    """A finder for mocking."""

    def __init__(self, modnames):
        # type: (List[str]) -> None
        super().__init__()
        self.modnames = modnames
        self.loader = MockLoader(self)
        self.mocked_modules = []  # type: List[str]

    def find_spec(self, fullname, path, target=None):
        # type: (str, Sequence[Union[bytes, str]], ModuleType) -> ModuleSpec
        for modname in self.modnames:
            # check if fullname is (or is a descendant of) one of our targets
            if modname == fullname or fullname.startswith(modname + '.'):
                return ModuleSpec(fullname, self.loader)

        return None

    def invalidate_caches(self):
        # type: () -> None
        """Invalidate mocked modules on sys.modules."""
        for modname in self.mocked_modules:
            sys.modules.pop(modname, None)


@contextlib.contextmanager
def mock(modnames):
    # type: (List[str]) -> Generator[None, None, None]
    """Insert mock modules during context::

        with mock(['target.module.name']):
            # mock modules are enabled here
            ...
    """
    try:
        finder = MockFinder(modnames)
        sys.meta_path.insert(0, finder)
        yield
    finally:
        sys.meta_path.remove(finder)
        finder.invalidate_caches()
