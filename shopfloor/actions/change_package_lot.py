# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, exceptions
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero

from odoo.addons.component.core import Component


class InventoryError(UserError):
    pass


class ChangePackageLot(Component):
    """Provide methods for changing a package or a lot on a move line"""

    _name = "shopfloor.change.package.lot.action"
    _inherit = "shopfloor.process.action"
    _usage = "change.package.lot"

    def change_lot(self, move_line, lot, response_ok_func, response_error_func):
        """Change the lot on the move line.

        :param response_ok_func: callable used to return ok response
        :param response_error_func: callable used to return error response
        """
        # If the lot is part of a package, what we really want
        # is not to change the lot, but change the package (which will
        # in turn change the lot altogether), but we have to pay attention
        # to some things:
        # * cannot replace a package by a lot without package (qty may be
        #   different, ...)
        # * if we have several packages for the same lot, we can't know which
        #   one the operator is moving, ask to scan a package
        lot_quants = self.env["stock.quant"].search(
            [
                ("lot_id", "=", lot.id),
                ("location_id", "=", move_line.location_id.id),
                ("quantity", ">", 0),
            ]
        )
        package_quants = lot_quants.filtered(lambda quant: quant.package_id)
        unit_quants = lot_quants - package_quants

        if len(package_quants) > 1 or (package_quants and unit_quants):
            # When we can't know which package to take, ask to scan a package.
            # If we have both units and package, they have to scan the package
            # first.
            return response_error_func(
                move_line,
                message=self.msg_store.several_packs_in_location(move_line.location_id),
            )
        elif len(package_quants) == 1:
            # change the package directly
            package = package_quants.package_id
            return self.change_package(
                move_line, package, response_ok_func, response_error_func
            )
        return self._change_pack_lot_change_lot(
            move_line, lot, response_ok_func, response_error_func
        )

    def _change_pack_lot_change_lot(
        self, move_line, lot, response_ok_func, response_error_func
    ):
        previous_lot = move_line.lot_id
        previous_reserved_uom_qty = move_line.reserved_uom_qty

        inventory = self._actions_for("inventory")

        try:
            with self.env.cr.savepoint():
                move_line.write(
                    {
                        "lot_id": lot.id,
                        "package_id": False,
                        "result_package_id": False,
                    }
                )
                rounding = move_line.product_id.uom_id.rounding
                if float_is_zero(
                    move_line.reserved_uom_qty, precision_rounding=rounding
                ):
                    # The lot is not found at all, but the user scanned it, which means
                    # it's an error in the stock data!
                    raise InventoryError("Lot not available")
        except InventoryError:
            inventory.create_control_stock(
                move_line.location_id,
                move_line.product_id,
                lot=lot,
                name=_(
                    "Pick: stock issue on lot: %(lot_name)s found in %(location_name)s",
                    lot_name=lot.name,
                    location_name=move_line.location_id.name,
                ),
            )
            message = self.msg_store.cannot_change_lot_already_picked(lot)
            return response_error_func(move_line, message=message)
        except UserError as e:
            message = {
                "message_type": "error",
                "body": str(e),
            }
            return response_error_func(move_line, message=message)

        message = self.msg_store.lot_replaced_by_lot(previous_lot, lot)
        if (
            float_compare(
                move_line.reserved_uom_qty,
                previous_reserved_uom_qty,
                precision_rounding=rounding,
            )
            != 0
        ):
            message["body"] += " " + _("The quantity to do has changed!")
        return response_ok_func(move_line, message=message)

    def _package_content_replacement_allowed(self, package, move_line):
        # we can't replace by a package which doesn't contain the product...
        return move_line.product_id in package.quant_ids.product_id

    def change_package(self, move_line, package, response_ok_func, response_error_func):
        # Prevent change if package is already set and it's the same
        if move_line.package_id == package:
            return response_error_func(
                move_line,
                message=self.msg_store.package_change_error_same_package(package),
            )

        # prevent to replace a package by a package that would not satisfy the
        # move (different product)
        content_replacement_allowed = self._package_content_replacement_allowed(
            package, move_line
        )
        if not content_replacement_allowed:
            return response_error_func(
                move_line, message=self.msg_store.package_different_content(package)
            )

        previous_package = move_line.package_id

        # /!\ be sure to box the side-effects before calling "replace_package"
        # in the savepoint, as we catch the error, we must be sure that any
        # change is rollbacked
        try:
            with self.env.cr.savepoint():
                # if no quantity is available in the package, this call will
                # raise a UserError, which will revert the savepoint
                move_line.replace_package(package)
        except exceptions.UserError as err:
            return response_error_func(
                move_line,
                message=self.msg_store.package_change_error(package, err.args[0]),
            )

        if previous_package:
            message = self.msg_store.package_replaced_by_package(
                previous_package, package
            )
        else:
            message = self.msg_store.units_replaced_by_package(package)
        return response_ok_func(move_line, message=message)
