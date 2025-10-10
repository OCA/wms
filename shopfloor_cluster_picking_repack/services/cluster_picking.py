# Copyright 2021 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.stock.models.stock_move_line import StockMoveLine
from odoo.addons.stock.models.stock_package_type import PackageType
from odoo.addons.stock.models.stock_picking import Picking
from odoo.addons.stock.models.stock_quant import QuantPackage

from .packing import PackingAction


class ClusterPicking(Component):
    _inherit = "shopfloor.cluster.picking"

    # PUBLIC METHODS - ENDPOINTS

    def list_delivery_package_types(
        self, picking_batch_id, picking_id, selected_line_ids
    ) -> dict:
        """List available delivery package types for given picking.

        Transitions:
        * select_delivery_package_types: list available delivery package types, the
        user has to choose one to create the new package
        * select_package: when no delivery package types are available
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_start(message=message)
        selected_lines = self.env["stock.move.line"].browse(selected_line_ids).exists()
        delivery_package_type = self._get_available_delivery_package_type(picking)
        if not delivery_package_type:
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=self.msg_store.no_package_type_available(),
            )
        response = self._check_allowed_qty_picked(picking, selected_lines)
        if response:
            return response
        return self._response_for_select_delivery_package_type(
            picking, delivery_package_type, selected_lines
        )

    def scan_package_action(self, picking_id, selected_line_ids, barcode) -> dict:
        """Scan a package, a lot, a product or a package to handle a line

        When a package is scanned (only delivery ones), if the package is known
        as the destination package of one of the lines or is the source package
        of a selected line, the package is set to be the destination package of
        all the lines to pack.

        When a product is scanned, it selects (set qty_picked = reserved qty) or
        deselects (set qty_picked = 0) the move lines for this product. Only
        products not tracked by lot can use this.

        When a lot is scanned, it does the same as for the products but based
        on the lot.

        When a package type is scanned, a new
        package is created and set as destination of the lines to pack.

        Lines to pack are move lines in the list of ``selected_line_ids``
        where ``picked`` is set and have not been packed yet
        (``shopfloor_checkout_done is False``).

        Transitions:
        * select_package: when a product or lot is scanned to select/deselect,
        the client app has to show the same screen with the updated selection
        * select_line: when a package or package type is scanned, move lines
        have been put in package and we can return back to this state to handle
        the other lines
        * summary: if there is no other lines, go to the summary screen to be able
        to close the stock picking
        """
        packing_action: PackingAction = self._actions_for("packing")
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)

        selected_lines = self.env["stock.move.line"].browse(selected_line_ids).exists()
        search_result = packing_action._scan_package_find(picking, barcode)
        message = packing_action._check_scan_package_find(picking, search_result)
        if message:
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=message,
            )
        if search_result and search_result.type == "package_type":
            package_type_id = search_result.record.id
        else:
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=self.msg_store.package_not_found_for_barcode(barcode),
            )
        # Call the specific put in pack with package type filled in
        return self.put_in_pack(
            picking.batch_id.id,
            picking.id,
            selected_line_ids=selected_line_ids,
            package_type_id=package_type_id,
        )

    def scan_destination_pack(
        self, picking_batch_id, move_line_id, barcode, quantity
    ) -> dict:
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
                move_line,
                message=self.msg_store.bin_should_be_internal(bin_package),
                qty_done=quantity,
            )
        return super().scan_destination_pack(
            picking_batch_id, move_line_id, barcode, quantity
        )

    def scan_packing_to_pack(self, picking_batch_id, picking_id, barcode) -> dict:
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

    def prepare_unload(self, picking_batch_id) -> dict:
        # before initializing the unloading phase we put picking in pack if
        # required by the scenario
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()
        if not self.work.menu.pack_pickings or not batch.is_shopfloor_packing_todo:
            return super().prepare_unload(picking_batch_id)
        return self._prepare_pack_picking(batch)

    def put_in_pack(
        self,
        picking_batch_id,
        picking_id,
        selected_line_ids,
        nbr_packages=None,
        package_type_id=None,
    ) -> dict:
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()
        picking = batch.picking_ids.filtered(
            lambda p, picking_id=picking_id: p.id == picking_id
        )

        package_type = self.env["stock.package.type"].browse(package_type_id)
        if not package_type and nbr_packages:
            package_type = self._get_suitable_package_type(nbr_packages)
            if package_type:
                package_type_id = package_type.id
                nbr_packages = None

        # Check if parameters are correct
        packing_action: PackingAction = self._actions_for("packing")
        result = packing_action._check_put_in_pack(
            picking_batch_id,
            picking,
            self._response_put_in_pack,
            nbr_packages=nbr_packages,
            package_type_id=package_type_id,
        )
        if result:
            return result

        lines = self.env["stock.move.line"].browse(selected_line_ids).exists()
        savepoint = self._actions_for("savepoint").new()
        pack = self._put_in_pack(picking, lines, nbr_packages, package_type_id)
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

    # HELPER METHODS
    def _get_suitable_package_type(self, number_of_parcels):
        return self.env["stock.package.type"].search(
            [
                ("number_of_parcels", "=", number_of_parcels),
                ("package_carrier_type", "=", "none"),
            ],
            limit=1,
        )

    @property
    def default_pick_pack_action(self):
        return self.work.menu.default_pack_pickings_action

    def _get_available_delivery_package_type(self, picking) -> PackageType:
        """
        This returns available packages types for the carrier if defined
        or package types that have "none" delivery type.

        The returned package types are ordered by number of parcels then
        by name.
        """
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

    def _last_picked_line(self, picking) -> StockMoveLine:
        # a complete override to add a condition on internal package
        # TODO: Add a hook to avoid re-writing this
        return fields.first(
            picking.move_line_ids.filtered(
                lambda line: line.picked
                and line.result_package_id.is_internal
                # if we are moving the entire package, we shouldn't
                # add stuff inside it, it's not a new package
                and line.package_id != line.result_package_id
            ).sorted(key="write_date", reverse=True)
        )

    def _get_next_picking_to_pack(self, batch) -> Picking:
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
        return fields.first(move_lines).picking_id

    def _get_move_lines_to_pack(self, picking) -> StockMoveLine:
        """
        This returns the lines that have an internal package
        and the same destination
        """
        move_lines = picking.move_line_ids.filtered(
            lambda ml: ml.result_package_id.is_internal
        ).sorted(key=lambda ml: ml.result_package_id.name)
        # Take the first line to filter then the lines per destination
        first_line = fields.first(move_lines)
        return move_lines.filtered(
            lambda line: line.location_dest_id == first_line.location_dest_id
        )

    def _prepare_pack_picking(self, batch, message=None) -> dict:
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

    def _postprocess_put_in_pack(self, picking, pack):
        """Override this method to include post-processing logic for the new package,
        such as printing.."""
        return

    def _put_in_pack(
        self, picking, move_lines, number_of_parcels=None, package_type_id=None
    ) -> QuantPackage:
        """
        This will enhance the put in pack flow by adding the number
        of parcels or the package type to the generated package.
        """
        pack = picking._put_in_pack(move_lines)
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

    def _data_for_packing_info(self, picking):
        """Return the packing information

        Intended to be extended.
        """
        # TODO: This could be avoided if included in the picking parser.
        return ""

    def _data_for_delivery_package_type(self, package_type, **kw):
        return self.data.package_type_list(package_type, **kw)

    def _check_allowed_qty_picked(self, picking, lines) -> dict:
        for line in lines:
            # Do not allow to proceed if the picked qty of
            # any of the selected lines
            # is higher than the quantity to do.
            if line.qty_picked > line.quantity:
                return self._response_for_select_package(
                    picking,
                    lines,
                    message=self.msg_store.selected_lines_qty_picked_higher_than_allowed(
                        line
                    ),
                )

    # RESPONSES

    def _response_pack_picking_put_in_pack(self, picking, message=None) -> dict:
        data = self.data.pack_picking(picking)
        return self._response(
            next_state="pack_picking_put_in_pack", data=data, message=message
        )

    def _response_pack_picking_scan_pack(self, picking, message=None) -> dict:
        data = self.data.pack_picking(picking)
        return self._response(
            next_state="pack_picking_scan_pack", data=data, message=message
        )

    def _response_for_select_package(self, picking, lines, message=None) -> dict:
        return self._response(
            next_state="select_package",
            data=self.data.select_package(picking, lines),
            message=message,
        )

    def _response_for_select_dest_package(self, picking, message=None) -> dict:
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
            with_package_type=True,
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

    def _response_for_select_delivery_package_type(
        self, picking, package_type, selected_lines, message=None
    ) -> dict:
        return self._response(
            next_state="select_delivery_package_type",
            data={
                "picking": self.data.picking(picking),
                "selected_lines_for_packing": self.data.move_lines(selected_lines),
                "package_type": self._data_for_delivery_package_type(package_type),
            },
            message=message,
        )

    def _response_put_in_pack(self, picking_batch_id, message=None) -> dict:
        """
        Fallback to prepare_unload
        """
        res = self.prepare_unload(picking_batch_id)
        if message:
            res["message"] = message
        return res


class ShopfloorClusterPickingValidator(Component):
    """Validators for the Cluster Picking endpoints."""

    _inherit = "shopfloor.cluster_picking.validator"

    def put_in_pack(self) -> dict:
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
            "nbr_packages": {"coerce": to_int, "required": False, "type": "integer"},
            "package_type_id": {"coerce": to_int, "required": False, "type": "integer"},
        }

    def scan_packing_to_pack(self) -> dict:
        return {
            "picking_batch_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def list_delivery_package_types(self) -> dict:
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

    def scan_package_action(self) -> dict:
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
        states["pack_picking_put_in_pack"] = self.schemas.pack_picking()
        states["pack_picking_scan_pack"] = self.schemas.pack_picking()
        states["select_package"] = self.schemas.select_package()
        states["select_delivery_package_type"] = (
            self._schema_select_delivery_package_type
        )
        return states

    @property
    def _schema_pack_picking(self) -> dict:
        schema = self.schemas.pack_picking()
        return {"type": "dict", "nullable": True, "schema": schema}

    @property
    def _schema_select_package(self) -> dict:
        schema = self.schemas.select_package()
        return {"type": "dict", "nullable": True, "schema": schema}

    def prepare_unload(self) -> dict:
        res = super().prepare_unload()
        res["data"]["schema"]["pack_picking_put_in_pack"] = self._schema_pack_picking
        res["data"]["schema"]["pack_picking_scan_pack"] = self._schema_pack_picking
        res["data"]["schema"]["select_package"] = self._schema_select_package
        return res

    def put_in_pack(self) -> dict:
        return self.prepare_unload()

    def confirm_start(self) -> dict:
        res = super().confirm_start()
        res["data"]["schema"]["pack_picking_put_in_pack"] = self._schema_pack_picking
        res["data"]["schema"]["pack_picking_scan_pack"] = self._schema_pack_picking
        res["data"]["schema"]["select_package"] = self._schema_select_package
        return res

    def select_package(self) -> dict:
        res = self._response_schema(
            next_states={"select_delivery_package_type", "select_package"}
        )
        res["data"]["schema"]["select_package"] = self._schema_select_package
        return res

    def scan_destination_pack(self) -> dict:
        res = super().scan_destination_pack()
        res["data"]["schema"]["pack_picking_put_in_pack"] = self._schema_pack_picking
        res["data"]["schema"]["pack_picking_scan_pack"] = self._schema_pack_picking
        return res

    def scan_packing_to_pack(self) -> dict:
        return self._response_schema(
            next_states={
                "unload_all",
                "unload_single",
                "pack_picking_put_in_pack",
                "pack_picking_scan_pack",
                "select_package",
            }
        )

    def list_delivery_package_types(self) -> dict:
        return self._response_schema(
            next_states={"select_delivery_package_type", "select_package"}
        )

    @property
    def _schema_select_delivery_package_type(self) -> dict:
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "selected_lines_for_packing": self.schemas._schema_list_of(
                self.schemas.move_line()
            ),
            "package_type": self.schemas._schema_list_of(self.schemas.package_type()),
        }

    def scan_package_action(self) -> dict:
        return self.prepare_unload()
