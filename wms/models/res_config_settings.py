# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_stock_vertical_lift_kardex = fields.Boolean(
        string="Vertical Lift Using Kardex"
    )
    module_stock_putaway_rule = fields.Boolean(
        string="Configurable Put-Away Rules"
    )
    module_stock_putaway_recursive = fields.Boolean(
        string="Recursive Put-Away rules"
    )
    module_stock_putaway_abc = fields.Boolean(
        string="ABC chaotic storage Put-Away"
    )
    module_stock_move_location_dest_constraint_empty = fields.Boolean(
        string="Put-Away Constraint: Empty bin"
    )
    module_stock_move_location_dest_constraint_tag = fields.Boolean(
        string="Put-Away Constraint: Tags Matching"
    )
    module_stock_picking_completion_info = fields.Boolean(
        string="Show Operations completion details"
    )
    module_stock_picking_type_routing_operation = fields.Boolean(
        string="Route extra operation depending on source location"
    )
    module_stock_reserve_rule = fields.Boolean(
        string="Configure reservation rules by location"
    )
