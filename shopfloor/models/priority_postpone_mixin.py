# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class PriorityPostponeMixin(models.AbstractModel):
    _name = "shopfloor.priority.postpone.mixin"
    _description = "Adds shopfloor priority/postpone fields"

    # shopfloor_priority is set to this value when postponed
    # consider it as the max value for priority
    _SF_PRIORITY_POSTPONED = 9999
    _SF_PRIORITY_DEFAULT = 10

    shopfloor_priority = fields.Integer(
        default=lambda self: self._SF_PRIORITY_DEFAULT,
        copy=False,
        help="Technical field. Overrides operation priority in barcode scenario.",
    )

    shopfloor_postponed = fields.Boolean(
        compute="_compute_shopfloor_postponed",
        inverse="_inverse_shopfloor_postponed",
        help="Technical field. "
        "Indicates if the operation has been postponed in a barcode scenario.",
    )

    @api.depends("shopfloor_priority")
    def _compute_shopfloor_postponed(self):
        for record in self:
            record.shopfloor_postponed = bool(
                record.shopfloor_priority == self._SF_PRIORITY_POSTPONED
            )

    def _inverse_shopfloor_postponed(self):
        for record in self:
            if record.shopfloor_postponed:
                record.shopfloor_priority = self._SF_PRIORITY_POSTPONED
            else:
                record.shopfloor_priority = self._SF_PRIORITY_DEFAULT
