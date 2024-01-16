# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _, exceptions, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero

_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _name = "stock.move.line"
    _inherit = ["stock.move.line", "shopfloor.priority.postpone.mixin"]

    # TODO use a serialized field
    shopfloor_unloaded = fields.Boolean(default=False)
    shopfloor_checkout_done = fields.Boolean(default=False)
    shopfloor_user_id = fields.Many2one(comodel_name="res.users", index=True)

    date_planned = fields.Datetime(related="move_id.date", store=True, index=True)

    # we search lines based on their location in some workflows
    location_id = fields.Many2one(index=True)
    package_id = fields.Many2one(index=True)
    result_package_id = fields.Many2one(index=True)

    # allow domain on picking_id.xxx without too much perf penalty
    picking_id = fields.Many2one(auto_join=True)

    def _split_partial_quantity(self):
        """Create new move line for the quantity remaining to do

        :return: the new move line if created else empty recordset
        """
        self.ensure_one()
        rounding = self.product_uom_id.rounding
        if float_is_zero(self.qty_done, precision_rounding=rounding):
            return self.browse()
        compare = float_compare(
            self.qty_done, self.product_uom_qty, precision_rounding=rounding
        )
        qty_lesser = compare == -1
        qty_greater = compare == 1
        assert not qty_greater, "Quantity done cannot exceed quantity to do"
        if qty_lesser:
            remaining = self.product_uom_qty - self.qty_done
            new_line = self.copy({"product_uom_qty": remaining, "qty_done": 0})
            # if we didn't bypass reservation update, the quant reservation
            # would be reduced as much as the deduced quantity, which is wrong
            # as we only moved the quantity to a new move line
            self.with_context(
                bypass_reservation_update=True
            ).product_uom_qty = self.qty_done
            return new_line
        return self.browse()

    def _extract_in_split_order(self, default=None):
        """Have pickings fully reserved with only those move lines.

        If the condition is not met, extract the move lines in a new picking.
        :param default: dictionary of field values to override in the original
            values of the copied record
        """
        for picking in self.picking_id:
            moves_to_extract = new_move = picking.move_lines.browse()
            need_backorder = need_split = False
            for move in picking.move_lines:
                if move.state in ("cancel", "done"):
                    continue
                if move.state == "confirmed":
                    # The move has no ancestor and is not available
                    need_backorder = True
                    continue
                move_lines = move.move_line_ids & self
                if not move_lines:
                    # The picking contains moves not related to given move lines
                    need_split = True
                    continue
                new_move = move.split_other_move_lines(move_lines, intersection=True)
                if new_move:
                    if move.state == "confirmed":
                        # The move has no ancestor and is not available
                        need_backorder = True
                    else:
                        # The move contains other move lines
                        need_split = True
                moves_to_extract += new_move or move
            if need_split:
                moves_to_extract._extract_in_split_order(default=default)
            elif need_backorder:
                # All the lines are processed but some moves are partially available
                moves_to_extract._extract_in_split_order(
                    default=default, backorder=True
                )

    def _split_pickings_from_source_location(self):
        """Ensure that the related pickings will have the same source location.

        Some pickings related could have other unrelated move lines, as such we
        have to split them to contain only the move lines related to the expected
        source location.

        Example:

            Initial data:

                PICK1:
                    - move line with source location LOC1
                    - move line with source location LOC2
                PICK2:
                    - move line with source location LOC2
                    - move line with source location LOC3

            Then we process move lines related to LOC2 with this method, we get:

                PICK1:
                    - move line with source location LOC1
                PICK2:
                    - move line with source location LOC3
                PICK3:
                    - move line with source location LOC2
                    - move line with source location LOC2

        Return the pickings containing the given move lines.
        """
        _logger.warning(
            "`_split_pickings_from_source_location` is deprecated "
            "and replaced by `_extract_in_split_order`"
        )
        location_src_to_process = self.location_id
        if location_src_to_process and len(location_src_to_process) != 1:
            raise UserError(
                _("Move lines processed have to share the same source location.")
            )
        pickings = self.picking_id
        move_lines_to_process_ids = []
        for picking in pickings:
            location_src = picking.move_line_ids.location_id
            if len(location_src) == 1:
                continue
            (picking.move_line_ids & self)._extract_in_split_order()
            # Get the related move lines among the picking and split them
            move_lines_to_process_ids.extend(
                set(picking.move_line_ids.ids) & set(self.ids)
            )
        return self.picking_id

    def _split_qty_to_be_done(self, qty_done, split_partial=True, **split_default_vals):
        """Check qty to be done for current move line. Split it if needed.

        :param qty_done: qty expected to be done
        :param split_partial: split if qty is less than expected
            otherwise rely on a backorder.
        """
        if self.product_uom_qty < 0:
            raise UserError(_("The demand cannot be negative"))
        # store a new line if we have split our line (not enough qty)
        new_line = self.env["stock.move.line"]
        rounding = self.product_uom_id.rounding
        compare = float_compare(
            qty_done, self.product_uom_qty, precision_rounding=rounding
        )
        qty_lesser = compare == -1
        qty_greater = compare == 1
        if qty_greater:
            return (new_line, "greater")
        elif qty_lesser:
            if not split_partial:
                return (new_line, "lesser")
            new_line = self._split_partial_quantity_to_be_done(
                qty_done, split_default_vals
            )
            return (new_line, "lesser")
        return (new_line, "full")

    def _split_partial_quantity_to_be_done(self, quantity_done, split_default_vals):
        """Create a new move line with the remaining quantity to process."""
        # split the move line which will be processed later (maybe the user
        # has to pick some goods from another place because the location
        # contained less items than expected)
        remaining = self.product_uom_qty - quantity_done
        vals = {"product_uom_qty": remaining, "qty_done": 0}
        vals.update(split_default_vals)
        new_line = self.copy(vals)
        # if we didn't bypass reservation update, the quant reservation
        # would be reduced as much as the deduced quantity, which is wrong
        # as we only moved the quantity to a new move line
        self.with_context(
            bypass_reservation_update=True
        ).product_uom_qty = quantity_done
        return new_line

    def replace_package(self, new_package):
        """Replace a package on an assigned move line"""
        self.ensure_one()

        # search other move lines which should already pick the scanned package
        other_reserved_lines = self.env["stock.move.line"].search(
            [
                ("package_id", "=", new_package.id),
                ("state", "in", ("partially_available", "assigned")),
            ]
        )

        # we can't change already picked lines
        unreservable_lines = other_reserved_lines.filtered(
            lambda line: line.qty_done == 0
        )
        to_assign_moves = unreservable_lines.move_id

        # if we leave the package level, it will try to reserve the same
        # one again
        unreservable_lines.package_level_id.explode_package()
        # unreserve qties of other lines
        unreservable_lines.unlink()

        if new_package.location_id != self.location_id:
            if new_package.quant_ids.reserved_quantity:
                # this is a unexpected condition: if we started picking a package
                # in another location, user should never be able to scan it in
                # another location, block the operation
                raise exceptions.UserError(
                    _(
                        "Package {} has been partially picked in another location"
                    ).format(new_package.display_name)
                )
            # the package has been scanned in the current location so we know its
            # a mistake in the data... fix the quant to move the package here
            new_package.move_package_to_location(self.location_id)

        # several move lines can be moved by the package level, if we change
        # the package for the current one, we destroy the package level because
        # we are no longer moving the entire package
        self.package_level_id.explode_package()

        def is_greater(value, other, rounding):
            return float_compare(value, other, precision_rounding=rounding) == 1

        def is_lesser(value, other, rounding):
            return float_compare(value, other, precision_rounding=rounding) == -1

        quant = fields.first(
            new_package.quant_ids.filtered(
                lambda quant: quant.product_id == self.product_id
                and is_greater(
                    quant.quantity,
                    quant.reserved_quantity,
                    quant.product_uom_id.rounding,
                )
            )
        )
        if not quant:
            raise exceptions.UserError(
                _(
                    "Package {} does not contain available product {},"
                    " cannot replace package."
                ).format(new_package.display_name, self.product_id.display_name)
            )

        values = {
            "package_id": new_package.id,
            "lot_id": quant.lot_id.id,
            "owner_id": quant.owner_id.id,
            "result_package_id": False,
        }

        available_quantity = quant.quantity - quant.reserved_quantity
        if is_lesser(
            available_quantity, self.product_qty, quant.product_uom_id.rounding
        ):
            new_uom_qty = self.product_id.uom_id._compute_quantity(
                available_quantity, self.product_uom_id, rounding_method="HALF-UP"
            )
            values["product_uom_qty"] = new_uom_qty

        self.write(values)

        # try reassign the move in case we had a partial qty, also, it will
        # recreate a package level if it applies
        if "product_uom_qty" in values:
            # when we change the quantity of the move, the state
            # will still be "assigned" and be skipped by "_action_assign",
            # recompute the state to be "partially_available"
            self.move_id._recompute_state()

        # if the new package has less quantities, assign will create new move
        # lines
        self.move_id._action_assign()

        # Find other available goods for the lines which were using the
        # package before...
        to_assign_moves._action_assign()

        # computation of the 'state' of the package levels is not
        # triggered, force it
        to_assign_moves.move_line_ids.package_level_id.modified(["move_line_ids"])
        self.package_level_id.modified(["move_line_ids"])

    def _filter_on_picking(self, picking=False):
        """Filter a bunch of lines on a picking.

        If no picking is provided the first one is taken.
        """
        picking = picking or fields.first(self.picking_id)
        return self.filtered_domain([("picking_id", "=", picking.id)])
