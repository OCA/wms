from odoo import _, api, exceptions, fields, models


class ShopfloorMenu(models.Model):
    _name = "shopfloor.menu"
    _description = "Menu displayed in the scanner application"
    _order = "sequence"

    _scenario_allowing_create_moves = (
        "single_pack_transfer",
        "location_content_transfer",
    )

    name = fields.Char(translate=True)
    sequence = fields.Integer()
    profile_ids = fields.Many2many(
        "shopfloor.profile", string="Profiles", help="Visible for these profiles"
    )
    picking_type_ids = fields.Many2many(
        comodel_name="stock.picking.type", string="Operation Types", required=True
    )

    scenario = fields.Selection(selection="_selection_scenario", required=True)

    move_create_is_possible = fields.Boolean(compute="_compute_move_create_is_possible")
    # only available for some scenarios, move_create_is_possible defines if the option
    # can be used or not
    allow_move_create = fields.Boolean(
        string="Allow Move Creation",
        default=False,
        help="Some scenario may create move(s) when a product or package is"
        " scanned and no move already exists. Any new move is created in the"
        " selected operation type, so it can be active only when one type is selected.",
    )

    def _selection_scenario(self):
        return [
            # these must match a REST service's '_usage'
            ("single_pack_transfer", "Single Pack Transfer"),
            ("cluster_picking", "Cluster Picking"),
            ("checkout", "Checkout/Packing"),
            ("delivery", "Delivery"),
            ("location_content_transfer", "Location Content Transfer"),
        ]

    @api.depends("scenario", "picking_type_ids")
    def _compute_move_create_is_possible(self):
        for menu in self:
            menu.move_create_is_possible = bool(
                menu.scenario in self._scenario_allowing_create_moves
                and len(menu.picking_type_ids) == 1
            )

    @api.onchange("move_create_is_possible")
    def onchange_move_create_is_possible(self):
        self.allow_move_create = self.move_create_is_possible

    @api.constrains("scenario", "picking_type_ids", "allow_move_create")
    def _check_allow_move_create(self):
        for menu in self:
            if menu.allow_move_create and not menu.move_create_is_possible:
                raise exceptions.ValidationError(
                    _("Creation of moves is not allowed for menu {}.").format(menu.name)
                )
