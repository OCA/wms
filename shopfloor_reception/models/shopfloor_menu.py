# Copyright 2025 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models

FILTER_TODAY_SCHEDULED_PICKINGS_HELP = """
By default, at first step, filter the available
pickings with the ones that are scheduled for today.
"""


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    filter_today_scheduled_pickings_is_possible = fields.Boolean(
        compute="_compute_filter_today_scheduled_pickings_is_possible"
    )
    filter_today_scheduled_pickings = fields.Boolean(
        default=False,
        help=FILTER_TODAY_SCHEDULED_PICKINGS_HELP,
    )

    @api.depends("scenario_id")
    def _compute_filter_today_scheduled_pickings_is_possible(self):
        for menu in self:
            menu.filter_today_scheduled_pickings_is_possible = bool(
                menu.scenario_id.has_option("allow_filter_today_scheduled_pickings")
            )

    @api.onchange("filter_today_scheduled_pickings_is_possible")
    def onchange_filter_today_scheduled_pickings_is_possible(self):
        self.filter_today_scheduled_pickings = (
            self.filter_today_scheduled_pickings_is_possible
        )

    @api.constrains("scenario_id", "picking_type_ids", "allow_move_create")
    def _check_filter_today_scheduled_pickings(self):
        for menu in self:
            if (
                menu.filter_today_scheduled_pickings
                and not menu.filter_today_scheduled_pickings_is_possible
            ):
                raise exceptions.ValidationError(
                    _("Filter Today Pickings is not allowed for menu {}.").format(
                        menu.name
                    )
                )
