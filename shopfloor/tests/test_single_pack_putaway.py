from odoo.tests.common import Form

from .common import CommonCase


class PutawayCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        stock_location = cls.env.ref("stock.stock_location_stock")
        cls.stock_location = stock_location
        cls.dispatch_location = cls.env.ref("stock.location_dispatch_zone")
        cls.dispatch_location.barcode = "DISPATCH"
        cls.input_location = cls.env.ref("stock.stock_location_company")
        cls.shelf1 = cls.env.ref("stock.stock_location_components")
        cls.shelf2 = cls.env.ref("stock.stock_location_14")
        cls.productA = cls.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        cls.packA = cls.env["stock.quant.package"].create(
            {"location_id": stock_location.id}
        )
        cls.env["stock.putaway.rule"].create(
            {
                "product_id": cls.productA.id,
                "location_in_id": cls.stock_location.id,
                "location_out_id": cls.shelf1.id,
            }
        )
        cls.quantA = cls.env["stock.quant"].create(
            {
                "product_id": cls.productA.id,
                "location_id": cls.dispatch_location.id,
                "quantity": 1,
                "package_id": cls.packA.id,
            }
        )
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_put_away_reach_truck")
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="single_pack_putaway")

    def test_start(self):
        """Test the happy path for single pack putaway /start endpoint

        The pre-conditions:

        * A Pack exists in the Input Location (presumably brought there by a
          reception for a PO)
        * A put-away rule moves the product of the Pack from Stock to Stock/Shelf 1

        Expected result:

        * A move is created from Input to Stock/Shelf 1. It is assigned and the package
        level is set to Done.

        The next step in the workflow is to call /validate with the created
        package level that will set the move and picking to done.
        """
        barcode = self.packA.name
        params = {"barcode": barcode}
        # Simulate the client scanning a package's barcode, which
        # in turns should start the operation in odoo
        response = self.service.dispatch("start", params=params)

        # Checks:
        package_level = self.env["stock.package_level"].browse(response["data"]["id"])
        move_line = package_level.move_line_ids
        move = move_line.move_id

        # the put-away rule should have set the shelf1 for the move line
        self.assertRecordValues(
            move_line, [{"qty_done": 1.0, "location_dest_id": self.shelf1.id}]
        )
        self.assertRecordValues(
            move, [{"state": "assigned", "location_dest_id": self.stock_location.id}]
        )
        # self.assertDictEqual(
        #     response,
        #     {
        #         # TODO (mock any for ids?)
        #     },
        # )

    def _simulate_started(self):
        picking_form = Form(self.env["stock.picking"])
        picking_form.picking_type_id = self.menu.process_id.picking_type_ids
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.productA
            move.product_uom_qty = 1
        picking = picking_form.save()
        picking.action_confirm()
        picking.action_assign()
        package_level = picking.move_line_ids.package_level_id
        self.assertEqual(package_level.package_id, self.packA)
        # at this point, the package level is already set to "done", by the
        # "start" method of the pack transfer putaway
        package_level.is_done = True
        return package_level

    def test_validate(self):
        """Test the happy path for single pack putaway /validate endpoint

        The pre-conditions:

        * /start has been called

        Expected result:

        * The move associated to the package level is 'done'
        """
        # setup the picking as we need, like if the move line
        # was already started by the first step (start operation)
        package_level = self._simulate_started()

        # now, call the service to proceed with validation of the
        # movement
        response = self.service.dispatch(
            "validate",
            params={
                "package_level_id": package_level.id,
                "location_barcode": self.shelf1.barcode,
            },
        )
        self.assertDictEqual(
            response,
            {
                "message": {
                    "message": "The pack has been moved, you can scan a new pack.",
                    "message_type": "info",
                    "title": "Start",
                },
                "state": "start",
            },
        )

        self.assertRecordValues(
            package_level.move_line_ids,
            [{"qty_done": 1.0, "location_dest_id": self.shelf1.id, "state": "done"}],
        )
        self.assertRecordValues(
            package_level.move_line_ids.move_id,
            [{"location_dest_id": self.stock_location.id, "state": "done"}],
        )

    def test_validate_not_found(self):
        """Test a call on /validate on package level not found

        Expected result:

        * No change in odoo, Transition with a message
        """
        response = self.service.dispatch(
            "validate",
            params={"package_level_id": -1, "location_barcode": self.shelf1.barcode},
        )
        self.assertDictEqual(
            response,
            {
                "message": {
                    "message": "This operation does not exist anymore.",
                    "message_type": "error",
                    "title": "Start again",
                },
                "state": "start",
            },
        )

    def test_validate_location_not_found(self):
        """Test a call on /validate on location not found

        The pre-conditions:

        * /start has been called

        Expected result:

        * No change in odoo, Transition with a message
        """
        # setup the picking as we need, like if the move line
        # was already started by the first step (start operation)
        package_level = self._simulate_started()

        response = self.service.dispatch(
            "validate",
            params={
                "package_level_id": package_level.id,
                "location_barcode": "THIS_BARCODE_DOES_NOT_EXISTS",
            },
        )
        self.assertDictEqual(
            response,
            {
                "message": {
                    "message": "No location found for this barcode.",
                    "message_type": "error",
                    "title": "Scan",
                },
                "state": "scan_location",
            },
        )

    def test_validate_location_forbidden(self):
        """Test a call on /validate on a forbidden location

        The pre-conditions:

        * /start has been called

        Expected result:

        * No change in odoo, Transition with a message

        Note: a forbidden location is when a location is not a child
        of the destination location of the picking type used for the process
        """
        # setup the picking as we need, like if the move line
        # was already started by the first step (start operation)
        package_level = self._simulate_started()

        response = self.service.dispatch(
            "validate",
            params={
                "package_level_id": package_level.id,
                # this location is outside of the expected destination
                "location_barcode": self.dispatch_location.barcode,
            },
        )
        self.assertDictEqual(
            response,
            {
                "message": {
                    "message": "You cannot place it here",
                    "message_type": "error",
                    "title": "Forbidden",
                },
                "state": "scan_location",
            },
        )

    def test_cancel(self):
        """Test the happy path for single pack putaway /cancel endpoint

        The pre-conditions:

        * /start has been called

        Expected result:

        * The move associated to the package level is 'cancel'
        """
        # setup the picking as we need, like if the move line
        # was already started by the first step (start operation)
        package_level = self._simulate_started()

        # keep references for later checks
        move = package_level.move_line_ids.move_id
        move_lines = package_level.move_line_ids
        picking = move.picking_id

        # now, call the service to cancel
        response = self.service.dispatch(
            "cancel", params={"package_level_id": package_level.id}
        )
        self.assertRecordValues(move, [{"state": "cancel"}])
        self.assertRecordValues(picking, [{"state": "cancel"}])
        self.assertFalse(package_level.move_line_ids)
        self.assertFalse(move_lines.exists())

        self.assertDictEqual(
            response,
            {
                "message": {
                    "message": "The move has been canceled, you can scan a new pack.",
                    "message_type": "info",
                    "title": "Start",
                },
                "state": "start",
            },
        )

    def test_cancel_already_canceled(self):
        """Test a call on /cancel for already canceled move

        The pre-conditions:

        * /start has been called
        * /cancel has been called elsewhere or the move canceled on Odoo

        Expected result:

        * Nothing happens, transition with a message
        """
        # setup the picking as we need, like if the move line
        # was already started by the first step (start operation)
        package_level = self._simulate_started()

        # keep references for later checks
        move = package_level.move_line_ids.move_id
        move_lines = package_level.move_line_ids
        picking = move.picking_id

        # someone cancel the work started by our operator
        move._action_cancel()

        # now, call the service to cancel
        response = self.service.dispatch(
            "cancel", params={"package_level_id": package_level.id}
        )
        self.assertRecordValues(move, [{"state": "cancel"}])
        self.assertRecordValues(picking, [{"state": "cancel"}])
        self.assertFalse(package_level.move_line_ids)
        self.assertFalse(move_lines.exists())

        self.assertDictEqual(
            response,
            {
                "message": {
                    "message": "The move has been canceled, you can scan a new pack.",
                    "message_type": "info",
                    "title": "Start",
                },
                "state": "start",
            },
        )

    def test_cancel_already_done(self):
        """Test a call on /cancel on move already done

        The pre-conditions:

        * /start has been called
        * /validate has been called or move set to done in odoo

        Expected result:

        * No change in odoo, Transition with a message
        """
        # setup the picking as we need, like if the move line
        # was already started by the first step (start operation)
        package_level = self._simulate_started()

        # keep references for later checks
        move = package_level.move_line_ids.move_id
        picking = move.picking_id

        # someone cancel the work started by our operator
        move._action_done()

        # now, call the service to cancel
        response = self.service.dispatch(
            "cancel", params={"package_level_id": package_level.id}
        )
        self.assertRecordValues(move, [{"state": "done"}])
        self.assertRecordValues(picking, [{"state": "done"}])

        self.assertDictEqual(
            response,
            {
                "message": {
                    "message": "Move already processed.",
                    "message_type": "info",
                    "title": "Start",
                },
                "state": "start",
            },
        )

    def test_cancel_not_found(self):
        """Test a call on /cancel on package level not found

        Expected result:

        * No change in odoo, Transition with a message
        """
        response = self.service.dispatch("cancel", params={"package_level_id": -1})
        self.assertDictEqual(
            response,
            {
                "message": {
                    "message": "This operation does not exist anymore.",
                    "message_type": "error",
                    "title": "Start again",
                },
                "state": "start",
            },
        )
