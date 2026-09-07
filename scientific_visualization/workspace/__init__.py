"""Data workspace: import, profile, clean, transform, analyze, visualize.

See README.md in this package for the architecture overview.
"""
try:
    import pandas as _pd
    # pandas >=3.0 defaults to inferring its new PyArrow-backed "str" dtype
    # for any string data, even after an explicit `.astype(object)` cast.
    # That dtype's `.str.*` accessor dispatches to PyArrow's RE2 regex
    # engine, which rejects patterns Python's `re` accepts (e.g. `\uXXXX`
    # escapes) and has other subtle behavioral differences. This package
    # does a lot of ad hoc string/regex work over arbitrary user data
    # (currency/percentage detection, text cleaning, column splitting, ...)
    # where predictable, classic Python-`re` semantics matter more than the
    # PyArrow backend's memory/speed benefits, so it's turned off once here
    # for the whole process rather than worked around at every call site.
    _pd.set_option("future.infer_string", False)
except ImportError:
    pass

# Importing this package registers every cleaning AND transform operation
# into cleaning.OPERATIONS (see cleaning.py's `@operation` decorator) --
# so callers never need to remember "also import transforms.py" just to
# make its operations resolvable by name in a pipeline.
from . import cleaning as _cleaning  # noqa: E402,F401
from . import transforms as _transforms  # noqa: E402,F401
