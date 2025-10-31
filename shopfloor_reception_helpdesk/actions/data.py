# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class DataAction(Component):

    _inherit = "shopfloor.data.action"

    def _get_picking_parser(self, record, **kw):
        parser = super()._get_picking_parser(record, **kw)
        if record.picking_type_id.allow_helpdesk_ticket:
            parser.append("helpdesk_ticket_allowed")
        return parser
