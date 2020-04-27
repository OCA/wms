from odoo import fields, models


class ShopfloorMenu(models.Model):
    _name = "shopfloor.menu"
    _description = "Menu displayed in the scanner application"
    _order = "sequence"

    name = fields.Char(translate=True)
    sequence = fields.Integer()
    profile_ids = fields.Many2many(
        "shopfloor.profile", string="Profiles", help="Visible for these profiles"
    )
    picking_type_ids = fields.Many2many(
        comodel_name="stock.picking.type", string="Operation Types",
        required=True,
    )
    # TODO allow only one picking type when 'move creation' is allowed

    scenario = fields.Selection(selection="_selection_scenario", required=True)

    def _selection_scenario(self):
        return [
            # these must match a REST service's '_usage'
            ("single_pack_putaway", "Single Pack Put-away"),
            ("single_pack_transfer", "Single Pack Transfer"),
            ("cluster_picking", "Cluster Picking"),
            ("checkout", "Checkout/Packing"),
            ("delivery", "Delivery"),
        ]
