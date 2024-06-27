# Copyright 2021 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ClusterPicking(Component):
    _inherit = "shopfloor.cluster.picking"

    def _last_picked_line(self, picking):
        # a complete override to add a condition on internal package
        return fields.first(
            picking.move_line_ids.filtered(
                lambda l: l.qty_done > 0
                and l.result_package_id.is_internal
                # if we are moving the entire package, we shouldn't
                # add stuff inside it, it's not a new package
                and l.package_id != l.result_package_id
            ).sorted(key="write_date", reverse=True)
        )

    def _get_next_picking_to_pack(self, batch):
        """
        Return a picking not yet packed.

        The returned picking is the first
        one into the list of picking not yet packed (is_shopfloor_packing_todo=True).
         nbr_packages
        """
        pickings_to_pack = batch.picking_ids.filtered(
            lambda p: p.is_shopfloor_packing_todo
        )
        move_lines = pickings_to_pack.mapped("move_line_ids")
        move_lines = move_lines.filtered(
            lambda ml: ml.result_package_id.is_internal
        ).sorted(key=lambda ml: ml.result_package_id.name)
        return move_lines[0].picking_id if move_lines else move_lines.picking_id

    def _response_pack_picking_put_in_pack(self, picking, message=None):
        data = self.data_detail.pack_picking_detail(picking)
        return self._response(
            next_state="pack_picking_put_in_pack", data=data, message=message
        )

    def _response_pack_picking_scan_pack(self, picking, message=None):
        data = self.data_detail.pack_picking_detail(picking)
        return self._response(
            next_state="pack_picking_scan_pack", data=data, message=message
        )

    def scan_destination_pack(self, picking_batch_id, move_line_id, barcode, quantity):
        search = self._actions_for("search")
        bin_package = search.package_from_scan(barcode)

        if bin_package and not bin_package.is_internal:
            batch = self.env["stock.picking.batch"].browse(picking_batch_id)
            if not batch.exists():
                return self._response_batch_does_not_exist()
            move_line = self.env["stock.move.line"].browse(move_line_id)
            if not move_line.exists():
                return self._pick_next_line(
                    batch, message=self.msg_store.operation_not_found()
                )
            return self._response_for_scan_destination(
                move_line, message=self.msg_store.bin_should_be_internal(bin_package)
            )
        return super().scan_destination_pack(
            picking_batch_id, move_line_id, barcode, quantity
        )

    def scan_packing_to_pack(self, picking_batch_id, picking_id, barcode):
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()
        picking = batch.picking_ids.filtered(
            lambda p, picking_id=picking_id: p.id == picking_id
        )
        if not picking:
            return self._prepare_pack_picking(
                batch,
                message=self.msg_store.stock_picking_not_found(),
            )
        if not picking.is_shopfloor_packing_todo:
            return self._prepare_pack_picking(
                batch,
                message=self.msg_store.stock_picking_already_packed(picking),
            )

        search = self._actions_for("search")
        bin_package = search.package_from_scan(barcode)

        if not bin_package:
            return self._prepare_pack_picking(
                batch, message=self.msg_store.bin_not_found_for_barcode(barcode)
            )
        if not bin_package.is_internal:
            return self._prepare_pack_picking(
                batch, message=self.msg_store.bin_should_be_internal(bin_package)
            )
        if bin_package not in picking.mapped("move_line_ids.result_package_id"):
            return self._prepare_pack_picking(
                batch, message=self.msg_store.bin_is_for_another_picking(bin_package)
            )

        picking._set_packing_pack_scanned(bin_package.id)
        return self._prepare_pack_picking(
            batch,
        )

    def _prepare_pack_picking(self, batch, message=None):
        picking = self._get_next_picking_to_pack(batch)
        if not picking:
            return self._response_put_in_pack(
                batch.id,
                message=self.msg_store.stock_picking_packed_successfully(picking),
            )
        if picking.is_shopfloor_packing_pack_to_scan():
            return self._response_pack_picking_scan_pack(picking, message=message)
        return self._response_pack_picking_put_in_pack(picking, message=message)

    def prepare_unload(self, picking_batch_id):
        # before initializing the unloading phase we put picking in pack if
        # required by the scenario
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()
        if not self.work.menu.pack_pickings or not batch.is_shopfloor_packing_todo:
            return super().prepare_unload(picking_batch_id)
        return self._prepare_pack_picking(batch)

    def put_in_pack(self, picking_batch_id, picking_id, nbr_packages):
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()
        picking = batch.picking_ids.filtered(
            lambda p, picking_id=picking_id: p.id == picking_id
        )
        if not picking:
            return self._response_put_in_pack(
                picking_batch_id,
                message=self.msg_store.stock_picking_not_found(),
            )
        if not picking.is_shopfloor_packing_todo:
            return self._response_put_in_pack(
                picking_batch_id,
                message=self.msg_store.stock_picking_already_packed(picking),
            )
        if nbr_packages <= 0:
            return self._response_put_in_pack(
                picking_batch_id,
                message=self.msg_store.nbr_packages_must_be_greated_than_zero(),
            )
        savepoint = self._actions_for("savepoint").new()
        pack = self._put_in_pack(picking, nbr_packages)
        picking._reset_packing_packs_scanned()
        if not pack:
            savepoint.rollback()
            return self._response_put_in_pack(
                picking_batch_id,
                message=self.msg_store.notable_to_put_in_pack(picking),
            )
        self._postprocess_put_in_pack(picking, pack)
        return self._response_put_in_pack(
            picking_batch_id,
            message=self.msg_store.stock_picking_packed_successfully(picking),
        )

    def _postprocess_put_in_pack(self, picking, pack):
        """Override this method to include post-processing logic for the new package,
        such as printing.."""
        return

    def _put_in_pack(self, picking, number_of_parcels):
        move_lines_to_pack = picking.move_line_ids.filtered(
            lambda l: l.result_package_id and l.result_package_id.is_internal
        )
        pack = picking._put_in_pack(move_lines_to_pack)
        if (
            isinstance(pack, dict)
            and pack.get("res_model") == "stock.quant.package"
            and pack.get("res_id")
        ):
            pack = self.env["stock.quant.package"].browse(pack.get("res_id"))
        if isinstance(pack, self.env["stock.quant.package"].__class__):
            pack.number_of_parcels = number_of_parcels
        return pack

    def _response_put_in_pack(self, picking_batch_id, message=None):
        res = self.prepare_unload(picking_batch_id)
        if message:
            res["message"] = message
        return res


class ShopfloorClusterPickingValidator(Component):
    """Validators for the Cluster Picking endpoints."""

    _inherit = "shopfloor.cluster_picking.validator"

    def put_in_pack(self):
        return {
            "picking_batch_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "nbr_packages": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def scan_packing_to_pack(self):
        return {
            "picking_batch_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }


class ShopfloorClusterPickingValidatorResponse(Component):
    """Validators for the Cluster Picking endpoints responses."""

    _inherit = "shopfloor.cluster_picking.validator.response"

    def _states(self):
        states = super()._states()
        states["pack_picking_put_in_pack"] = self.schemas_detail.pack_picking_detail()
        states["pack_picking_scan_pack"] = self.schemas_detail.pack_picking_detail()
        return states

    @property
    def _schema_pack_picking(self):
        schema = self.schemas_detail.pack_picking_detail()
        return {"type": "dict", "nullable": True, "schema": schema}

    def prepare_unload(self):
        res = super().prepare_unload()
        res["data"]["schema"]["pack_picking_put_in_pack"] = self._schema_pack_picking
        res["data"]["schema"]["pack_picking_scan_pack"] = self._schema_pack_picking
        return res

    def put_in_pack(self):
        return self.prepare_unload()

    def confirm_start(self):
        res = super().confirm_start()
        res["data"]["schema"]["pack_picking_put_in_pack"] = self._schema_pack_picking
        res["data"]["schema"]["pack_picking_scan_pack"] = self._schema_pack_picking
        return res

    def scan_destination_pack(self):
        res = super().scan_destination_pack()
        res["data"]["schema"]["pack_picking_put_in_pack"] = self._schema_pack_picking
        res["data"]["schema"]["pack_picking_scan_pack"] = self._schema_pack_picking
        return res

    def scan_packing_to_pack(self):
        return self._response_schema(
            next_states={
                "unload_all",
                "unload_single",
                "pack_picking_put_in_pack",
                "pack_picking_scan_pack",
            }
        )
