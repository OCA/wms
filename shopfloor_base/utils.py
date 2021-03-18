# -*- coding: utf-8 -*-
# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
# @author Simone Orsi <simahawk@gmail.com>
from functools import wraps


def ensure_model(model_name):
    """Decorator to ensure data method is called w/ the right recordset."""

    def _ensure_model(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            # 1st arg is `self`
            record = args[1]
            if record is not None:
                assert record._name == model_name, "Expected model: {}. Got: {}".format(
                    model_name, record._name
                )
            return func(*args, **kwargs)

        return wrapped

    return _ensure_model


class DotDict(dict):
    """Helper for dot.notation access to dictionary attributes

        E.g.
          foo = DotDict({'bar': False})
          return foo.bar
    """

    def __getattr__(self, attrib):
        val = self.get(attrib)
        return DotDict(val) if type(val) is dict else val
