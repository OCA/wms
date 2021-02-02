# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def to_float(val):
    if isinstance(val, float):
        return val
    if val:
        return float(val)
    return None
