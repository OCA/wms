# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_picking_base import ClusterPickingCommonCase


class ClusterPickingChangePackLotCase(ClusterPickingCommonCase):
    """Tests covering the /change_pack_lot endpoint

    Only simple cases are tested to check the flow of responses on success and
    error, the "change.package.lot" component is tested in its own tests.
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.batch = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=10)]]
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
                data=self._line_data(line),
            )
        else:
            self.assert_response(
                response,
                message=message,
                next_state="change_pack_lot",
                data=self._line_data(line),
            )
        return response

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
            message=self.service.msg_store.package_replaced_by_package(
                initial_package, new_package
            ),
        )

        self.assertRecordValues(
            line,
            [
                {
                    "package_id": new_package.id,
                    "result_package_id": new_package.id,
                    "product_qty": 10.0,
                }
            ],
        )
        self.assertRecordValues(line.package_level_id, [{"package_id": new_package.id}])

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
            message=self.service.msg_store.lot_replaced_by_lot(initial_lot, new_lot),
        )
        self.assertRecordValues(line, [{"lot_id": new_lot.id}])

    def test_change_pack_lot_change_error(self):
        initial_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=initial_lot)
        self._simulate_batch_selected(self.batch, fill_stock=False)
        line = self.batch.picking_ids.move_line_ids
        # ensure we have our new package in the same location
        self._test_change_pack_lot(
            line,
            "NOT_FOUND",
            success=False,
            message=self.service.msg_store.no_package_or_lot_for_barcode("NOT_FOUND"),
        )
