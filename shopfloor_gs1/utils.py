# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from biip import ParseError
from biip.gs1 import GS1Message

AI_MAPPING = {
    # https://www.gs1.org/standards/barcodes/application-identifiers
    # TODO: define other internal mappings by convention
    "01": "product",
    "10": "lot",
    "11": "production_date",
    "21": "serial",
}
AI_MAPPING_INV = {v: k for k, v in AI_MAPPING.items()}


class GS1Barcode:
    """TODO"""

    __slots__ = ("ai", "type", "code", "value", "raw_value")

    def __init__(self, **kw) -> None:
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: ai={self.ai} type={self.type}>"

    def __bool__(self):
        return self.type != "none" or bool(self.record)

    def __eq__(self, other):
        for k in self.__slots__:
            if not hasattr(other, k):
                return False
            if getattr(other, k) != getattr(self, k):
                return False
        return True

    @classmethod
    def parse(cls, barcode, ai_whitelist=None, ai_mapping=None):
        """TODO"""
        res = []
        try:
            # TODO: we might not get an HRI...
            parsed = GS1Message.parse_hri(barcode)
        except ParseError:
            parsed = None
        if not parsed:
            return res
        ai_mapping = ai_mapping or AI_MAPPING
        # Use whitelist if given, to respect a specific order
        ai_whitelist = ai_whitelist or ai_mapping.keys()
        for ai in ai_whitelist:
            record_type = ai_mapping[ai]
            found = parsed.get(ai=ai)
            if found:
                # when value is a date the datetime obj is in `date`
                # TODO: other types have their own special key
                value = found.date or found.value
                info = cls(
                    ai=ai,
                    type=record_type,
                    code=barcode,
                    raw_value=found.value,
                    value=value,
                )
                res.append(info)
        return res

    @classmethod
    def to_ai(cls, type_, safe=True):
        try:
            return AI_MAPPING_INV[type_]
        except KeyError:
            if not safe:
                raise ValueError(f"{type_} is not supported.")
            return None
