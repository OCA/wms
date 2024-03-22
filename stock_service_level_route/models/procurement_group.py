# Copyright 2024 Foodles (https://www.foodles.co)
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models
from odoo.osv import expression


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def _get_rule_domain(self, location, values):
        domain = super()._get_rule_domain(location, values)
        service_level_domain = []
        if service_level := values.get("service_level_id"):
            service_level_domain = [
                ("route_id.service_level_ids", "=", service_level),
                ("route_id.service_level_selectable", "=", True),
            ]
        else:
            service_level_domain = [
                ("route_id.service_level_selectable", "=", True),
                ("route_id.service_level_ids", "=", False),
            ]
        service_level_domain = expression.OR(
            [service_level_domain, [("route_id.service_level_selectable", "=", False)]]
        )
        domain = expression.AND([domain, service_level_domain])
        return domain
