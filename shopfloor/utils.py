# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def to_float(val):
    if isinstance(val, float):
        return val
    if isinstance(val, int):
        return float(val)
    if isinstance(val, str):
        if val.replace(".", "", 1).isdigit():
            return float(val)
    return None
