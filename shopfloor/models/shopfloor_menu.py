# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models

PICK_PACK_SAME_TIME_HELP = """
If you tick this box, while picking goods from a location
(eg: zone picking) set destination will work as follow:

* if a location is scanned, a new delivery package is created;
* if a package is scanned, the package is validated against the carrier
* in both cases, if the picking has no carrier the operation fails.",
"""

UNLOAD_PACK_AT_DEST_HELP = """
With this option, the lines you process by putting on a package during the
picking process will be put as bulk products at the final destination location.

This is useful if your picking device is emptied at the destination location or
if you want to provide bulk products to the next operation.

Incompatible with: "Pick and pack at the same time"
"""

MULTIPLE_MOVE_SINGLE_PACK_HELP = """
When picking a move,
allow to set a destination package that was already used for the other lines.
"""


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    picking_type_ids = fields.Many2many(
        comodel_name="stock.picking.type", string="Operation Types", required=True
    )
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
    prepackaged_product_is_possible = fields.Boolean(
        compute="_compute_prepackaged_product_is_possible"
    )
    allow_prepackaged_product = fields.Boolean(
        string="Process as pre-packaged",
        default=False,
        help=(
            "When active, what you scan (typically a product packaging EAN) "
            "will be ship 'as-is' and the operation will be validated "
            "triggering a backorder creation with the remaining lines."
        ),
    )
    # TODO: refactor handling of these options.
    # Possible solution:
    # * field should stay on the scenario and get stored in options
    # * field should use `sf_scenario` (eg: sf_scenario=("zone_picking", ))
    #   to control for which scenario it will be available
    # * on the menu form, display a button to edit configurations
    #   and display a summary
    pick_pack_same_time = fields.Boolean(
        string="Pick and pack at the same time",
        default=False,
        help=PICK_PACK_SAME_TIME_HELP,
    )
    pick_pack_same_time_is_possible = fields.Boolean(
        compute="_compute_pick_pack_same_time_is_possible"
    )
    multiple_move_single_pack_is_possible = fields.Boolean(
        compute="_compute_multiple_move_single_pack_is_possible"
    )
    multiple_move_single_pack = fields.Boolean(
        string="Collect multiple moves on a same destination package",
        default=False,
        help=MULTIPLE_MOVE_SINGLE_PACK_HELP,
    )
    unload_package_at_destination_is_possible = fields.Boolean(
        compute="_compute_unload_package_at_dest_is_possible"
    )
    unload_package_at_destination = fields.Boolean(
        string="Unload package at destination",
        default=False,
        help=UNLOAD_PACK_AT_DEST_HELP,
    )

    allow_force_reservation = fields.Boolean(
        string="Force stock reservation",
        default=False,
    )
    allow_force_reservation_is_possible = fields.Boolean(
        compute="_compute_allow_force_reservation_is_possible"
    )

    @api.onchange("unload_package_at_destination")
    def _onchange_unload_package_at_destination(self):
        # Uncheck pick_pack_same_time when unload_package_at_destination is set to True
        # Ensure that multiple_move_single_pack is False when
        # unload_package_at_destination is checked out
        for record in self:
            if record.unload_package_at_destination:
                record.pick_pack_same_time = False
            else:
                record.multiple_move_single_pack = False

    @api.onchange("pick_pack_same_time")
    def _onchange_pick_pack_same_time(self):
        # pick_pack_same_time is incompatible with multiple_move_single_pack and
        # multiple_move_single_pack
        for record in self:
            if record.pick_pack_same_time:
                record.unload_package_at_destination = False
                record.multiple_move_single_pack = False

    @api.onchange("multiple_move_single_pack")
    def _onchange_multiple_move_single_pack(self):
        # multiple_move_single_pack is incompatible with pick_pack_same_time,
        # and requires unload_package_at_destination to be set
        for record in self:
            if record.multiple_move_single_pack:
                record.unload_package_at_destination = True
                record.pick_pack_same_time = False

    @api.constrains(
        "unload_package_at_destination",
        "pick_pack_same_time",
        "multiple_move_single_pack",
    )
    def _check_options(self):
        if self.pick_pack_same_time and self.unload_package_at_destination:
            raise exceptions.UserError(
                _(
                    "'Pick and pack at the same time' is incompatible with "
                    "'Unload package at destination'."
                )
            )
        elif self.pick_pack_same_time and self.multiple_move_single_pack:
            raise exceptions.UserError(
                _(
                    "'Pick and pack at the same time' is incompatible with "
                    "'Multiple moves same destination package'."
                )
            )
        elif self.multiple_move_single_pack and not self.unload_package_at_destination:
            raise exceptions.UserError(
                _(
                    "'Multiple moves same destination package' is mandatory when "
                    "'Pick and pack at the same time' is set."
                )
            )

    @api.depends("scenario_id", "picking_type_ids")
    def _compute_move_create_is_possible(self):
        for menu in self:
            menu.move_create_is_possible = bool(
                menu.scenario_id.has_option("allow_create_moves")
                and len(menu.picking_type_ids) == 1
            )

    @api.onchange("move_create_is_possible")
    def onchange_move_create_is_possible(self):
        self.allow_move_create = self.move_create_is_possible

    @api.constrains("scenario_id", "picking_type_ids", "allow_move_create")
    def _check_allow_move_create(self):
        for menu in self:
            if menu.allow_move_create and not menu.move_create_is_possible:
                raise exceptions.ValidationError(
                    _("Creation of moves is not allowed for menu {}.").format(menu.name)
                )

    @api.depends("scenario_id")
    def _compute_unreserve_other_moves_is_possible(self):
        for menu in self:
            menu.unreserve_other_moves_is_possible = menu.scenario_id.has_option(
                "allow_unreserve_other_moves"
            )

    @api.depends("scenario_id")
    def _compute_pick_pack_same_time_is_possible(self):
        for menu in self:
            menu.pick_pack_same_time_is_possible = menu.scenario_id.has_option(
                "pick_pack_same_time"
            )

    @api.depends("scenario_id")
    def _compute_unload_package_at_dest_is_possible(self):
        for menu in self:
            menu.unload_package_at_destination_is_possible = (
                menu.scenario_id.has_option("unload_package_at_destination")
            )

    @api.depends("scenario_id")
    def _compute_multiple_move_single_pack_is_possible(self):
        for menu in self:
            menu.multiple_move_single_pack_is_possible = menu.scenario_id.has_option(
                "multiple_move_single_pack"
            )

    @api.onchange("unreserve_other_moves_is_possible")
    def onchange_unreserve_other_moves_is_possible(self):
        self.allow_unreserve_other_moves = self.unreserve_other_moves_is_possible

    @api.depends("scenario_id")
    def _compute_ignore_no_putaway_available_is_possible(self):
        for menu in self:
            menu.ignore_no_putaway_available_is_possible = menu.scenario_id.has_option(
                "allow_ignore_no_putaway_available"
            )

    @api.onchange("ignore_no_putaway_available_is_possible")
    def onchange_ignore_no_putaway_available_is_possible(self):
        self.ignore_no_putaway_available = self.ignore_no_putaway_available_is_possible

    @api.depends("scenario_id")
    def _compute_prepackaged_product_is_possible(self):
        for menu in self:
            menu.prepackaged_product_is_possible = menu.scenario_id.has_option(
                "allow_prepackaged_product"
            )

    @api.constrains("scenario_id", "picking_type_ids", "ignore_no_putaway_available")
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

    @api.constrains("scenario_id", "picking_type_ids", "allow_unreserve_other_moves")
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

    @api.constrains("scenario_id", "picking_type_ids")
    def _check_move_entire_packages(self):
        for menu in self:
            # TODO: these kind of checks should be provided by the scenario itself.
            bad_picking_types = [
                x.name for x in menu.picking_type_ids if not x.show_entire_packs
            ]
            if (
                menu.scenario_id.has_option("must_move_entire_pack")
                and bad_picking_types
            ):
                scenario_name = menu.scenario_id.name
                raise exceptions.ValidationError(
                    _(
                        "Scenario `{}` require(s) "
                        "'Move Entire Packages' to be enabled.\n"
                        "These type(s) do not satisfy this constraint: \n{}.\n"
                        "Please, adjust your configuration."
                    ).format(scenario_name, "\n- ".join(bad_picking_types))
                )

    @api.depends("scenario_id")
    def _compute_allow_force_reservation_is_possible(self):
        for menu in self:
            menu.allow_force_reservation_is_possible = menu.scenario_id.has_option(
                "allow_force_reservation"
            )
