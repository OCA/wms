# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import Form

from .test_single_pack_transfer_base import SinglePackTransferCommonBase


class TestSinglePackTransfer(SinglePackTransferCommonBase):
    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.pack_a = cls.env["stock.quant.package"].create(
            {"location_id": cls.stock_location.id}
        )
        cls.quant_a = (
            cls.env["stock.quant"]
            .sudo()
            .create(
                {
                    "product_id": cls.product_a.id,
                    "location_id": cls.shelf1.id,
                    "quantity": 1,
                    "package_id": cls.pack_a.id,
                }
            )
        )
        cls.picking = cls._create_initial_move()

    @classmethod
    def _create_initial_move(cls):
        """Create the move to satisfy the pre-condition before /start"""
        picking_form = Form(cls.env["stock.picking"])
        picking_form.picking_type_id = cls.picking_type
        picking_form.location_id = cls.shelf1
        picking_form.location_dest_id = cls.shelf2
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = cls.product_a
            move.product_uom_qty = 1
        picking = picking_form.save()
        picking.action_confirm()
        picking.action_assign()
        return picking

    def _simulate_started(self):
        """Replicate what the /start endpoint would do

        Used to test the next endpoints (/validate and /cancel)
        """
        package_level = self.picking.move_line_ids.package_level_id
        package_level.is_done = True
        return package_level

    def _response_package_level_data(self, package_level):
        return {
            "id": package_level.id,
            "name": package_level.package_id.name,
            "location_src": self.data.location(package_level.location_id),
            "location_dest": self.data.location(package_level.location_dest_id),
            "picking": self.data.picking(self.picking),
            "product": self.data.product(self.product_a),
        }

    def test_start(self):
        """Test the happy path for single pack transfer /start endpoint

        We scan the barcode of the pack (simplest use case).

        The pre-conditions:

        * A Pack exists in Stock/Shelf1.
        * A stock picking exists to move the Pack from Stock/Shelf1 to
          Stock/Shelf2. The move is "assigned".

        Expected result:

        * The package level of the move is set to "is_done".

        The next step in the workflow is to call /validate with the
        package level that will set the move and picking to done.
        """
        barcode = self.pack_a.name
        params = {"barcode": barcode}

        package_level = self.picking.move_line_ids.package_level_id
        self.assertFalse(package_level.is_done)

        # Simulate the client scanning a package's barcode, which
        # in turns should start the operation in odoo
        response = self.service.dispatch("start", params=params)

        self.assertTrue(package_level.is_done)
        self.assert_response(
            response,
            next_state="scan_location",
            data=dict(
                self._response_package_level_data(package_level),
                confirmation_required=False,
            ),
        )

    def test_start_no_operation(self):
        """Test /start when there is no operation to move the pack

        The pre-conditions:

        * A Pack exists in Stock/Shelf1.
        * No stock picking exists to move the Pack from Stock/Shelf1 to
          Stock/Shelf2, or the state is not assigned.

        Expected result:

        * Return a message
        """
        barcode = self.pack_a.name
        params = {"barcode": barcode}
        self.picking.do_unreserve()

        # Simulate the client scanning a package's barcode, which
        # in turns should start the operation in odoo
        response = self.service.dispatch("start", params=params)

        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "error",
                "body": "No pending operation for package {}.".format(self.pack_a.name),
            },
        )

    def test_start_no_operation_create(self):
        """Test /start when there is no operation to move the pack, it is created

        The pre-conditions:

        * The option "Allow Move Creation" is turned on on the menu
        * A Pack exists in Stock/Shelf1.
        * No stock picking exists to move the Pack from Stock/Shelf1 to
          Stock/Shelf2, or the state is not assigned.

        Expected result:

        * Create a stock.picking, move, package level and continue with the
          workflow
        """
        self.menu.sudo().allow_move_create = True
        barcode = self.pack_a.name
        params = {"barcode": barcode}
        self.picking.do_unreserve()

        # Simulate the client scanning a package's barcode, which
        # in turns should start the operation in odoo
        response = self.service.dispatch("start", params=params)

        move_line = self.env["stock.move.line"].search(
            [("package_id", "=", self.pack_a.id)]
        )
        package_level = move_line.package_level_id

        self.assertTrue(package_level.is_done)

        expected_data = {
            "id": package_level.id,
            "name": package_level.package_id.name,
            "location_src": self.data.location(self.shelf1),
            "location_dest": self.data.location(
                self.picking_type.default_location_dest_id
            ),
            "picking": self.data.picking(package_level.picking_id),
            "product": self.data.product(self.product_a),
            "confirmation_required": False,
        }

        self.assert_response(response, next_state="scan_location", data=expected_data)

    def test_start_barcode_not_known(self):
        """Test /start when the barcode is unknown

        The pre-conditions:

        * Nothing

        Expected result:

        * Return a message
        """
        params = {"barcode": "THIS_BARCODE_DOES_NOT_EXIST"}
        response = self.service.dispatch("start", params=params)
        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "error",
                "body": "The package THIS_BARCODE_DOES_NOT_EXIST" " doesn't exist",
            },
        )

    def test_start_pack_from_location(self):
        """Test /start, finding the pack from location's barcode

        When we scan a location which contains only one pack,
        we want to move this pack.

        The pre-conditions:

        * A Pack exists in Stock/Shelf1.
        * A stock picking exists to move the Pack from Stock/Shelf1 to
          Stock/Shelf2. The move is "assigned".

        Expected result:

        * The package level of the move is set to "is_done".

        The next step in the workflow is to call /validate with the
        package level that will set the move and picking to done.
        """
        barcode = self.shelf1.barcode
        params = {"barcode": barcode}
        response = self.service.dispatch("start", params=params)
        self.assert_response(
            # We only care about the fact that we jump to the next
            # screen, so it found the pack. The details are already
            # checked in the test_start test.
            response,
            next_state="scan_location",
            data=self.ANY,
        )

    def test_start_pack_from_location_empty(self):
        """Test /start, scan location's barcode without pack

        When we scan a location which contains no packs,
        we ask the user to scan a pack.

        The pre-conditions:

        * No packs exists in Stock/Shelf2

        Expected result:

        * Return a message
        """
        barcode = self.shelf2.barcode
        params = {"barcode": barcode}
        response = self.service.dispatch("start", params=params)
        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "error",
                "body": "Location %s doesn't contain any package."
                % (self.shelf2.name,),
            },
        )

    def test_start_pack_from_location_several_packs(self):
        """Test /start, scan location's barcode with several packs

        When we scan a location which contains several packs,
        we ask the user to scan a pack.

        The pre-conditions:

        * 2 packs exists in Stock/Shelf1.

        Expected result:

        * Return a message
        """
        pack_b = self.env["stock.quant.package"].create(
            {"location_id": self.stock_location.id}
        )
        self.env["stock.quant"].sudo().create(
            {
                "product_id": self.product_a.id,
                "location_id": self.shelf1.id,
                "quantity": 1,
                "package_id": pack_b.id,
            }
        )
        barcode = self.shelf1.barcode
        params = {"barcode": barcode}
        response = self.service.dispatch("start", params=params)
        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "warning",
                "body": "Several packages found in %s, please scan a package."
                % (self.shelf1.name,),
            },
        )

    def test_start_pack_outside_of_location(self):
        """Test /start, scan a pack outside of the picking type location

        The pre-conditions:

        * A pack exists in a location outside of Stock (the default source
          location of the picking type associated with the process)

        Expected result:

        * Return a message
        """
        self.pack_a.location_id = self.dispatch_location
        barcode = self.pack_a.name
        params = {"barcode": barcode}
        response = self.service.dispatch("start", params=params)
        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "error",
                "body": "You cannot work on a package (%s) outside of locations: %s"
                % (self.pack_a.name, self.picking_type.default_location_src_id.name),
            },
        )

    def test_start_already_started(self):
        """Test /start when it was already started

        We scan the barcode of the pack (simplest use case).

        The pre-conditions:

        * A Pack exists in Stock/Shelf1.
        * A stock picking exists to move the Pack from Stock/Shelf1 to
          Stock/Shelf2. The move is "assigned".
        * Start is already called once

        Expected result:

        * Transition for confirmation with such message

        The next step in the workflow is to call /validate with the
        package level that will set the move and picking to done.
        """
        barcode = self.pack_a.name
        params = {"barcode": barcode}

        package_level = self._simulate_started()
        self.assertTrue(package_level.is_done)

        # Simulate the client scanning a package's barcode, which
        # in turns should start the operation in odoo
        response = self.service.dispatch("start", params=params)

        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "warning",
                "body": "Operation's already running."
                " Would you like to take it over?",
            },
            data=dict(
                self._response_package_level_data(package_level),
                confirmation_required=True,
            ),
        )

    def test_validate(self):
        """Test the happy path for single pack transfer /validate endpoint

        The pre-conditions:

        * /start has been called
        * "completion info" is not active on the picking type

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
                "location_barcode": self.shelf2.barcode,
            },
        )

        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "success",
                "body": "The pack has been moved, you can scan a new pack.",
            },
        )

        self.assertRecordValues(
            package_level.move_line_ids,
            [{"qty_done": 1.0, "location_dest_id": self.shelf2.id, "state": "done"}],
        )
        self.assertRecordValues(
            package_level.move_line_ids.move_id,
            [{"location_dest_id": self.shelf2.id, "state": "done"}],
        )

    def test_validate_completion_info(self):
        """Test /validate when the picking is the last (show completion info)

        When the picking is the last, we display an information screen on the
        js application.

        The pre-conditions:

        * /start has been called
        * "completion info" is active on the picking type
        * the picking must be the last (it must not have destination moves with
          unprocessed origin moves)

        Expected result:

        * The move associated to the package level is 'done'
        * The transition goes to the completion info screen instead of starting
          over
        """
        # setup the picking as we need, like if the move line
        # was already started by the first step (start operation)
        package_level = self._simulate_started()

        # activate the computation of this field, so we have a chance to
        # transition to the 'show completion info' screen.
        self.picking_type.sudo().display_completion_info = True

        # create a chained picking after the current one
        next_picking = self.picking.copy(
            {
                "picking_type_id": self.wh.out_type_id.id,
                "location_id": self.picking.location_dest_id.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        next_picking.move_lines.write(
            {"move_orig_ids": [(6, 0, self.picking.move_lines.ids)]}
        )
        next_picking.action_confirm()

        # now, call the service to proceed with validation of the
        # movement
        response = self.service.dispatch(
            "validate",
            params={
                "package_level_id": package_level.id,
                "location_barcode": self.shelf2.barcode,
            },
        )
        self.assertEqual(package_level.picking_id.state, "done")

        self.assert_response(
            response,
            next_state="start",
            popup={
                "body": "Last operation of transfer {}. Next operation "
                "({}) is ready to proceed.".format(self.picking.name, next_picking.name)
            },
            message={
                "message_type": "success",
                "body": "The pack has been moved, you can scan a new pack.",
            },
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
                "body": "This operation does not exist anymore.",
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
            data=self.ANY,
            message={
                "message_type": "error",
                "body": "No location found for this barcode.",
            },
        )

    def test_validate_location_forbidden(self):
        """Test a call on /validate on a forbidden location (not child of type)

        The pre-conditions:

        * /start has been called

        Expected result:

        * No change in odoo, Transition with a message

        Note: the location is forbidden when a location is not a child
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
            data=self.ANY,
            message={"message_type": "error", "body": "You cannot place it here"},
        )

    def test_validate_location_forbidden_move_invalid(self):
        """Test a call on /validate on a forbidden location (not child of move)

        The pre-conditions:

        * /start has been called

        Expected result:

        * No change in odoo, Transition with a message

        Note: the location is forbidden when a location is not a child
        of the destination location of the move
        """
        # setup the picking as we need, like if the move line
        # was already started by the first step (start operation)
        package_level = self._simulate_started()

        move = package_level.move_line_ids.move_id
        # take the parent of the expected dest.: not allowed
        location = move.location_dest_id.location_id
        # allow this location to be used in the picking type, otherwise,
        # we check the wrong condition
        self.picking_type.sudo().default_location_dest_id = location

        response = self.service.dispatch(
            "validate",
            params={
                "package_level_id": package_level.id,
                # this location is outside of the expected destination
                "location_barcode": location.barcode,
            },
        )

        self.assert_response(
            response,
            next_state="scan_location",
            data=self.ANY,
            message={"message_type": "error", "body": "You cannot place it here"},
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

        sub_shelf1 = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "subshelf1",
                    "barcode": "subshelf1",
                    "location_id": self.shelf2.id,
                }
            )
        )
        sub_shelf2 = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "subshelf2",
                    "barcode": "subshelf2",
                    "location_id": self.shelf2.id,
                }
            )
        )

        # expected destination is 'shelf2', we'll scan shelf1 which must
        # ask a confirmation to the user (it's still in the same picking type)
        package_level.location_dest_id = sub_shelf1
        response = self.service.dispatch(
            "validate",
            params={
                "package_level_id": package_level.id,
                "location_barcode": sub_shelf2.barcode,
            },
        )

        message = self.service._actions_for("message").confirm_location_changed(
            sub_shelf1, sub_shelf2
        )
        self.assert_response(
            response,
            next_state="scan_location",
            message=message,
            data=dict(
                self._response_package_level_data(package_level),
                confirmation_required=True,
            ),
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
                "message_type": "success",
                "body": "The pack has been moved, you can scan a new pack.",
            },
        )

        self.assertRecordValues(
            package_level.move_line_ids,
            [{"qty_done": 1.0, "location_dest_id": self.shelf2.id, "state": "done"}],
        )
        self.assertRecordValues(
            package_level.move_line_ids.move_id,
            [{"location_dest_id": self.shelf2.id, "state": "done"}],
        )

    def test_cancel(self):
        """Test the happy path for single pack transfer /cancel endpoint

        The pre-conditions:

        * /start has been called

        Expected result:

        * The package level has is_done to False
        """
        # setup the picking as we need, like if the move line
        # was already started by the first step (start operation)
        package_level = self._simulate_started()
        self.assertTrue(package_level.is_done)

        # keep references for later checks
        move = package_level.move_line_ids.move_id
        picking = move.picking_id

        # now, call the service to cancel
        response = self.service.dispatch(
            "cancel", params={"package_level_id": package_level.id}
        )
        self.assertRecordValues(move, [{"state": "assigned"}])
        self.assertRecordValues(picking, [{"state": "assigned"}])
        self.assertRecordValues(package_level, [{"is_done": False}])

        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "success",
                "body": "Canceled, you can scan a new pack.",
            },
        )

    def test_cancel_already_canceled(self):
        """Test a call on /cancel for already canceled package level

        The pre-conditions:

        * /start has been called
        * /cancel has been called elsewhere or 'is_done' removed in odoo

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
                "message_type": "success",
                "body": "Canceled, you can scan a new pack.",
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
        move.extract_and_action_done()

        # now, call the service to cancel
        response = self.service.dispatch(
            "cancel", params={"package_level_id": package_level.id}
        )
        self.assertRecordValues(move, [{"state": "done"}])
        self.assertRecordValues(picking, [{"state": "done"}])

        self.assert_response(
            response,
            next_state="start",
            message={"message_type": "info", "body": "Operation already processed."},
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
                "body": "This operation does not exist anymore.",
            },
        )


class SinglePackTransferSpecialCase(SinglePackTransferCommonBase):
    def test_start_package_unreserve_ok(self):
        """Test /start when the package was already reserved...

        ...for another picking type and unreserving is allowed.

        When we scan a location which contains only one package,
        we want to move this package.

        The pre-conditions:

        * A package exists in Stock/Shelf1.
        * A stock picking exists to move the package from Stock/Shelf1 to
          Out with a different picking type. The move is "assigned".
        * Another package exists in Stock

        Expected result:

        * the original transfer is reserved to move the other package from Stock
        * a new transfer is created to move the package from Shelf1

        The next step in the workflow is to call /validate with the
        package level that will set the move and picking to done.
        """
        self.menu.sudo().allow_move_create = True
        self.menu.sudo().allow_unreserve_other_moves = True

        package = self.env["stock.quant.package"].create({})
        self._update_qty_in_location(self.shelf1, self.product_a, 10, package=package)
        # create a picking of another picking type
        picking = self._create_picking(
            picking_type=self.wh.out_type_id, lines=[(self.product_a, 10)]
        )
        picking.action_assign()

        # create another package that should be used when the picking will
        # get re-assigned
        package2 = self.env["stock.quant.package"].create({})
        self._update_qty_in_location(
            self.stock_location, self.product_a, 10, package=package2
        )

        barcode = self.shelf1.barcode
        params = {"barcode": barcode}
        response = self.service.dispatch("start", params=params)

        new_picking = self.env["stock.picking"].search(
            [("picking_type_id", "=", self.picking_type.id)]
        )
        self.assertEqual(len(new_picking), 1)
        new_package_level = new_picking.package_level_ids

        self.assert_response(
            # We only care about the fact that we jump to the next
            # screen, so it found the pack. The details are already
            # checked in the test_start test.
            response,
            next_state="scan_location",
            data=dict(
                self.service._data_after_package_scanned(new_package_level),
                confirmation_required=False,
            ),
        )
        self.assertRecordValues(
            picking.package_level_ids, [{"package_id": package2.id}]
        )

        self.assertRecordValues(new_package_level, [{"package_id": package.id}])

    def test_start_package_unreserve_picked_error(self):
        """Test /start when the package was already reserved...

        ...for another picking type and the other move is already picked.

        When we scan a location which contains only one package,
        we want to move this package.

        The pre-conditions:

        * A package exists in Stock/Shelf1.
        * A stock picking exists to move the package from Stock/Shelf1 to
          Out with a different picking type. The move is "assigned".

        Expected result:

        * receive an error that we cannot pick the package
        """
        self.menu.sudo().allow_move_create = True
        self.menu.sudo().allow_unreserve_other_moves = True

        package = self.env["stock.quant.package"].create({})
        self._update_qty_in_location(self.shelf1, self.product_a, 10, package=package)
        # create a picking of another picking type
        picking = self._create_picking(
            picking_type=self.wh.out_type_id, lines=[(self.product_a, 10)]
        )
        picking.action_assign()

        # pick the goods
        picking.move_line_ids.qty_done = 10

        barcode = self.shelf1.barcode
        params = {"barcode": barcode}
        response = self.service.dispatch("start", params=params)
        self.assert_response(
            response,
            next_state="start",
            message=self.service.msg_store.package_already_picked_by(package, picking),
        )
        # no change in the picking
        self.assertEqual(picking.state, "assigned")
        self.assertRecordValues(picking.package_level_ids, [{"package_id": package.id}])

    def test_start_package_unreserve_disabled_error(self):
        """Test /start when the package was already reserved...

        ...for another picking type and unreserving is disallowed.

        When we scan a location which contains only one package,
        we want to move this package.

        The pre-conditions:

        * A package exists in Stock/Shelf1.
        * A stock picking exists to move the package from Stock/Shelf1 to
          Out with a different picking type. The move is "assigned".

        Expected result:

        * receive an error that we cannot pick the package
        """
        self.menu.sudo().allow_move_create = True
        self.menu.sudo().allow_unreserve_other_moves = False

        package = self.env["stock.quant.package"].create({})
        self._update_qty_in_location(self.shelf1, self.product_a, 10, package=package)
        # create a picking of another picking type
        picking = self._create_picking(
            picking_type=self.wh.out_type_id, lines=[(self.product_a, 10)]
        )
        picking.action_assign()
        barcode = self.shelf1.barcode
        params = {"barcode": barcode}
        response = self.service.dispatch("start", params=params)
        self.assert_response(
            response,
            next_state="start",
            message=self.service.msg_store.package_already_picked_by(package, picking),
        )
        # no change in the picking
        self.assertEqual(picking.state, "assigned")
        self.assertRecordValues(picking.package_level_ids, [{"package_id": package.id}])

    def test_start_package_unreserve_no_create_error(self):
        """Test /start when the package was already reserved...

        ...for another picking type and unreserving is allowed
        and the option to create a move is not allowed.

        This test ensure that the unreservation of the first package
        is rollbacked.

        """
        self.menu.sudo().allow_move_create = False
        self.menu.sudo().allow_unreserve_other_moves = True

        package = self.env["stock.quant.package"].create({})
        self._update_qty_in_location(self.shelf1, self.product_a, 10, package=package)
        # create a picking of another picking type
        picking = self._create_picking(
            picking_type=self.wh.out_type_id, lines=[(self.product_a, 10)]
        )
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        barcode = self.shelf1.barcode
        params = {"barcode": barcode}
        response = self.service.dispatch("start", params=params)
        self.assert_response(
            response,
            next_state="start",
            message=self.service.msg_store.no_pending_operation_for_pack(package),
        )
        # no change in the picking
        self.assertEqual(picking.state, "assigned")
        self.assertRecordValues(picking.package_level_ids, [{"package_id": package.id}])
