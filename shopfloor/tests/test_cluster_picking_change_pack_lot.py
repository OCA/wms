from collections import namedtuple

from odoo.tests.common import Form

from .test_cluster_picking_base import ClusterPickingCommonCase


class ClusterPickingChangePackLotCommon(ClusterPickingCommonCase):

    # used by _create_package_in_location
    PackageContent = namedtuple(
        "PackageContent",
        # recordset of the product,
        # quantity in float
        # recordset of the lot (optional)
        "product quantity lot",
    )

    def _create_package_in_location(self, location, content):
        """Create a package and quants in a location

        content is a list of PackageContent
        """
        package = self.env["stock.quant.package"].create({})
        for product, quantity, lot in content:
            self._update_qty_in_location(
                location, product, quantity, package=package, lot=lot
            )
        return package

    def _create_lot(self, product):
        return self.env["stock.production.lot"].create(
            {"product_id": product.id, "company_id": self.env.company.id}
        )

    def _test_change_pack_lot(self, line, barcode, success=True, message=None):
        batch = line.picking_id.batch_id
        response = self.service.dispatch(
            "change_pack_lot",
            params={
                "picking_batch_id": batch.id,
                "move_line_id": line.id,
                "barcode": barcode,
            },
        )
        if success:
            self.assert_response(
                response,
                message=message,
                next_state="scan_destination",
                data=self._line_data(line, qty_by_packaging=True),
            )
        else:
            self.assert_response(
                response,
                message=message,
                next_state="change_pack_lot",
                data=self._line_data(line, qty_by_packaging=True),
            )

    def _skip_line(self, line, next_line=None):
        batch = line.picking_id.batch_id
        response = self.service.dispatch(
            "skip_line", params={"picking_batch_id": batch.id, "move_line_id": line.id}
        )
        if next_line:
            self.assert_response(
                response, next_state="start_line", data=self._line_data(next_line)
            )
        return response

    def assert_quant_reserved_qty(self, move_line, qty_func, package=None, lot=None):
        domain = [
            ("location_id", "=", move_line.location_id.id),
            ("product_id", "=", move_line.product_id.id),
        ]
        if package:
            domain.append(("package_id", "=", package.id))
        if lot:
            domain.append(("lot_id", "=", lot.id))
        quant = self.env["stock.quant"].search(domain)
        self.assertEqual(quant.reserved_quantity, qty_func())

    def assert_quant_package_qty(self, location, package, qty_func):
        quant = self.env["stock.quant"].search(
            [("location_id", "=", location.id), ("package_id", "=", package.id)]
        )
        self.assertEqual(quant.quantity, qty_func())

    def assert_control_stock_inventory(self, location, product, lot):
        inventory = self.env["stock.inventory"].search([], order="id desc", limit=1)
        self.assertRecordValues(
            inventory,
            [
                {
                    "state": "draft",
                    "product_ids": product.ids,
                    "name": "Pick: stock issue on lot: {} found in {}".format(
                        lot.name, location.name
                    ),
                },
            ],
        )


class ClusterPickingChangePackLotCase(ClusterPickingChangePackLotCommon):
    """Tests covering the /change_pack_lot endpoint"""

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.batch = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=10)]]
        )

    def test_change_pack_lot_change_pack_ok(self):
        initial_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )
        self._simulate_batch_selected(self.batch, fill_stock=False)

        # ensure we have our new package in the same location
        new_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )

        line = self.batch.picking_ids.move_line_ids
        self._test_change_pack_lot(
            line,
            new_package.name,
            success=True,
            message={
                "message_type": "success",
                "body": "Package {} replaced by package {}".format(
                    initial_package.name, new_package.name
                ),
            },
        )

        self.assertRecordValues(
            line, [{"package_id": new_package.id, "result_package_id": new_package.id}]
        )

        self.assertRecordValues(line.package_level_id, [{"package_id": new_package.id}])
        # check that reservations have been updated
        self.assert_quant_reserved_qty(line, lambda: 0, package=initial_package)
        self.assert_quant_reserved_qty(
            line, lambda: line.product_qty, package=new_package
        )

    def test_change_pack_lot_change_pack_different_location(self):
        initial_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )

        # initial_package from shelf1 will be selected in our move line
        self._simulate_batch_selected(self.batch, fill_stock=False)

        # put a package in shelf2 in the system, but we assume that in real,
        # the operator put it in shelf1
        new_package = self._create_package_in_location(
            self.shelf2, [self.PackageContent(self.product_a, 10, lot=None)]
        )

        line = self.batch.picking_ids.move_line_ids
        # when the operator wants to pick the initial package, in shelf1, the new
        # package is in front of the other so they want to change the package
        self._test_change_pack_lot(
            line,
            new_package.name,
            success=True,
            message={
                "message_type": "success",
                "body": "Package {} replaced by package {}".format(
                    initial_package.name, new_package.name
                ),
            },
        )

        self.assertRecordValues(
            line, [{"package_id": new_package.id, "result_package_id": new_package.id}]
        )
        self.assertRecordValues(line.package_level_id, [{"package_id": new_package.id}])
        # check that reservations have been updated, the new package is not
        # supposed to be in shelf2 anymore, and we should have no reserved qty
        # for the initial package anymore
        self.assert_quant_package_qty(self.shelf2, new_package, lambda: 0)
        self.assert_quant_reserved_qty(line, lambda: 0, package=initial_package)
        self.assert_quant_reserved_qty(
            line, lambda: line.product_qty, package=new_package
        )

    def test_change_pack_lot_change_lot_in_package_ok(self):
        self.product_a.tracking = "lot"
        initial_lot = self._create_lot(self.product_a)
        initial_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=initial_lot)]
        )
        self._simulate_batch_selected(self.batch, fill_stock=False)
        # ensure we have our new package in the same location
        new_lot = self._create_lot(self.product_a)
        new_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=new_lot)]
        )
        line = self.batch.picking_ids.move_line_ids
        self._test_change_pack_lot(
            line,
            new_lot.name,
            success=True,
            message={
                "message_type": "success",
                "body": "Package {} replaced by package {}".format(
                    initial_package.name, new_package.name
                ),
            },
        )

        self.assertRecordValues(
            line,
            [
                {
                    "package_id": new_package.id,
                    "result_package_id": new_package.id,
                    "lot_id": new_lot.id,
                }
            ],
        )
        self.assertRecordValues(line.package_level_id, [{"package_id": new_package.id}])
        # check that reservations have been updated
        self.assert_quant_reserved_qty(line, lambda: 0, package=initial_package)
        self.assert_quant_reserved_qty(
            line, lambda: line.product_qty, package=new_package
        )

    def test_change_pack_lot_change_lot_in_several_packages_error(self):
        self.product_a.tracking = "lot"
        initial_lot = self._create_lot(self.product_a)
        self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=initial_lot)]
        )
        self._simulate_batch_selected(self.batch, fill_stock=False)
        line = self.batch.picking_ids.move_line_ids
        # create 2 packages for the same new lot in the same location
        new_lot = self._create_lot(self.product_a)
        self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, new_lot)]
        )
        self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, new_lot)]
        )
        self._test_change_pack_lot(
            line,
            new_lot.name,
            success=False,
            message={
                "message_type": "warning",
                "body": "Several packages found in {},"
                " please scan a package.".format(self.shelf1.name),
            },
        )

    def test_change_pack_lot_change_lot_from_package_error(self):
        # we shouldn't be allowed to replace a package by a lot
        # if the lot is not a package in the quants (because we
        # could then replace a package by a single unit)
        self.product_a.tracking = "lot"
        initial_lot = self._create_lot(self.product_a)
        self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=initial_lot)]
        )
        self._simulate_batch_selected(self.batch, fill_stock=False)
        line = self.batch.picking_ids.move_line_ids
        # create a lot and put a unit in the location without package
        new_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, line.product_id, 1, lot=new_lot)
        self._test_change_pack_lot(
            line,
            new_lot.name,
            success=False,
            message={
                "message_type": "error",
                "body": "Lot {} is not a package.".format(new_lot.name),
            },
        )

    def test_change_pack_lot_change_lot_ok(self):
        initial_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=initial_lot)
        self._simulate_batch_selected(self.batch, fill_stock=False)
        line = self.batch.picking_ids.move_line_ids
        source_location = line.location_id
        new_lot = self._create_lot(self.product_a)
        # ensure we have our new package in the same location
        self._update_qty_in_location(source_location, line.product_id, 10, lot=new_lot)
        self._test_change_pack_lot(
            line,
            new_lot.name,
            success=True,
            message={
                "message_type": "success",
                "body": "Lot {} replaced by lot {}.".format(
                    initial_lot.name, new_lot.name
                ),
            },
        )

        self.assertRecordValues(line, [{"lot_id": new_lot.id}])
        # check that reservations have been updated
        self.assert_quant_reserved_qty(line, lambda: 0, lot=initial_lot)
        self.assert_quant_reserved_qty(line, lambda: line.product_qty, lot=new_lot)

    def test_change_pack_lot_change_lot_different_location_ok(self):
        self.product_a.tracking = "lot"
        initial_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=initial_lot)
        self._simulate_batch_selected(self.batch, fill_stock=False)
        line = self.batch.picking_ids.move_line_ids
        new_lot = self._create_lot(self.product_a)
        # ensure we have our new package in a different location
        self._update_qty_in_location(self.shelf2, line.product_id, 10, lot=new_lot)
        self._test_change_pack_lot(
            line,
            new_lot.name,
            success=True,
            message={
                "message_type": "success",
                "body": "Lot {} replaced by lot {}. A draft inventory has"
                " been created for control.".format(initial_lot.name, new_lot.name),
            },
        )

        self.assertRecordValues(line, [{"lot_id": new_lot.id}])
        # check that reservations have been updated
        self.assert_quant_reserved_qty(line, lambda: 0, lot=initial_lot)
        self.assert_quant_reserved_qty(line, lambda: line.product_qty, lot=new_lot)
        self.assert_control_stock_inventory(self.shelf1, line.product_id, new_lot)


class ClusterPickingChangePackLotCaseSpecial(ClusterPickingChangePackLotCommon):
    """Tests covering the /change_pack_lot endpoint

    Special cases where we use a custom batch transfer
    """

    def _create_picking_with_package_level(self, packages):
        picking_form = Form(self.env["stock.picking"])
        picking_form.partner_id = self.customer
        picking_form.origin = "test"
        picking_form.picking_type_id = self.picking_type
        picking_form.location_id = self.stock_location
        picking_form.location_dest_id = self.packing_location
        for package in packages:
            with picking_form.package_level_ids_details.new() as move:
                move.package_id = package
        picking = picking_form.save()
        picking.action_confirm()
        picking.action_assign()
        return picking

    def _create_batch_with_pickings(self, pickings):
        batch_form = Form(self.env["stock.picking.batch"])
        for picking in pickings:
            batch_form.picking_ids.add(picking)
        batch = batch_form.save()
        return batch

    def test_change_pack_lot_change_pack_different_content_error(self):
        # create the initial package, that will be reserved first
        initial_package = self._create_package_in_location(
            self.shelf1,
            [
                self.PackageContent(self.product_a, 10, lot=None),
                self.PackageContent(self.product_b, 10, lot=None),
            ],
        )
        picking = self._create_picking_with_package_level(initial_package)
        batch = self._create_batch_with_pickings(picking)
        self._simulate_batch_selected(batch, fill_stock=False)

        # create a new package in the same location
        # with a different content
        new_package = self._create_package_in_location(
            self.shelf1,
            [
                self.PackageContent(self.product_a, 10, lot=None),
                self.PackageContent(self.product_b, 8, lot=None),
            ],
        )

        lines = batch.picking_ids.move_line_ids
        # try to use the new package, which has a different content,
        # not accepted
        self._test_change_pack_lot(
            lines[0],
            new_package.name,
            success=False,
            message={
                "message_type": "error",
                "body": "Package {} has a different content.".format(new_package.name),
            },
        )

    def test_change_pack_lot_change_pack_multi_content_with_lot(self):
        (self.product_a + self.product_b).tracking = "lot"
        # create a package with 2 products tracked by lot, stored in shelf1
        # this package is reserved first on the move line
        initial_lot_a = self._create_lot(self.product_a)
        initial_lot_b = self._create_lot(self.product_b)
        initial_package = self._create_package_in_location(
            self.shelf1,
            [
                self.PackageContent(self.product_a, 10, initial_lot_a),
                self.PackageContent(self.product_b, 10, initial_lot_b),
            ],
        )

        # create and reserve our transfer using the initial package
        picking = self._create_picking_with_package_level(initial_package)
        batch = self._create_batch_with_pickings(picking)
        self._simulate_batch_selected(batch, fill_stock=False)

        lines = picking.move_line_ids
        package_level = lines.mapped("package_level_id")

        # create a second package with the same content, which will be used
        # as replacement
        new_lot_a = self._create_lot(self.product_a)
        new_lot_b = self._create_lot(self.product_b)
        new_package = self._create_package_in_location(
            self.shelf1,
            [
                self.PackageContent(self.product_a, 10, new_lot_a),
                self.PackageContent(self.product_b, 10, new_lot_b),
            ],
        )
        # changing the package of the first line will change all of them
        self._test_change_pack_lot(
            lines[0],
            new_package.name,
            success=True,
            message={
                "message_type": "success",
                "body": "Package {} replaced by package {}".format(
                    initial_package.name, new_package.name
                ),
            },
        )

        self.assertRecordValues(
            lines,
            [
                {
                    "package_id": new_package.id,
                    "result_package_id": new_package.id,
                    "lot_id": new_lot_a.id,
                },
                {
                    "package_id": new_package.id,
                    "result_package_id": new_package.id,
                    "lot_id": new_lot_b.id,
                },
            ],
        )

        self.assertRecordValues(package_level, [{"package_id": new_package.id}])
        # check that reservations have been updated
        for line in lines:
            self.assert_quant_reserved_qty(line, lambda: 0, package=initial_package)
            self.assert_quant_reserved_qty(
                line, lambda: line.product_qty, package=new_package
            )

    def test_change_pack_lot_change_pack_steal_from_other_move_line(self):
        # create 2 picking, each with its own package
        package1 = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)],
        )
        picking1 = self._create_picking_with_package_level(package1)
        self.assertEqual(picking1.move_line_ids.package_id, package1)

        package2 = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)],
        )
        picking2 = self._create_picking_with_package_level(package2)
        self.assertEqual(picking2.move_line_ids.package_id, package2)

        batch = self._create_batch_with_pickings(picking1 + picking2)
        self._simulate_batch_selected(batch, fill_stock=False)

        line = picking1.move_line_ids
        # We "steal" package2 for the picking1
        self._test_change_pack_lot(
            line,
            package2.name,
            success=True,
            message={
                "message_type": "success",
                "body": "Package {} replaced by package {}".format(
                    package1.name, package2.name
                ),
            },
        )

        self.assertRecordValues(
            picking1.move_line_ids,
            [
                {
                    "package_id": package2.id,
                    "result_package_id": package2.id,
                    "state": "assigned",
                }
            ],
        )
        self.assertRecordValues(
            picking2.move_line_ids,
            [
                {
                    "package_id": package1.id,
                    "result_package_id": package1.id,
                    "state": "assigned",
                }
            ],
        )
        self.assertRecordValues(
            picking1.package_level_ids,
            [{"package_id": package2.id, "state": "assigned"}],
        )
        self.assertRecordValues(
            picking2.package_level_ids,
            [{"package_id": package1.id, "state": "assigned"}],
        )
        # check that reservations have been updated
        self.assert_quant_reserved_qty(
            picking1.move_line_ids,
            lambda: picking1.move_line_ids.product_qty,
            package=package2,
        )
        self.assert_quant_reserved_qty(
            picking2.move_line_ids,
            lambda: picking2.move_line_ids.product_qty,
            package=package1,
        )
