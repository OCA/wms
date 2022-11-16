# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

logger = logging.getLogger(__name__)


class StockWarehouseFlow(models.Model):
    _name = "stock.warehouse.flow"
    _description = "Stock Warehouse Routing Flow"
    _order = "sequence"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(related="warehouse_id.company_id")
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        ondelete="restrict",
        string="Warehouse",
        default=lambda o: o._default_warehouse_id(),
        required=True,
    )
    from_picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        ondelete="restrict",
        string="From operation type",
        required=True,
        index=True,
        domain="[('code', '=', 'outgoing')]",
    )
    from_location_src_id = fields.Many2one(
        comodel_name="stock.location",
        compute="_compute_from_location_src_id",
    )
    from_location_dest_id = fields.Many2one(
        comodel_name="stock.location",
        compute="_compute_from_location_dest_id",
    )
    to_picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        ondelete="restrict",
        string="To operation type",
        readonly=True,
        domain="[('default_location_dest_id', '=', from_location_dest_id)]",
        check_company=True,
    )
    to_output_stock_loc_id = fields.Many2one(
        comodel_name="stock.location",
        ondelete="restrict",
        string="To output location",
        check_company=True,
    )
    carrier_ids = fields.Many2many(
        comodel_name="delivery.carrier",
        relation="delivery_carrier_stock_warehouse_flow_rel",
        column1="stock_warehouse_flow_id",
        column2="delivery_carrier_id",
        string="With carriers",
        copy=False,
    )
    move_domain = fields.Char(
        string="Source Routing Domain",
        default=[],
        copy=False,
        help="Domain based on Stock Moves, to define if the "
        "routing flow is applicable or not.",
    )
    delivery_steps = fields.Selection(
        selection=[
            ("ship_only", "Deliver goods directly (1 step)"),
            ("pick_ship", "Send goods in output and then deliver (2 steps)"),
            (
                "pick_pack_ship",
                "Pack goods, send goods in output and then deliver (3 steps)",
            ),
        ],
        string="Outgoing Shipments",
        default="ship_only",
        required=True,
        help="Outgoing route to follow",
    )
    sequence_prefix = fields.Char(
        help=(
            "Used to generate the default prefix of new operation types. "
            "(e.g. 'DG' => 'WH/OUT/DG/')"
        )
    )
    delivery_route_id = fields.Many2one(
        comodel_name="stock.location.route",
        string="Delivery Route",
        ondelete="set null",
        readonly=True,
        index=True,
        copy=False,
    )
    rule_ids = fields.One2many(
        related="delivery_route_id.rule_ids",
        string="Rules",
    )
    impacted_route_ids = fields.One2many(
        comodel_name="stock.location.route",
        compute="_compute_impacted_route_ids",
        string="Impacted Routes",
    )
    warning = fields.Html(compute="_compute_warning")
    pack_stock_loc_id = fields.Many2one(
        "stock.location", "Packing Location", check_company=True
    )
    output_stock_loc_id = fields.Many2one(
        related="to_output_stock_loc_id",
        string="Output Location",
        readonly=True,
        help=(
            "Same than 'To output location' field, displayed here to get a "
            "global overview of the flow configuration."
        ),
    )
    pick_type_id = fields.Many2one(
        "stock.picking.type", "Pick Type", check_company=True
    )
    pack_type_id = fields.Many2one(
        "stock.picking.type", "Pack Type", check_company=True
    )
    out_type_id = fields.Many2one(
        related="to_picking_type_id",
        string="Out Type",
        readonly=True,
        help=(
            "Same than 'To operation type' field, displayed here to get a "
            "global overview of the flow configuration."
        ),
    )

    def _default_warehouse_id(self):
        warehouse = self.env["stock.warehouse"].search([])
        if len(warehouse) == 1:
            return warehouse

    @api.depends("from_picking_type_id.default_location_src_id")
    def _compute_from_location_src_id(self):
        for record in self:
            location = record.from_picking_type_id.default_location_src_id
            if not location:
                __, location = self.env["stock.warehouse"]._get_partner_locations()
            record.from_location_src_id = location

    @api.depends("from_picking_type_id.default_location_dest_id")
    def _compute_from_location_dest_id(self):
        for record in self:
            location = record.from_picking_type_id.default_location_dest_id
            if not location:
                location, __ = self.env["stock.warehouse"]._get_partner_locations()
            record.from_location_dest_id = location

    def _compute_impacted_route_ids(self):
        for flow in self:
            rules = self.env["stock.rule"].search(
                [
                    ("picking_type_id", "=", flow.from_picking_type_id.id),
                    ("route_id.flow_id", "=", False),
                ]
            )
            flow.impacted_route_ids = rules.route_id

    def _compute_warning(self):
        for flow in self:
            flow.warning = False
            try:
                flow._get_rule_from_delivery_route(html_exc=True)
            except UserError as exc:
                flow.warning = str(exc)

    @api.constrains(
        "warehouse_id", "from_picking_type_id", "carrier_ids", "move_domain"
    )
    def _constrains_uniq(self):
        args = [
            ("warehouse_id", "=", self.warehouse_id.id),
            ("from_picking_type_id", "=", self.from_picking_type_id.id),
        ]
        flows = self.search(args) - self
        for flow in flows:
            if (
                self.carrier_ids & flow.carrier_ids
                or not self.carrier_ids
                and not flow.carrier_ids
            ) and self.move_domain == flow.move_domain:
                raise UserError(
                    _("Existing flow '%s' already applies on these kind of moves.")
                    % flow.name
                )

    @api.onchange("name")
    def onchange_name(self):
        self.sequence_prefix = "".join(
            [w[0] for w in (self.name or "").split()]
        ).upper()

    @api.onchange("warehouse_id")
    def onchange_warehouse_id(self):
        self.from_picking_type_id = self.warehouse_id.out_type_id

    def _generate_delivery_route(self):
        self.ensure_one()
        if self.delivery_route_id:
            return False
        # Re-generate the WH configuration with the chosen delivery steps in a
        # savepoint to get a whole route+rules+picking types configured almost
        # automatically (to not re-invent the wheel).
        # Delivery route values are then copied to generate a new one.
        # Copy some picking types with new sublocations first so the new
        # delivery route will use them.
        if not self.to_picking_type_id:
            self.to_picking_type_id = self.warehouse_id.out_type_id.copy(
                {
                    "name": (
                        f"{self.warehouse_id.out_type_id.name} "
                        f"{self.sequence_prefix}"
                    ),
                    "active": True,
                }
            )
            self.to_picking_type_id.sequence_id.prefix += f"{self.sequence_prefix}/"
        if "pick_" in self.delivery_steps:
            if not self.pick_type_id:
                self.pick_type_id = self.warehouse_id.pick_type_id.copy(
                    {
                        "name": (
                            f"{self.warehouse_id.pick_type_id.name} "
                            f"{self.sequence_prefix}"
                        ),
                        "active": True,
                    }
                )
                self.pick_type_id.sequence_id.prefix += f"{self.sequence_prefix}/"
            # Create a dedicated 'Output/SUB' location
            if not self.to_output_stock_loc_id:
                self.to_output_stock_loc_id = (
                    self.warehouse_id.wh_output_stock_loc_id.copy(
                        {
                            "name": self.sequence_prefix,
                            "location_id": self.warehouse_id.wh_output_stock_loc_id.id,
                        }
                    )
                )
                self.pick_type_id.default_location_dest_id = self.to_output_stock_loc_id
                self.to_picking_type_id.default_location_src_id = (
                    self.to_output_stock_loc_id
                )
            if "pack_" in self.delivery_steps:
                if not self.pack_type_id:
                    self.pack_type_id = self.warehouse_id.pack_type_id.copy(
                        {
                            "name": (
                                f"{self.warehouse_id.pack_type_id.name} "
                                f"{self.sequence_prefix}"
                            ),
                            "active": True,
                        }
                    )
                    self.pack_type_id.sequence_id.prefix += f"{self.sequence_prefix}/"
                # Create a dedicated 'Packing Zone/SUB' location
                if not self.pack_stock_loc_id:
                    self.pack_stock_loc_id = self.warehouse_id.wh_pack_stock_loc_id.copy(
                        {
                            "name": self.sequence_prefix,
                            "location_id": self.warehouse_id.wh_pack_stock_loc_id.id,
                        }
                    )
                self.pick_type_id.default_location_dest_id = self.pack_stock_loc_id
                self.pack_type_id.default_location_src_id = self.pack_stock_loc_id
                self.pack_type_id.default_location_dest_id = self.to_output_stock_loc_id
        try:
            with self.env.cr.savepoint():
                wh_vals = {
                    "delivery_steps": self.delivery_steps,
                    "out_type_id": self.to_picking_type_id.id,
                }
                if self.pick_type_id:
                    wh_vals.update(
                        {
                            "pick_type_id": self.pick_type_id.id,
                            "wh_output_stock_loc_id": self.to_output_stock_loc_id.id,
                        }
                    )
                if self.pack_type_id:
                    wh_vals.update(
                        {
                            "pack_type_id": self.pack_type_id.id,
                            "wh_pack_stock_loc_id": self.pack_stock_loc_id.id,
                        }
                    )
                wh_vals["out_type_id"] = self.to_picking_type_id.id
                self.warehouse_id.write(wh_vals)
                vals = self.warehouse_id.delivery_route_id.copy_data()[0]
                raise Exception()
        except Exception:
            logger.info(
                f"Routing flow {self.name}: delivery route data generated "
                f"from WH {self.warehouse_id.name}"
            )
        vals.update(
            {
                "name": f"{self.warehouse_id.name}: {self.name}",
                "active": True,
                "flow_id": self.id,
                # Give the priority to routes/rules not tied to a flow
                # when the initial move is created by the procurement
                "sequence": 1000,
            }
        )
        self.delivery_route_id = self.env["stock.location.route"].create(vals)
        # Subscribe the route to the warehouse
        if self.delivery_route_id.warehouse_selectable:
            self.warehouse_id.route_ids |= self.delivery_route_id

    def action_generate_route(self):
        for flow in self:
            flow._generate_delivery_route()
        return True

    def _search_for_move_domain(self, move):
        domain = [
            ("from_picking_type_id", "=", move.picking_type_id.id),
            ("delivery_route_id", "!=", False),
        ]
        if move.group_id.carrier_id:
            domain.append(("carrier_ids", "in", move.group_id.carrier_id.ids))
        else:
            domain.append(("carrier_ids", "=", False))
        return domain

    def _is_valid_for_move(self, move):
        self.ensure_one()
        if not self.move_domain:
            return move
        domain = safe_eval(self.move_domain or "[]")
        if not domain:
            return move
        return move.filtered_domain(domain)

    @api.model
    def _search_for_move(self, move):
        """Return the first flow matching the move."""
        domain = self._search_for_move_domain(move)
        flows = self.search(domain)
        for flow in flows:
            if flow._is_valid_for_move(move):
                return flow
        if flows:
            raise UserError(
                _(
                    "No routing flow available for the move {move} in transfer {picking}."
                ).format(move=move.display_name, picking=move.picking_id.name)
            )
        return self.browse()

    def _get_rule_from_delivery_route(self, html_exc=False):
        rule = self.delivery_route_id.rule_ids.filtered(
            lambda r: r.picking_type_id == self.to_picking_type_id
        )
        if self.delivery_route_id and not rule:
            args = {
                "picking_type": self.to_picking_type_id.display_name,
                "delivery_route": self.delivery_route_id.display_name,
            }
            if html_exc:
                args = {
                    "picking_type": f"<strong>{self.to_picking_type_id.display_name}</strong>",
                    "delivery_route": f"<strong>{self.delivery_route_id.display_name}</strong>",
                }
            raise UserError(
                _(
                    "No rule corresponding to '%(picking_type)s' operation type "
                    "has been found on delivery route '%(delivery_route)s'.\n"
                    "Please check your configuration."
                )
                % args
            )
        return rule

    def _apply_on_move(self, move):
        """Apply the flow configuration on the move."""
        if not self:
            return False
        logger.info("Applying flow '%s' on '%s'", self.name, move)
        rule = self._get_rule_from_delivery_route()
        move.picking_id = False
        move.picking_type_id = self.to_picking_type_id
        move.location_id = (
            self.to_output_stock_loc_id
            or self.to_picking_type_id.default_location_src_id
        )
        move.procure_method = rule.procure_method
        move.rule_id = rule
        move._assign_picking()

    def write(self, vals):
        res = super().write(vals)
        # Sync 'active' field with underlying route
        if "active" in vals:
            self.delivery_route_id.write({"active": vals["active"]})
        return res
