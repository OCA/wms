# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):

    _inherit = "shopfloor.data.action"

    def _get_picking_parser(self, record, **kw):
        parser = super()._get_picking_parser(record, **kw)
        if record.picking_type_id.allow_helpdesk_ticket:
            parser.append("helpdesk_ticket_allowed")
        return parser

    @ensure_model("stock.helpdesk.ticket.create")
    def helpdesk_wizard(self, record, **kw):
        parser = self._helpdesk_wizard_parser
        data = self._jsonify(record, parser, **kw)
        return data

    @property
    def _helpdesk_wizard_parser(self):
        return [
            "id",
            "description",
            ("motive_id:motive", self._helpdesk_motive_parser),
        ]

    @property
    def _helpdesk_motive_parser(self):
        return ["id", "name"]
