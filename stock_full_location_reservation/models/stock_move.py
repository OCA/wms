# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import warnings
from typing import Literal

from odoo import api, fields, models, tools

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    is_full_location_reservation = fields.Boolean(
        "Full location reservation move", default=False
    )

    def init(self):
        tools.create_index(
            self._cr,
            "stock_move_full_loc_reservation_gc_idx",
            self._table,
            ["id"],
            where="is_full_location_reservation AND state = 'cancel'",
        )

    def _filter_full_location_reservation_moves(self):
        return self.filtered(lambda m: m.is_full_location_reservation)

    def _do_unreserve(self):
        if self.env.context.get("skip_undo_full_location_reservation"):
            return super()._do_unreserve()
        full_location_moves = self._filter_full_location_reservation_moves()
        full_location_moves._undo_full_location_reservation()
        return super(StockMove, (self - full_location_moves))._do_unreserve()

    def undo_full_location_reservation(self):
        full_location_moves = self._filter_full_location_reservation_moves()
        full_location_moves._undo_full_location_reservation()

    def _undo_full_location_reservation(self):
        if not self.exists():
            return
        self = self.with_context(skip_undo_full_location_reservation=True)
        self._do_unreserve()
        self._action_cancel()
        self._post_commit_unlink()

    def _post_commit_unlink(self):
        # We need to defer the unlink of the moves until the end of the
        # transaction to avoid issues where methods having a reference
        # to the original move would try to access it after it has been unlinked
        ids_to_unlink = self.ids
        env = self.env

        def _deferred_unlink():
            try:
                env["stock.move"].browse(ids_to_unlink).exists().unlink()
            except Exception:
                _logger.exception(
                    "Failed to unlink full location reservation moves %s",
                    ids_to_unlink,
                )

        self.env.cr.postcommit.add(_deferred_unlink)

    @api.autovacuum
    def _gc_full_location_reservation_moves(self):
        """This method is meant to be called by a cron and will delete full location
        reservation moves that are still in canceled state.

        This should normally not be necessary as the moves should be unlinked right
        after being canceled into the post commit hook of the transaction,
        but this is a safety measure in case something goes wrong with the unlinking.
        """
        self.search(
            [("is_full_location_reservation", "=", True), ("state", "=", "cancel")]
        ).unlink()

    def _prepare_full_location_reservation_package_level_vals(self, package):
        return {
            "package_id": package.id,
            "company_id": self.company_id.id,
        }

    def _full_location_reservation_create_package_level(self, package):
        return self.env["stock.package_level"].create(
            self._prepare_full_location_reservation_package_level_vals(package)
        )

    def _full_location_reservation_prepare_move_vals(
        self, product, qty, location, package=None
    ):
        self.ensure_one()
        package_level_id = False
        if package:
            package_level_id = self._full_location_reservation_create_package_level(
                package
            ).id
        return {
            "is_full_location_reservation": True,
            "product_uom_qty": qty,
            "name": product.name,
            "product_uom": product.uom_id.id,
            "product_id": product.id,
            "location_id": location.id,
            "location_dest_id": self.picking_id.location_dest_id.id,
            "picking_id": self.picking_id.id,
            "package_level_id": package_level_id,
        }

    def _full_location_reservation_create_move(
        self, product, qty, location, package=None
    ):
        new_move = self.copy(
            default=self._full_location_reservation_prepare_move_vals(
                product, qty, location, package
            )
        )
        if (
            self.product_id == product
            and self.picking_type_id.merge_move_for_full_location_reservation
        ):
            # To be able to be merged, the new move should use the same source location as
            # the original one.
            new_move.location_id = self.location_id
            self._do_unreserve()
            # Don't merge at confirm
            new_move._action_confirm(merge=False)
            new_move = (
                (new_move | self)
                .with_context(skip_undo_full_location_reservation=True)
                ._merge_moves(merge_into=self)
            )
        return new_move

    def _full_location_reservation(
        self,
        reservation_mode: Literal["strict", "package", "product"] | None = None,
        **kwargs
    ):
        if "package_only" in kwargs:
            warnings.warn(
                "The 'package_only' parameter is deprecated. "
                "Use reservation_mode='package' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if kwargs.pop("package_only"):
                reservation_mode = "package"
        return self.move_line_ids._full_location_reservation(
            reservation_mode=reservation_mode
        )
