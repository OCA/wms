# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, exceptions, fields, models
from odoo.tools.float_utils import float_compare


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
    zip_code = fields.Char(related="partner_id.zip", store=True)
    state_id = fields.Many2one(related="partner_id.state_id", store=True)
    city = fields.Char(related="partner_id.city", store=True)

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

    @api.depends("move_ids.ordered_available_to_promise_qty")
    def _compute_release_ready(self):
        for picking in self:
            if not picking.need_release:
                picking.release_ready = False
                picking.release_ready_count = 0
                continue
            move_lines = picking.move_ids.filtered(
                lambda move: move.state not in ("cancel", "done")
            )
            if picking._get_shipping_policy() == "one":
                picking.release_ready_count = sum(
                    1
                    for move in move_lines
                    if float_compare(
                        move.ordered_available_to_promise_qty,
                        move.product_qty,
                        precision_rounding=move.product_id.uom_id.rounding,
                    )
                    == 0
                )
                picking.release_ready = picking.release_ready_count == len(move_lines)
            else:
                picking.release_ready_count = sum(
                    1
                    for move in move_lines
                    if move.ordered_available_to_promise_qty > 0
                )
                picking.release_ready = bool(picking.release_ready_count)

    def _search_release_ready(self, operator, value):
        if operator != "=":
            raise exceptions.UserError(_("Unsupported operator %s") % (operator,))
        # if we search moves with a promise qty > 0, we restrict
        # the number of moves / pickings to filter afterwards
        moves = self.env["stock.move"].search(
            [("ordered_available_to_promise_uom_qty", ">", 0)]
        )
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
        self.mapped("move_ids").with_context(**context).release_available_to_promise()

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
        self._after_release_set_printed()
        self._after_release_set_expected_date()

    def _after_release_set_printed(self):
        self.filtered(lambda p: not p.printed).printed = True

    def _after_release_set_expected_date(self):
        prep_time = self.env.company.stock_release_max_prep_time
        new_expected_date = fields.Datetime.add(
            fields.Datetime.now(), minutes=prep_time
        )
        self.scheduled_date = new_expected_date

    def action_open_move_need_release(self):
        self.ensure_one()
        if not self.need_release:
            return
        xmlid = "stock_available_to_promise_release.stock_move_release_action"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = [("picking_id", "=", self.id), ("need_release", "=", True)]
        action["context"] = {}
        return action
