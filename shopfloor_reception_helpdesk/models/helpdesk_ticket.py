# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HelpdeskTicket(models.Model):

    _inherit = "helpdesk.ticket"

    is_shopfloor_created = fields.Boolean()
