# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, api, exceptions, fields, models


class StockReceptionScreen(models.Model):
    _name = "stock.reception.screen"
    _inherit = "barcodes.barcode_events_mixin"
    _description = "Stock Reception Screen"

    _step_start = "select_product"
    _steps = {
        "select_product": {
            "label": _("Select Product"),
            "next_steps": [{"next": "select_move"}],
        },
        "select_move": {
            "label": _("Select Move"),
            "next_steps": [
                {
                    # Only if the product is managed by lots
                    "before": "_before_select_move_to_set_lot_number",
                    "next": "set_lot_number",
                },
                {"next": "set_quantity"},
            ],
        },
        "set_lot_number": {
            "label": _("Set Lot Number"),
            "next_steps": [{"next": "set_expiry_date"}],
        },
        "set_expiry_date": {
            "label": _("Set Expiry Date"),
            "next_steps": [{"next": "set_quantity"}],
            "focus_field": "current_move_line_lot_life_date",
        },
        "set_quantity": {
            "label": _("Set Quantity"),
            "next_steps": [{"next": "set_location"}],
            "focus_field": "current_move_line_qty_done",
        },
        "set_location": {
            "label": _("Set Destination"),
            "next_steps": [
                {
                    "before": "_before_set_location_to_select_packaging",
                    "next": "select_packaging",
                }
            ],
            "focus_field": "current_move_line_location_dest_id",
        },
        "select_packaging": {
            "label": _("Select Packaging"),
            "next_steps": [{"next": "set_package"}],
        },
        "set_package": {
            "label": _("Set Package"),
            "next_steps": [
                # TODO: Should add a before step
                {
                    "before": "_before_next_move_to_set_lot_number",
                    "next": "set_lot_number",
                },
                {
                    "before": "_before_next_move_to_set_quantity",
                    "next": "set_quantity",
                },
                {
                    # Loop until all moves are processed
                    "before": "_before_set_location_to_select_move",
                    "next": "select_move",
                },
                {
                    # Only if there are remaining moves to process}
                    "before": "_before_set_location_to_select_product",
                    "next": "select_product",
                },
                {"next": "done", "after": "_after_step_done"},
            ],
            "focus_field": "current_move_line_package",
        },
        "done": {"label": _("Done"), "next_steps": []},
    }

    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Transfer",
        ondelete="cascade",
        required=True,
    )
    name = fields.Char(related="picking_id.name", store=True)
    picking_origin = fields.Char(related="picking_id.origin")
    picking_partner_id = fields.Many2one(related="picking_id.partner_id")
    picking_state = fields.Selection(related="picking_id.state")
    picking_move_lines = fields.One2many(related="picking_id.move_lines")
    picking_location_dest_id = fields.Many2one(related="picking_id.location_dest_id")
    picking_filtered_move_lines = fields.One2many(
        comodel_name="stock.move", compute="_compute_picking_filtered_move_lines"
    )
    current_step = fields.Char(default="select_product", copy=False)
    current_step_descr = fields.Char(
        string="Operation", compute="_compute_current_step_descr"
    )
    current_step_focus_field = fields.Char(
        string="Focus field", compute="_compute_current_step_descr"
    )
    current_filter_product = fields.Char(string="Filter product", copy=False)
    # current move
    current_move_id = fields.Many2one(comodel_name="stock.move", copy=False)
    current_move_product_id = fields.Many2one(
        related="current_move_id.product_id", string="Move's product"
    )
    current_move_product_display_name = fields.Char(
        related="current_move_id.product_id.display_name", string="Product"
    )
    current_move_product_uom_qty = fields.Float(
        related="current_move_id.product_uom_qty"
    )
    current_move_product_uom_id = fields.Many2one(related="current_move_id.product_uom")
    current_move_product_packaging_ids = fields.One2many(
        related="current_move_id.product_id.packaging_ids"
    )
    current_move_product_vendor_code = fields.Char(
        related="current_move_id.vendor_code"
    )
    # current move line
    current_move_line_id = fields.Many2one(comodel_name="stock.move.line", copy=False)
    current_move_line_location_dest_id = fields.Many2one(
        comodel_name="stock.location",
        string="Destination",
        compute="_compute_current_move_line_location_dest_id",
        inverse="_inverse_current_move_line_location_dest_id",
    )
    current_move_line_lot_id = fields.Many2one(
        related="current_move_line_id.lot_id", string="Lot NumBer"
    )
    current_move_line_lot_life_date = fields.Datetime(
        # NOTE: Not a related as we want to check the user input before storing
        # the date in the related lot
        string="End of Life Date",
    )
    current_move_line_qty_done = fields.Float(
        related="current_move_line_id.qty_done", string="Quantity", readonly=False
    )
    current_move_line_uom_id = fields.Many2one(
        related="current_move_line_id.product_uom_id", string="UoM"
    )
    current_move_line_qty_status = fields.Char(
        string="Qty Status", compute="_compute_current_move_line_qty_status"
    )
    current_move_line_package = fields.Char(
        compute="_compute_current_move_line_package",
        inverse="_inverse_current_move_line_package",
        string="Package N°",
    )
    current_move_line_package_stored = fields.Char()
    # == Packaging fields ==
    # NOTE: Mainly not related as we want to store these data on the current
    # package when the "select_packaging" step is confirmed by the user
    product_packaging_id = fields.Many2one(
        "product.packaging", domain="[('product_id', '=', current_move_product_id)]",
    )
    package_storage_type_id = fields.Many2one("stock.package.storage.type",)
    package_storage_type_height_required = fields.Boolean(
        related="package_storage_type_id.height_required"
    )
    package_height = fields.Integer()
    # == / Packaging fields ==

    @api.depends("picking_id.move_lines", "current_filter_product")
    def _compute_picking_filtered_move_lines(self):
        for screen in self:
            moves = screen.picking_id.move_lines
            screen.picking_filtered_move_lines = moves
            if screen.current_filter_product:
                filter_ = screen.current_filter_product
                search_args = [
                    ("id", "in", moves.ids),
                    "|",
                    "|",
                    ("product_id.barcode", "=", filter_),
                    ("product_id.default_code", "=", filter_),
                    ("product_id.name", "ilike", filter_),
                ]
                moves = moves.search(search_args)
                screen.picking_filtered_move_lines = moves

    @api.depends("current_step")
    def _compute_current_step_descr(self):
        for wiz in self:
            wiz.current_step_descr = False
            wiz.current_step_focus_field = False
            if self.current_step:
                steps = self.get_reception_screen_steps()
                step_descr = steps[self.current_step]["label"]
                wiz.current_step_descr = step_descr
                wiz.current_step_focus_field = steps[self.current_step].get(
                    "focus_field", ""
                )

    @api.depends("current_move_line_id.location_dest_id")
    def _compute_current_move_line_location_dest_id(self):
        for wiz in self:
            move_line = wiz.current_move_line_id
            wiz.current_move_line_location_dest_id = move_line.location_dest_id
            location = move_line.location_dest_id._get_putaway_strategy(
                move_line.product_id
            )
            if location:
                wiz.current_move_line_location_dest_id = location

    def _inverse_current_move_line_location_dest_id(self):
        for wiz in self:
            move_line = wiz.current_move_line_id
            move_line.location_dest_id = wiz.current_move_line_location_dest_id

    @api.depends("current_move_line_id.qty_done")
    def _compute_current_move_line_qty_status(self):
        """Based on the total quantity received, a colored disk will
        appear in green/blue/red to the user.

        - green: the qty received match the planned qty
        - red: the qty received is inferior to the planned qty
        - blue: the qty received is superior to the planned qty
        """
        for wiz in self:
            move_line = wiz.current_move_line_id
            move = move_line.move_id
            if not move_line.qty_done:
                wiz.current_move_line_qty_status = ""
            elif move.quantity_done > move.product_uom_qty:
                wiz.current_move_line_qty_status = "gt"
            elif move.quantity_done < move.product_uom_qty:
                wiz.current_move_line_qty_status = "lt"
            else:
                wiz.current_move_line_qty_status = "eq"

    @api.depends("current_move_line_id.result_package_id.package_storage_type_id")
    def _compute_current_move_line_package(self):
        for wiz in self:
            package = wiz.current_move_line_id.result_package_id
            wiz.current_move_line_package = package.name

    def _inverse_current_move_line_package(self):
        for wiz in self:
            wiz.current_move_line_package_stored = wiz.current_move_line_package

    @api.onchange("product_packaging_id")
    def onchange_product_packaging_id(self):
        self.package_storage_type_id = self.product_packaging_id.package_storage_type_id
        self.package_height = self.product_packaging_id.height

    @api.onchange("package_storage_type_id")
    def onchange_package_storage_type_id(self):
        # NOTE: this onchange is required as the related field
        # doesn't seem to work well on such screen
        self.package_storage_type_height_required = (
            self.package_storage_type_id.height_required
        )

    def get_reception_screen_steps(self):
        """Aim to be overloaded to update the reception steps."""
        self.ensure_one()
        return self._steps

    def action_reception_screen_close(self):
        """Close the reception screen.
        It'll automatically reload the picking form.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self.picking_id._name,
            "res_id": self.picking_id.id,
            "view_mode": "form",
            "target": "main",  # Will restore the main menu/panel on top
        }

    def action_reception_screen_manual_barcode(self):
        """Display a window to fill manually a barcode.

        You don't need to open this window if you use a barcode scanner
        directly on the screen.
        """
        return {
            "type": "ir.actions.act_window",
            "res_model": "stock.picking.manual.barcode",
            "view_mode": "form",
            "name": _("Barcode"),
            "target": "new",
        }

    def next_step(self):
        """Evaluate the next step for the operator."""
        if self.current_move_id and self.current_move_id.state in ("cancel", "done"):
            raise exceptions.UserError(_("The move is already processed, aborting."))
        if self.current_step:
            steps = self.get_reception_screen_steps()
            step = steps[self.current_step]
            for next_step in step["next_steps"]:
                if next_step.get("before"):
                    check = getattr(self, next_step["before"])()
                    if not check:
                        # This step can be skipped
                        continue
                self.current_step = next_step["next"]
                if next_step.get("after"):
                    getattr(self, next_step["after"])()
                break

    def on_barcode_scanned(self, barcode):
        """Dispatch the barcode event to the right method (if any)."""
        self.ensure_one()
        method = "on_barcode_scanned_{}".format(self.current_step)
        if hasattr(self, method):
            getattr(self, method)(barcode)

    def on_barcode_scanned_select_product(self, barcode):
        """Try to find the corresponding product based on the barcode."""
        moves = self.picking_id.move_lines
        # First find a moves corresponding to the barcode
        move = moves.filtered(lambda o: o.product_id.barcode == barcode)
        # Then try on the product code
        if not move:
            move = moves.filtered(lambda o: o.product_id.default_code == barcode)
        # And on the name
        if not move:
            move = moves.filtered(lambda o: barcode in o.product_id.name)
        if not move:
            self.env.user.notify_warning(
                message="", title=_("Product '{}' not found.").format(barcode)
            )
            return
        # If there are several moves/products corresponding to the search
        # criteria we want to propose the user to choose the right one
        # by filtering them
        if len(move) > 1:
            self.current_filter_product = barcode
        # Otherwise we select directly the available move
        else:
            self.current_move_id = move
        self.process_select_product()

    def _create_remaining_move_line(self, move):
        """Create one move line with a remaining qty to process equals to the
        difference between the planned qty and the already processed qty
        of the move.
        """
        remaining_qty = move.product_uom_qty - move.quantity_done
        vals = move._prepare_move_line_vals(quantity=remaining_qty)
        return self.env["stock.move.line"].create(vals)

    def on_barcode_scanned_set_lot_number(self, barcode):
        """Set the lot number on a move line."""
        # First, check if the lot already exists
        lot_model = self.env["stock.production.lot"]
        lot = lot_model.search(
            [
                ("name", "=", barcode),
                ("product_id", "=", self.current_move_id.product_id.id),
                ("company_id", "=", self.picking_id.company_id.id),
            ]
        )
        if lot:
            self.env.user.notify_info(
                message="", title=_("Reuse the existing lot {}.").format(barcode)
            )
        else:
            lot_vals = {
                "name": barcode,
                "product_id": self.current_move_id.product_id.id,
                "company_id": self.picking_id.company_id.id,
            }
            lot = lot_model.create(lot_vals)
        # Check for an existing move line without lot otherwise create one
        move_lines = self.current_move_id.move_line_ids
        # Finally if there is no corresponding move line we create one
        # with a remaining qty to process equals to the difference between
        # the planned qty and the already processed qty.
        # TODO: need to check if it is still necessary as we are now validating
        # stock.move at the end of each reception flow
        if not move_lines:
            move_lines = self._create_remaining_move_line(self.current_move_id)
        self.current_move_line_id = move_lines[0]
        # Set the lot
        self.current_move_line_id.lot_id = lot
        self.process_set_lot_number()

    def on_barcode_scanned_set_package(self, barcode):
        """Set the package on the move line."""
        self.current_move_line_package = barcode

    def on_barcode_scanned_select_packaging(self, barcode):
        """Auto-complete the package data.

        The package data is filled automatically depending on
        the barcode scanned for the package storage type.
        """
        packaging = self.current_move_product_packaging_ids.filtered(
            lambda o: o.package_storage_type_id.barcode == barcode
        )[:1]
        self._autocomplete_package_data(packaging)

    def _autocomplete_package_data(self, packaging):
        """Auto-complete the package data on the screen but doesn't
        actually update the package itself.

        The update of the package is done by `_set_package_data` method
        when the user confirm the step.
        """
        if packaging:
            self.product_packaging_id = packaging
            self.package_storage_type_id = packaging.package_storage_type_id
            self.package_height = packaging.height

    def _set_package_data(self):
        """Set the packaging, package storage type and height on a newly
        created package.

        This is performed at the end to not trigger the constraint regarding
        the height required for some package storage types.
        """
        # Create the package
        move_line = self.current_move_line_id
        package = self.env["stock.quant.package"].create(
            {"name": self.current_move_line_package_stored}
        )
        move_line.result_package_id = package
        # Set the height at first to not trigger the constraint related to
        # the product packaging and storage type
        package.height = self.package_height
        package.product_packaging_id = self.product_packaging_id
        package.package_storage_type_id = self.package_storage_type_id
        # Clean up package data input (better to get them empty on the screen
        # until they are again autocompleted depending on the selected packaging)
        self.product_packaging_id = (
            self.package_storage_type_id
        ) = self.package_height = False

    def process_select_product(self):
        self.next_step()
        if self.current_move_id:
            # Go to the next step automatically if only one move has been found
            self.process_select_move()

    def _validate_current_move(self):
        """Split the current move with the move line qty done and
        validate it.
        It is performed right after the processing of the current move (so
        before checking the next move to process).
        """
        if self.current_move_line_id and self.current_move_id:
            # We use the 'is_scrap' context key to avoid the generation of a
            # backorder when validating the move (see _action_done() method in
            # stock/models/stock_move.py).
            self.current_move_id.with_context(is_scrap=True)._action_done()
            # A new move is automatically created if we made a partial receipt
            # and we have to update it to the 'assigned' state to generate the
            # related 'stock.move.line' (required if we want to process it)
            confirmed_moves = self.picking_id.move_lines.filtered(
                lambda o: o.state == "confirmed"
            )
            confirmed_moves._action_assign()

    def _before_set_location_to_select_move(self):
        """Check if there is remaining moves to process for the
        selected product.
        """
        # self._validate_current_move()
        if not self.current_filter_product:
            return False
        moves_to_process_ok = any(
            move.quantity_done < move.product_uom_qty
            for move in self.picking_filtered_move_lines
        )
        if moves_to_process_ok:
            self.current_move_id = False
            self.current_move_line_id = False
        return moves_to_process_ok

    def _before_set_location_to_select_product(self):
        """Check if there is remaining products/moves to process."""
        moves_to_process_ok = any(
            move.quantity_done < move.product_uom_qty
            for move in self.picking_id.move_lines
        )
        if moves_to_process_ok:
            self.current_filter_product = False
            self.current_move_id = False
            self.current_move_line_id = False
        return moves_to_process_ok

    def _select_move_line(self):
        # Select the move line to process for the remaining qty
        # NOTE: we should always have one move line available since we run
        # 'action_assign' on the picking each time we validate a move.
        move_line = fields.first(self.current_move_id.move_line_ids)
        self.current_move_line_id = move_line
        last_lot = self.current_move_id.last_move_line_lot_id
        if last_lot:
            self.current_move_line_id.lot_id = last_lot
            self.current_move_line_lot_life_date = last_lot.life_date
        else:
            # No lot to reuse, we reset the life date
            self.current_move_line_lot_life_date = False

    def process_select_move(self):
        self.next_step()
        self._select_move_line()

    def _before_select_move_to_set_lot_number(self):
        """Decide if we have to handle lots on the current move."""
        return self.current_move_id.has_tracking != "none"

    def process_set_lot_number(self):
        if not self.current_move_line_id.lot_id:
            self.env.user.notify_warning(
                message="", title=_("You have to fill the lot number.")
            )
            return
        # Saving the lot number for next operation
        self.current_move_id.last_move_line_lot_id = self.current_move_line_id.lot_id
        self.next_step()

    def process_set_expiry_date(self):
        """Set the lot life date on a move line."""
        if not self.current_move_line_lot_life_date:
            self.env.user.notify_warning(
                message="", title=_("You have to set an expiry date.")
            )
            return
        if (
            self.current_move_line_lot_id.life_date
            and self.current_move_line_lot_life_date
            < self.current_move_line_lot_id.life_date
        ):
            lang = self.env["res.lang"]._lang_get(self.env.user.lang)
            previous_life_date_str = self.current_move_line_lot_id.life_date.strftime(
                lang.date_format
            )
            self.env.user.notify_warning(
                message="",
                title=_(
                    "You cannot set a date prior to previous one ({})".format(
                        previous_life_date_str
                    )
                ),
            )
            return
        self.current_move_line_lot_id.life_date = self.current_move_line_lot_life_date
        self.next_step()

    def process_set_quantity(self):
        if not self.current_move_line_qty_done:
            self.env.user.notify_warning(
                message="", title=_("You have to set the received quantity.")
            )
            return
        self.next_step()

    def process_set_location(self):
        if not self.current_move_line_location_dest_id:
            self.env.user.notify_warning(
                message="", title=_("You have to set the destination.")
            )
            return
        self.next_step()

    def process_select_packaging(self):
        self.next_step()

    def _before_set_location_to_select_packaging(self):
        """Auto-complete the package data matching the qty (if there is one)."""
        qty_done = self.current_move_line_qty_done
        if qty_done:
            packaging = self.current_move_product_packaging_ids.filtered(
                lambda o: o.qty == qty_done
            )[:1]
            self._autocomplete_package_data(packaging)
        return True

    def process_set_package(self):
        if self._check_package_data():
            self._set_package_data()
            self.next_step()
            return True
        return False

    def _before_next_move_to_set_lot_number(self):
        """Receive next move for same product (with lot) directely."""
        self._validate_current_move()
        current_product = self.current_move_id.product_id
        moves_to_do = self.picking_filtered_move_lines.filtered(
            lambda r: r.quantity_done < r.product_uom_qty
            and r.product_id == current_product
        )
        if not moves_to_do:
            return False
        if self.current_move_id.has_tracking == "none":
            return False
        self.current_move_id = moves_to_do[0]
        self._select_move_line()
        return True

    def _before_next_move_to_set_quantity(self):
        """Receive next move for same product (without lot) directely."""
        current_product = self.current_move_id.product_id
        moves_to_do = self.picking_filtered_move_lines.filtered(
            lambda r: r.quantity_done < r.product_uom_qty
            and r.product_id == current_product
        )
        if not moves_to_do:
            return False
        if self.current_move_id.has_tracking != "none":
            return False
        self.current_move_id = moves_to_do[0]
        self._select_move_line()
        return True

    def _check_package_data(self):
        """Check that the storage type is set.
        It is done this way to not set the field required on the form
        (allowing to quit the reception screen via the exit button and resume
        the step later).
        """
        if not self.package_storage_type_id:
            msg = _("The storage type is mandatory before going further.")
            self.env.user.notify_warning(message="", title=msg)
            return False
        if (
            self.product_packaging_id
            and not self.product_packaging_id.type_is_pallet
            and (
                # NOTE: we are not checking the 'volume' field as it is rounded
                # to 0 with small dimensions and produces false positive results
                not (
                    self.product_packaging_id.lngth
                    and self.product_packaging_id.width
                    and self.product_packaging_id.height
                )
                or not self.product_packaging_id.max_weight
            )
        ):
            msg = _("Product packaging info are missing. Please use the CUBISCAN.")
            self.env.user.notify_warning(message="", title=msg)
            return False
        return True

    def _after_step_done(self):
        """Reset the current selected move line."""
        self.current_filter_product = False
        self.current_move_id = False
        self.current_move_line_id = False
        return True

    def button_save_step(self):
        """Save the current step."""
        self.ensure_one()
        if not self.current_move_id and not self.current_move_line_id:
            return
        method = "process_{}".format(self.current_step)
        getattr(self, method)()
        return True

    def button_next_pack(self):
        """Process the current package and prepare the screen to scan another
        one for the same product/lot/packaging data.

        When calling this button we are supposed to be in the `set_package` step,
        and once triggered the button will complete the first steps with the
        same data than the previous package, and will stop again on the
        `set_package` step.
        """
        self.ensure_one()
        if not self.current_move_id and not self.current_move_line_id:
            return
        assert self.current_step == "set_package", f"step = {self.current_step}"
        # Copy relevant data for the next package
        qty_done = self.current_move_line_qty_done
        location_dest = self.current_move_line_location_dest_id
        product_packaging = self.product_packaging_id
        package_storage_type = self.package_storage_type_id
        package_height = self.package_height
        # Validate the current package
        if not self.process_set_package():
            # Package data may be missing the first time, aborting operation
            return
        # Stop when the current product/lot has been fully processed
        if self.current_step in ("select_product", "select_move"):
            return
        # Process the first steps of the next package
        #   - process lot if required
        if self.current_step == "set_lot_number":
            self.process_set_lot_number()
            self.process_set_expiry_date()
        #   - set the quantity
        assert self.current_step == "set_quantity", f"step = {self.current_step}"
        self.current_move_line_qty_done = qty_done
        self.process_set_quantity()
        #   - set the destination
        self.current_move_line_location_dest_id = location_dest
        self.process_set_location()
        #   - set packaging data
        assert self.current_step == "select_packaging", f"step = {self.current_step}"
        self.product_packaging_id = product_packaging
        self.package_storage_type_id = package_storage_type
        if self.package_storage_type_height_required:
            self.package_height = package_height
        self.process_select_packaging()
        assert self.current_step == "set_package", f"step = {self.current_step}"
        return True

    def button_reset(self):
        """Reset the current step.

        This allows the user to choose another product to process.
        """
        self.ensure_one()
        self.current_step = self._step_start
        self.current_filter_product = False
        self.current_move_id = self.current_move_line_id = False
        # Empty package input data
        self.product_packaging_id = (
            self.package_storage_type_id
        ) = self.package_height = False
        self.current_move_line_package_stored = False
        return True

    def action_check_quantity(self):
        """Used to trigger an implicit call to 'write()' on the form
        to check the quantity.
        """
        return True
