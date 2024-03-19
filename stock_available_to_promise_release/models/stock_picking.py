# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, exceptions, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    need_release = fields.Boolean(
        compute="_compute_need_release", search="_search_need_release"
    )
    need_release_count = fields.Integer(
        string="# of need release moves", compute="_compute_need_release"
    )
    release_ready = fields.Boolean(
        compute="_compute_release_ready", search="_search_release_ready"
    )
    release_ready_count = fields.Integer(
        string="# of moves ready", compute="_compute_release_ready"
    )
    date_priority = fields.Datetime(
        string="Priority Date",
        compute="_compute_date_priority",
        help="Date/time used to sort moves to deliver first. "
        "Used to calculate the ordered available to promise.",
    )
    last_release_date = fields.Datetime()

    @api.depends("move_ids.need_release")
    def _compute_need_release(self):
        data = self.env["stock.move"].read_group(
            [("need_release", "=", True), ("picking_id", "in", self.ids)],
            ["picking_id"],
            ["picking_id"],
        )
        count = {
            row["picking_id"][0]: row["picking_id_count"]
            for row in data
            if row["picking_id"]
        }
        for picking in self:
            picking.need_release_count = count.get(picking.id, 0)
            picking.need_release = bool(picking.need_release_count)

    def _search_need_release(self, operator, value):
        if operator not in ("=", "!="):
            raise exceptions.UserError(_("Unsupported operator: %s") % (operator,))
        groups = self.env["stock.move"].read_group(
            [("need_release", "=", True)], ["picking_id"], ["picking_id"]
        )
        # if we have at least one stock move that needs release, the
        # picking needs release
        combinations = {
            ("=", True): "in",
            ("=", False): "not in",
            ("!=", True): "not in",
            ("!=", False): "in",
        }
        in_operator = combinations[(operator, value)]
        picking_ids = [group["picking_id"][0] for group in groups]
        return [("id", in_operator, picking_ids)]

    def _get_shipping_policy(self):
        """Hook returning the related shipping policy."""
        self.ensure_one()
        return self.move_type

    # move_ids.ordered_available_to_promise_qty has no depends, so we need to
    # invalidate cache before accessing this release_ready computed value
    @api.depends(
        "move_type",
        "move_ids.ordered_available_to_promise_qty",
        "move_ids.need_release",
        "move_ids.state",
    )
    def _compute_release_ready(self):
        for picking in self:
            moves = picking.move_ids.filtered(lambda move: move._is_release_needed())
            release_ready = False
            release_ready_count = sum(1 for move in moves if move._is_release_ready())
            if moves:
                if picking._get_shipping_policy() == "one":
                    release_ready = release_ready_count == len(moves)
                else:
                    release_ready = bool(release_ready_count)
            picking.release_ready_count = release_ready_count
            picking.release_ready = release_ready

    def _search_release_ready(self, operator, value):
        if operator != "=":
            raise exceptions.UserError(_("Unsupported operator %s") % (operator,))
        # if we search moves with a promise qty > 0, we restrict
        # the number of moves / pickings to filter afterwards
        moves = self.env["stock.move"].search(
            [("ordered_available_to_promise_uom_qty", ">", 0)]
        )
        # computed field depends on ordered_available_to_promise_qty that has no
        # depends set, invalidate cache before reading
        moves.picking_id.invalidate_recordset(["release_ready"])
        pickings = moves.picking_id.filtered("release_ready")
        return [("id", "in", pickings.ids)]

    @api.depends("move_ids.date_priority")
    def _compute_date_priority(self):
        for picking in self:
            dates = [
                date_priority
                for date_priority in picking.move_ids.mapped("date_priority")
                if date_priority
            ]
            picking.date_priority = min(dates) if dates else False

    def release_available_to_promise(self):
        # When the stock.picking form view is opened through the "Deliveries"
        # button of a sale order, the latter sets values in the context such as
        # default_picking_id default_origin, ... Clean up these values
        # otherwise they make the release misbehave.
        context = {
            key: value
            for key, value in self.env.context.items()
            if not key.startswith("default_")
        }
        self.move_ids.with_context(**context).release_available_to_promise()

    def _release_link_backorder(self, origin_picking):
        self.backorder_id = origin_picking
        origin_picking.message_post(
            body=_(
                "The backorder <a href=# data-oe-model=stock.picking"
                " data-oe-id=%(id)s>%(name)s</a> has been created.",
                name=self.name,
                id=self.id,
            )
        )

    def _after_release_update_chain(self):
        """Called after the moves are released

        ``self`` contains all the stock.picking of the chain up
        to the released one.
        """
        self._after_release_set_last_release_date()

    def _after_release_set_last_release_date(self):
        self.last_release_date = fields.Datetime.now()

    def action_open_move_need_release(self):
        self.ensure_one()
        if not self.need_release:
            return
        xmlid = "stock_available_to_promise_release.stock_move_release_action"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = [("picking_id", "=", self.id), ("need_release", "=", True)]
        action["context"] = {}
        return action

    def _create_backorder(self):
        backorders = super()._create_backorder()
        backorders_to_unrelease = backorders.filtered(
            lambda p: p.picking_type_id.unrelease_on_backorder
        )
        if backorders_to_unrelease:
            backorders_to_unrelease.mapped("move_ids").filtered(
                "unrelease_allowed"
            ).unrelease()
        return backorders

    def unrelease(self, safe_unrelease=False):
        """Unrelease the moves of the picking.

        If safe_unrelease is True, the unreleasable moves for which the
        processing has already started will be ignored
        """
        self.mapped("move_ids").unrelease(safe_unrelease=safe_unrelease)
