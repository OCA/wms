# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class ShopFloorPrintingAction(Component):
    """Base Component for actions"""

    _name = "shopfloor.reception.printing.action"
    _inherit = "shopfloor.printing.action"
    _collection = "shopfloor.printing"
    _usage = "reception"
