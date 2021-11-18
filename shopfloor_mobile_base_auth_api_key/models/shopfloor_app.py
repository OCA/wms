# Copyright 2021 Camptcamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ShopfloorApp(models.Model):

    # TODO: consider splitting this to new module shopfloor_base_auth_api_key
    _inherit = "shopfloor.app"

    def _selection_auth_type(self):
        return super()._selection_auth_type() + [("api_key", "API key")]

    # Borrowed from `endpoint_auth_api_key`: shall we define a mixin?
    auth_api_key_group_ids = fields.Many2many(
        comodel_name="auth.api.key.group",
        string="Allowed API key groups",
    )

    def _allowed_api_key_ids(self):
        return self.auth_api_key_group_ids.auth_api_key_ids.ids

    def action_manage_api_key_groups(self):
        xid = "auth_api_key_group.auth_api_key_group_act_window"
        action = self.env["ir.actions.act_window"]._for_xml_id(xid)
        action["domain"] = [("id", "in", self.auth_api_key_group_ids.ids)]
        return action
