# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import models
from odoo.tools.safe_eval import safe_eval


class ShopfloorApp(models.Model):
    _inherit = "shopfloor.app"

    def action_open_app_logs(self):
        xid = "shopfloor_rest_log.action_shopfloor_log"
        action = self.env["ir.actions.act_window"]._for_xml_id(xid)
        domain = safe_eval(action["domain"])
        domain.append(("collection_id", "=", self.id))
        action["domain"] = domain
        return action
