# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from biip import ParseError
from biip.gs1 import GS1Message

from .config import MAPPING_AI_TO_TYPE

DEFAULT_AI_WHITELIST = tuple(MAPPING_AI_TO_TYPE.keys())


class GS1Barcode:
    """GS1 barcode parser and wrapper."""

    __slots__ = ("ai", "code", "value", "raw_value")

    def __init__(self, **kw) -> None:
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: ai={self.ai}>"

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
    def parse(cls, barcode, ai_whitelist=None, safe=True):
        """Parse given barcode

        :param barcode: valid GS1 barcode
        :param ai_whitelist: ordered list of AI to look for
        :param safe: break or not if barcode is invalid

        :return: an instance of `GS1Barcode`.
        """
        res = []
        try:
            # TODO: we might not get an HRI...
            parsed = GS1Message.parse_hri(barcode)
        except ParseError:
            if not safe:
                raise
            parsed = None
        if not parsed:
            return res
        # Use whitelist if given, to respect a specific order
        ai_whitelist = ai_whitelist or DEFAULT_AI_WHITELIST
        for ai in ai_whitelist:
            found = parsed.get(ai=ai)
            if found:
                # when value is a date the datetime obj is in `date`
                # TODO: other types have their own special key
                value = found.date or found.value
                info = cls(
                    ai=ai,
                    code=barcode,
                    raw_value=found.value,
                    value=value,
                )
                res.append(info)
        return res
