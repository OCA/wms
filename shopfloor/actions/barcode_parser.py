# Copyright 2025 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component

from ..actions.search import SearchAction


class BarcodeResult:

    __slots__ = ("type", "value", "raw")

    def __init__(self, **kw) -> None:
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


class BarcodeParser(Component):
    """
    Some barcodes can have complex data structure
    """

    _name = "shopfloor.barcode.parser"
    _inherit = "shopfloor.process.action"
    _usage = "barcode"

    def __init__(self, search_action: SearchAction):
        # Get search action keys
        self.search_action = search_action

    @property
    def _authorized_barcode_types(self):
        return self.search_action._barcode_type_handler.keys()

    def parse(self, barcode, types) -> list[BarcodeResult]:
        """
        This method will parse the barcode and return the
        value with its type if determined.

        Override this to implement specific parsing

        """

        return [BarcodeResult(type="unknown", value=barcode, raw=barcode)]
