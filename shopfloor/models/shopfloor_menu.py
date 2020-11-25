# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models

from odoo.addons.base_sparse_field.models.fields import Serialized


class ShopfloorMenu(models.Model):
    _name = "shopfloor.menu"
    _description = "Menu displayed in the scanner application"
    _order = "sequence"

    _scenario_allowing_create_moves = (
        "single_pack_transfer",
        "location_content_transfer",
    )

    _scenario_allowing_unreserve_other_moves = (
        "single_pack_transfer",
        "location_content_transfer",
    )

    _scenario_allowing_ignore_no_putaway_available = (
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
    # TODO: `options` field allows to provide custom options for the scenario,
    # (or for any other kind of service).
    # Developers should probably have a way to register scenario and their options
    # which will be computed in this field at the end.
    # This would allow to get rid of hardcoded settings like
    # `_scenario_allowing_create_moves` or `_scenario_allowing_unreserve_other_moves`.
    # For now is not included in any view as it should be customizable by scenario.
    # Maybe we can have a wizard accessible via a button on the menu tree view.
    # There's no automation here. Developers are responsible for their usage
    # and/or their exposure to the scenario api.
    options = Serialized(default={})

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
    unreserve_other_moves_is_possible = fields.Boolean(
        compute="_compute_unreserve_other_moves_is_possible"
    )
    allow_unreserve_other_moves = fields.Boolean(
        string="Allow to process reserved quantities",
        default=False,
        help="If you tick this box, this scenario will allow operator to move"
        " goods even if a reservation is made by a different operation type.",
    )
    ignore_no_putaway_available_is_possible = fields.Boolean(
        compute="_compute_ignore_no_putaway_available_is_possible"
    )
    ignore_no_putaway_available = fields.Boolean(
        string="Ignore transfers when no put-away is available",
        default=False,
        help="If you tick this box, the transfer is reserved only "
        "if the put-away can find a sublocation (when putaway destination "
        "is different from the operation type's destination).",
    )
    active = fields.Boolean(default=True)

    def _selection_scenario(self):
        return [
            # these must match a REST service's '_usage'
            ("single_pack_transfer", "Single Pack Transfer"),
            ("zone_picking", "Zone Picking"),
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

    @api.depends("scenario", "picking_type_ids")
    def _compute_unreserve_other_moves_is_possible(self):
        for menu in self:
            menu.unreserve_other_moves_is_possible = (
                menu.scenario in self._scenario_allowing_unreserve_other_moves
            )

    @api.onchange("unreserve_other_moves_is_possible")
    def onchange_unreserve_other_moves_is_possible(self):
        self.allow_unreserve_other_moves = self.unreserve_other_moves_is_possible

    @api.depends("scenario", "picking_type_ids")
    def _compute_ignore_no_putaway_available_is_possible(self):
        for menu in self:
            menu.ignore_no_putaway_available_is_possible = bool(
                menu.scenario in self._scenario_allowing_ignore_no_putaway_available
            )

    @api.onchange("ignore_no_putaway_available_is_possible")
    def onchange_ignore_no_putaway_available_is_possible(self):
        self.ignore_no_putaway_available = self.ignore_no_putaway_available_is_possible

    @api.constrains("scenario", "picking_type_ids", "ignore_no_putaway_available")
    def _check_ignore_no_putaway_available(self):
        for menu in self:
            if (
                menu.ignore_no_putaway_available
                and not menu.ignore_no_putaway_available_is_possible
            ):
                raise exceptions.ValidationError(
                    _("Ignoring not found putaway is not allowed for menu {}.").format(
                        menu.name
                    )
                )

    @api.constrains("scenario", "picking_type_ids", "allow_unreserve_other_moves")
    def _check_allow_unreserve_other_moves(self):
        for menu in self:
            if (
                menu.allow_unreserve_other_moves
                and not menu.unreserve_other_moves_is_possible
            ):
                raise exceptions.ValidationError(
                    _(
                        "Processing reserved quantities is" " not allowed for menu {}."
                    ).format(menu.name)
                )

    # ATM the goal is to block using single_pack_transfer (SPT)
    # w/out moving the full pkg.
    # Is not optimal, but is mandatory as long as SPT does not work w/ moves
    # but only w/ package levels.
    # TODO: add tests.
    _move_entire_packs_scenario = ("single_pack_transfer", "delivery")

    @api.constrains("scenario", "picking_type_ids")
    def _check_move_entire_packages(self):
        _get_scenario_name = self._fields["scenario"].convert_to_export
        for menu in self:
            # TODO: these kind of checks should be provided by the scenario itself.
            bad_picking_types = [
                x.name for x in menu.picking_type_ids if not x.show_entire_packs
            ]
            if menu.scenario in self._move_entire_packs_scenario and bad_picking_types:
                scenario_name = _get_scenario_name(menu["scenario"], menu)
                raise exceptions.ValidationError(
                    _(
                        "Scenario `{}` require(s) "
                        "'Move Entire Packages' to be enabled.\n"
                        "These type(s) do not satisfy this constraint: \n{}.\n"
                        "Please, adjust your configuration."
                    ).format(scenario_name, "\n- ".join(bad_picking_types))
                )
