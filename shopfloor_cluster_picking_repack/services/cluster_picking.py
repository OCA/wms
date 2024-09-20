# Copyright 2021 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .packaging import PackagingAction


class ClusterPicking(Component):

    _inherit = "shopfloor.cluster.picking"

    def _get_available_delivery_packaging(self, picking):
        model = self.env["stock.package.type"]
        carrier = picking.ship_carrier_id or picking.carrier_id
        wizard_obj = self.env["choose.delivery.package"]
        delivery_type = (
            carrier.delivery_type
            if carrier.delivery_type not in ("fixed", False)
            else "none"
        )
        wizard = wizard_obj.with_context(
            current_package_carrier_type=delivery_type
        ).new({"picking_id": picking.id})
        if not carrier:
            return model.browse()
        return model.search(
            wizard.package_type_domain,
            order="number_of_parcels,name",
        )

    def list_delivery_packaging(self, picking_batch_id, picking_id, selected_line_ids):
        """List available delivery packaging for given picking.

        Transitions:
        * select_delivery_packaging: list available delivery packaging, the
        user has to choose one to create the new package
        * select_package: when no delivery packaging is available
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_start(message=message)
        selected_lines = self.env["stock.move.line"].browse(selected_line_ids).exists()
        delivery_packaging = self._get_available_delivery_packaging(picking)
        if not delivery_packaging:
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=self.msg_store.no_delivery_packaging_available(),
            )
        response = self._check_allowed_qty_done(picking, selected_lines)
        if response:
            return response
        return self._response_for_select_delivery_packaging(picking, delivery_packaging)

    def scan_package_action(self, picking_id, selected_line_ids, barcode):
        """Scan a package, a lot, a product or a package to handle a line

        When a package is scanned (only delivery ones), if the package is known
        as the destination package of one of the lines or is the source package
        of a selected line, the package is set to be the destination package of
        all the lines to pack.

        When a product is scanned, it selects (set qty_done = reserved qty) or
        deselects (set qty_done = 0) the move lines for this product. Only
        products not tracked by lot can use this.

        When a lot is scanned, it does the same as for the products but based
        on the lot.

        When a packaging type (one without related product) is scanned, a new
        package is created and set as destination of the lines to pack.

        Lines to pack are move lines in the list of ``selected_line_ids``
        where ``qty_done`` > 0 and have not been packed yet
        (``shopfloor_checkout_done is False``).

        Transitions:
        * select_package: when a product or lot is scanned to select/deselect,
        the client app has to show the same screen with the updated selection
        * select_line: when a package or packaging type is scanned, move lines
        have been put in package and we can return back to this state to handle
        the other lines
        * summary: if there is no other lines, go to the summary screen to be able
        to close the stock picking
        """
        packaging_action: PackagingAction = self._actions_for("packaging")
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)

        selected_lines = self.env["stock.move.line"].browse(selected_line_ids).exists()
        search_result = packaging_action._scan_package_find(picking, barcode)
        message = packaging_action._check_scan_package_find(picking, search_result)
        if message:
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=message,
            )
        if search_result and search_result.type == "delivery_packaging":
            package_type_id = search_result.record.id
        else:
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=self.msg_store.package_not_found_for_barcode(barcode),
            )
        # Call the specific put in pack with package type filled in
        return self._put_in_pack(self, picking, package_type_id=package_type_id)

    @property
    def default_pick_pack_action(self):
        return self.work.menu.default_pack_pickings_action

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

    def _get_move_lines_to_pack(self, picking):
        return picking.move_line_ids.filtered(
            lambda ml: ml.result_package_id.is_internal
        ).sorted(key=lambda ml: ml.result_package_id.name)

    def _prepare_pack_picking(self, batch, message=None):
        picking = self._get_next_picking_to_pack(batch)
        move_lines = self._get_move_lines_to_pack(picking)
        if not picking:
            return self._response_put_in_pack(
                batch.id,
                message=self.msg_store.stock_picking_packed_successfully(picking),
            )
        if picking.is_shopfloor_packing_pack_to_scan():
            return self._response_pack_picking_scan_pack(picking, message=message)
        if self.default_pick_pack_action == "nbr_packages":
            return self._response_pack_picking_put_in_pack(picking, message=message)
        else:
            return self._response_for_select_package(
                picking, move_lines, message=message
            )
        # return self._response_pack_picking_put_in_pack(picking, message=message)

    def prepare_unload(self, picking_batch_id):
        # before initializing the unloading phase we put picking in pack if
        # required by the scenario
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()
        if not self.work.menu.pack_pickings or not batch.is_shopfloor_packing_todo:
            return super().prepare_unload(picking_batch_id)
        return self._prepare_pack_picking(batch)

    def put_in_pack(
        self, picking_batch_id, picking_id, nbr_packages=None, package_type_id=None
    ):
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()
        picking = batch.picking_ids.filtered(
            lambda p, picking_id=picking_id: p.id == picking_id
        )

        # Check if parameters are correct
        packaging_action: PackagingAction = self._actions_for("packaging")
        result = packaging_action._check_put_in_pack(
            picking_batch_id,
            picking,
            self._response_put_in_pack,
            nbr_packages=nbr_packages,
            package_type_id=package_type_id,
        )
        if result:
            return result

        savepoint = self._actions_for("savepoint").new()
        pack = self._put_in_pack(picking, nbr_packages, package_type_id)
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

    def _put_in_pack(self, picking, number_of_parcels=None, package_type_id=None):
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
            # Enhance package details either with number of packages or package_type
            if number_of_parcels:
                pack.number_of_parcels = number_of_parcels
            elif package_type_id:
                pack.package_type_id = self.env["stock.package.type"].browse(
                    package_type_id
                )
        return pack

    def _response_put_in_pack(self, picking_batch_id, message=None):
        """
        Fallback to prepare_unload
        """
        res = self.prepare_unload(picking_batch_id)
        if message:
            res["message"] = message
        return res

    def _data_for_packing_info(self, picking):
        """Return the packing information

        Intended to be extended.
        """
        # TODO: This could be avoided if included in the picking parser.
        return ""

    def _response_for_select_package(self, picking, lines, message=None):
        return self._response(
            next_state="select_package",
            data=self.data.select_package(picking, lines),
            message=message,
        )

    def _response_for_select_dest_package(self, picking, message=None):
        packages = picking.mapped("move_line_ids.result_package_id").filtered(
            "package_type_id"
        )
        if not packages:
            # FIXME: do we want to move from 'select_dest_package' to
            # 'select_package' state? Until now (before enforcing the use of
            # delivery package) this part of code was never reached as we
            # always had a package on the picking (source or result)
            # Also the response validator did not support this state...
            return self._response_for_select_package(
                picking,
                message=self.msg_store.no_valid_package_to_select(),
            )
        picking_data = self.data.picking(picking)
        packages_data = self.data.packages(
            packages.with_context(picking_id=picking.id).sorted(),
            picking=picking,
            with_packaging=True,
            with_package_move_line_count=True,
        )
        return self._response(
            next_state="select_dest_package",
            data={
                "picking": picking_data,
                "packages": packages_data,
                # "selected_move_lines": self._data_for_move_lines(move_lines.sorted()),
            },
            message=message,
        )

    def _data_for_delivery_packaging(self, packaging, **kw):
        return self.data.delivery_packaging_list(packaging, **kw)

    def _response_for_select_delivery_packaging(self, picking, packaging, message=None):
        return self._response(
            next_state="select_delivery_packaging",
            data={
                "picking": self.data.picking(picking),
                "packaging": self._data_for_delivery_packaging(packaging),
            },
            message=message,
        )

    def _check_allowed_qty_done(self, picking, lines):
        for line in lines:
            # Do not allow to proceed if the qty_done of
            # any of the selected lines
            # is higher than the quantity to do.
            if line.qty_done > line.reserved_uom_qty:
                return self._response_for_select_package(
                    picking,
                    lines,
                    message=self.msg_store.selected_lines_qty_done_higher_than_allowed(),
                )


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
            "nbr_packages": {"coerce": to_int, "required": False, "type": "integer"},
            "package_type_id": {"coerce": to_int, "required": False, "type": "integer"},
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

    def list_delivery_packaging(self) -> dict:
        return {
            "picking_batch_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
        }

    def scan_package_action(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "barcode": {"required": True, "type": "string"},
        }


class ShopfloorClusterPickingValidatorResponse(Component):
    """Validators for the Cluster Picking endpoints responses."""

    _inherit = "shopfloor.cluster_picking.validator.response"

    def _states(self) -> dict:
        states = super()._states()
        states["pack_picking_put_in_pack"] = self.schemas_detail.pack_picking_detail()
        states["pack_picking_scan_pack"] = self.schemas_detail.pack_picking_detail()
        states["select_package"] = self.schemas.select_package()
        states["select_delivery_packaging"] = self._schema_select_delivery_packaging
        return states

    @property
    def _schema_pack_picking(self):
        schema = self.schemas_detail.pack_picking_detail()
        return {"type": "dict", "nullable": True, "schema": schema}

    @property
    def _schema_select_package(self):
        schema = self.schemas.select_package()
        return {"type": "dict", "nullable": True, "schema": schema}

    def prepare_unload(self):
        res = super().prepare_unload()
        res["data"]["schema"]["pack_picking_put_in_pack"] = self._schema_pack_picking
        res["data"]["schema"]["pack_picking_scan_pack"] = self._schema_pack_picking
        res["data"]["schema"]["select_package"] = self._schema_select_package
        return res

    def put_in_pack(self):
        return self.prepare_unload()

    def confirm_start(self):
        res = super().confirm_start()
        res["data"]["schema"]["pack_picking_put_in_pack"] = self._schema_pack_picking
        res["data"]["schema"]["pack_picking_scan_pack"] = self._schema_pack_picking
        res["data"]["schema"]["select_package"] = self._schema_select_package
        return res

    def select_package(self):
        res = self._response_schema(
            next_states={"select_delivery_packaging", "select_package"}
        )
        res["data"]["schema"]["select_package"] = self._schema_select_package
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
                "select_package",
            }
        )

    def list_delivery_packaging(self):
        return self._response_schema(
            next_states={"select_delivery_packaging", "select_package"}
        )

    @property
    def _schema_select_delivery_packaging(self):
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "packaging": self.schemas._schema_list_of(
                self.schemas.delivery_packaging()
            ),
        }

    def scan_package_action(self):
        return self.select_package()
