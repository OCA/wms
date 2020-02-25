from odoo.tests.common import Form

from .common import CommonCase


class SinglePackPutawayCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.product_a = cls.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        cls.pack_a = cls.env["stock.quant.package"].create(
            {"location_id": cls.stock_location.id}
        )
        cls.env["stock.putaway.rule"].create(
            {
                "product_id": cls.product_a.id,
                "location_in_id": cls.stock_location.id,
                "location_out_id": cls.shelf1.id,
            }
        )
        cls.quant_a = cls.env["stock.quant"].create(
            {
                "product_id": cls.product_a.id,
                "location_id": cls.dispatch_location.id,
                "quantity": 1,
                "package_id": cls.pack_a.id,
            }
        )
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_put_away_reach_truck")
        cls.process = cls.menu.process_id
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="single_pack_putaway")

    def test_to_openapi(self):
        # will raise if it fails to generate the openapi specs
        self.service.to_openapi()

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
        barcode = self.pack_a.name
        params = {"barcode": barcode}
        # Simulate the client scanning a package's barcode, which
        # in turns should start the operation in odoo
        response = self.service.dispatch("start", params=params)
        state_data = response["data"]["scan_location"]

        # Checks:
        package_level = self.env["stock.package_level"].browse(state_data["id"])
        move_line = package_level.move_line_ids
        move = move_line.move_id

        # the put-away rule should have set the shelf1 for the move line
        self.assertRecordValues(
            move_line, [{"qty_done": 1.0, "location_dest_id": self.shelf1.id}]
        )
        self.assertRecordValues(
            move, [{"state": "assigned", "location_dest_id": self.stock_location.id}]
        )
        self.assert_response(
            response,
            next_state="scan_location",
            message={
                "message_type": "info",
                "message": "Scan the destination location",
            },
            data={
                "id": self.ANY,
                "location_src": {
                    "id": self.dispatch_location.id,
                    "name": self.dispatch_location.name,
                },
                "location_dst": {"id": self.shelf1.id, "name": self.shelf1.name},
                "name": package_level.package_id.name,
                "picking": {"id": move.picking_id.id, "name": move.picking_id.name},
                "product": {"id": move.product_id.id, "name": move.product_id.name},
            },
        )

    def test_start_no_package_for_barcode(self):
        """Test /start when no package is found for barcode

        The pre-conditions:

        * No Pack exists with the barcode

        Expected result:

        * return a message
        """
        params = {"barcode": "NOTHING_SHOULD_EXIST_WITH: 👀"}
        response = self.service.dispatch("start", params=params)
        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "error",
                "message": "The package NOTHING_SHOULD_EXIST_WITH: 👀 doesn't exist",
            },
        )

    def test_start_package_not_in_src_location(self):
        """Test /start when the package is not in the src location

        The pre-conditions:

        * Pack exists with the barcode
        * The Pack is outside the location or sublocation of the source
          location of the current process' picking type

        Expected result:

        * return a message
        """
        barcode = self.pack_a.name
        self.pack_a.location_id = self.shelf1
        params = {"barcode": barcode}
        response = self.service.dispatch("start", params=params)
        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "error",
                "message": "You cannot work on a package (%s) outside of location: %s"
                % (
                    self.pack_a.name,
                    self.process.picking_type_id.default_location_src_id.name,
                ),
            },
        )

    def test_start_move_in_different_picking_type(self):
        """Test /start when the package is used in a move in a different picking type

        The pre-conditions:

        * Pack exists
        * A move is created and assigned to move the package, using another picking type

        Expected result:

        * return a message
        """
        barcode = self.pack_a.name

        # Create a move in a different picking type (trick the 'Delivery
        # Orders' to go directly from Input to Customers)
        picking_form = Form(self.env["stock.picking"])
        picking_form.picking_type_id = self.wh.out_type_id
        picking_form.location_id = self.input_location
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.product_a
            move.product_uom_qty = 1
        picking = picking_form.save()
        picking.action_confirm()
        picking.action_assign()

        params = {"barcode": barcode}
        response = self.service.dispatch("start", params=params)
        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "error",
                "message": "An operation exists in Delivery Orders %s. You cannot"
                " process it with this shopfloor process." % (picking.name,),
            },
        )

    def test_start_move_already_exist(self):
        """Test /start when the move for the package already exists

        Because it was already started.

        The pre-conditions:

        * Pack exists
        * A move is created and assigned to move the package, using the same
          picking type

        Expected result:

        * return a message to confirm
        """
        barcode = self.pack_a.name

        # Create a move in a the same picking type
        package_level = self._simulate_started()
        move = package_level.move_line_ids.move_id

        params = {"barcode": barcode}
        response = self.service.dispatch("start", params=params)

        self.assert_response(
            response,
            next_state="confirm_start",
            message={
                "message_type": "warning",
                "message": "Operation's already running."
                " Would you like to take it over?",
            },
            data={
                "id": self.ANY,
                "location_src": {
                    "id": self.dispatch_location.id,
                    "name": self.dispatch_location.name,
                },
                "location_dst": {"id": self.shelf1.id, "name": self.shelf1.name},
                "name": package_level.package_id.name,
                "picking": {"id": move.picking_id.id, "name": move.picking_id.name},
                "product": {"id": self.product_a.id, "name": self.product_a.name},
            },
        )

    def _simulate_started(self):
        """Replicate what the /start endpoint would do

        Used to test the next endpoints (/validate and /cancel)
        """
        picking_form = Form(self.env["stock.picking"])
        picking_form.picking_type_id = self.menu.process_id.picking_type_id
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.product_a
            move.product_uom_qty = 1
        picking = picking_form.save()
        picking.action_confirm()
        picking.action_assign()
        package_level = picking.move_line_ids.package_level_id
        self.assertEqual(package_level.package_id, self.pack_a)
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

        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "info",
                "message": "The pack has been moved, you can scan a new pack.",
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

        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "error",
                "message": "This operation does not exist anymore.",
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

        self.assert_response(
            response,
            next_state="scan_location",
            message={
                "message_type": "error",
                "message": "No location found for this barcode.",
            },
            data=self.ANY,
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

        self.assert_response(
            response,
            next_state="scan_location",
            message={"message_type": "error", "message": "You cannot place it here"},
            data=self.ANY,
        )

    def test_validate_location_to_confirm(self):
        """Test a call on /validate on a location to confirm

        The pre-conditions:

        * /start has been called

        Expected result:

        * No change in odoo, transition with a message

        Note: a location to confirm is when a location is a child
        of the destination location of the picking type used for the process
        but not a child or the expected destination
        """
        # setup the picking as we need, like if the move line
        # was already started by the first step (start operation)
        package_level = self._simulate_started()

        move = package_level.move_line_ids.move_id
        # expected destination is 'shelf1', we'll scan shelf2 which must
        # ask a confirmation to the user (it's still in the same picking type)
        response = self.service.dispatch(
            "validate",
            params={
                "package_level_id": package_level.id,
                "location_barcode": self.shelf2.barcode,
            },
        )
        message = self.service.actions_for("message").confirm_location_changed(
            self.shelf1, self.shelf2
        )

        self.assert_response(
            response,
            next_state="confirm_location",
            message=message,
            data={
                "id": self.ANY,
                "location_src": {
                    "id": self.dispatch_location.id,
                    "name": self.dispatch_location.name,
                },
                "location_dst": {"id": self.shelf1.id, "name": self.shelf1.name},
                "name": package_level.package_id.name,
                "picking": {"id": move.picking_id.id, "name": move.picking_id.name},
                "product": {"id": move.product_id.id, "name": move.product_id.name},
            },
        )

    def test_validate_location_with_confirm(self):
        """Test a call on /validate on a different location with confirmation

        The pre-conditions:

        * /start has been called

        Expected result:

        * Ignore the fact that the scanned location is not the expected
        * Change the destination of the move line to the scanned one
        * The move associated to the package level is 'done'

        Note: a location to confirm is when a location is a child
        of the destination location of the picking type used for the process
        but not a child or the expected destination.
        In such situation, the js application has to call /validate with
        a ``confirmation`` flag.
        """
        # setup the picking as we need, like if the move line
        # was already started by the first step (start operation)
        package_level = self._simulate_started()

        # expected destination is 'shelf1', we'll scan shelf2 which must
        # ask a confirmation to the user (it's still in the same picking type)
        response = self.service.dispatch(
            "validate",
            params={
                "package_level_id": package_level.id,
                "location_barcode": self.shelf2.barcode,
                # acknowledge the change of destination
                "confirmation": True,
            },
        )

        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "info",
                "message": "The pack has been moved, you can scan a new pack.",
            },
        )

        self.assertRecordValues(
            package_level.move_line_ids,
            [{"qty_done": 1.0, "location_dest_id": self.shelf2.id, "state": "done"}],
        )
        self.assertRecordValues(
            package_level.move_line_ids.move_id,
            [{"location_dest_id": self.stock_location.id, "state": "done"}],
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

        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "info",
                "message": "Canceled, you can scan a new pack.",
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

        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "info",
                "message": "Canceled, you can scan a new pack.",
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

        self.assert_response(
            response,
            next_state="start",
            message={"message_type": "info", "message": "Operation already processed."},
        )

    def test_cancel_not_found(self):
        """Test a call on /cancel on package level not found

        Expected result:

        * No change in odoo, Transition with a message
        """
        response = self.service.dispatch("cancel", params={"package_level_id": -1})
        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "error",
                "message": "This operation does not exist anymore.",
            },
        )
