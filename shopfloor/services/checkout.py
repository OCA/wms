# Copyright 2020-2021 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from werkzeug.exceptions import BadRequest

from odoo import _, fields

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from ..utils import to_float


class Checkout(Component):
    """
    Methods for the Checkout Process

    This scenario runs on existing moves.
    It happens on the "Packing" step of a pick/pack/ship.

    Use cases:

    1) Products are packed (e.g. full pallet shipping) and we keep the packages
    2) Products are packed (e.g. rollercage bins) and we create a new package
       with same content for shipping
    3) Products are packed (e.g. half-pallet ) and we merge several into one
    4) Products are packed (e.g. too high pallet) and we split it on several
    5) Products are not packed (e.g. raw products) and we create new packages
    6) Products are not packed (e.g. raw products) and we do not create packages

    A new flag ``shopfloor_checkout_done`` on move lines allows to track which
    lines have been checked out (can be with or without package).

    Flow Diagram: https://www.draw.io/#G1qRenBcezk50ggIazDuu2qOfkTsoIAxXP
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.checkout"
    _usage = "checkout"
    _description = __doc__

    def _response_for_select_line(
        self, picking, message=None, need_confirm_pack_all="", need_confirm_lot=None
    ):
        if all(line.shopfloor_checkout_done for line in picking.move_line_ids):
            return self._response_for_summary(picking, message=message)
        return self._response(
            next_state="select_line",
            data=self._data_for_select_line(
                picking,
                need_confirm_pack_all=need_confirm_pack_all,
                need_confirm_lot=need_confirm_lot,
            ),
            message=message,
        )

    def _data_for_select_line(
        self, picking, need_confirm_pack_all="", need_confirm_lot=None
    ):
        return {
            "picking": self._data_for_stock_picking(picking),
            "group_lines_by_location": True,
            "show_oneline_package_content": self.work.menu.show_oneline_package_content,
            "need_confirm_pack_all": need_confirm_pack_all,
            "need_confirm_lot": need_confirm_lot,
        }

    def _response_for_summary(self, picking, need_confirm=False, message=None):
        return self._response(
            next_state="summary" if not need_confirm else "confirm_done",
            data={
                "picking": self._data_for_stock_picking(picking, done=True),
                "all_processed": not bool(self._lines_to_pack(picking)),
            },
            message=message,
        )

    def _response_for_select_child_location(self, picking, message=None):
        return self._response(
            next_state="select_child_location",
            data={
                "picking": self._data_for_stock_picking(
                    picking, done=True, with_lines=False, with_location=True
                ),
            },
            message=message,
        )

    def _response_for_select_document(self, message=None):
        data = {"restrict_scan_first": self.work.menu.scan_location_or_pack_first}
        return self._response(next_state="select_document", message=message, data=data)

    def _response_for_manual_selection(self, message=None):
        pickings = self.env["stock.picking"].search(
            self._domain_for_list_stock_picking(),
            order=self._order_for_list_stock_picking(),
        )
        data = {"pickings": self.data.pickings(pickings)}
        return self._response(next_state="manual_selection", data=data, message=message)

    def _data_response_for_select_package(self, picking, lines):
        return {
            "selected_move_lines": self._data_for_move_lines(lines.sorted()),
            "picking": self.data.picking(picking),
            "packing_info": self._data_for_packing_info(picking),
            "no_package_enabled": not self.options.get("checkout__disable_no_package"),
            # Used by inheriting module
            "package_allowed": True,
        }

    def _response_for_select_package(self, picking, lines, message=None):
        return self._response(
            next_state="select_package",
            data=self._data_response_for_select_package(picking, lines),
            message=message,
        )

    def _data_for_packing_info(self, picking):
        """Return the packing information

        Intended to be extended.
        """
        # TODO: This could be avoided if included in the picking parser.
        return ""

    def _response_for_select_dest_package(self, picking, move_lines, message=None):
        packages = picking.mapped("move_line_ids.result_package_id").filtered(
            "packaging_id"
        )
        if not packages:
            # FIXME: do we want to move from 'select_dest_package' to
            # 'select_package' state? Until now (before enforcing the use of
            # delivery package) this part of code was never reached as we
            # always had a package on the picking (source or result)
            # Also the response validator did not support this state...
            return self._response_for_select_package(
                picking,
                move_lines,
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
                "selected_move_lines": self._data_for_move_lines(move_lines.sorted()),
            },
            message=message,
        )

    def _response_for_select_delivery_packaging(self, picking, packaging, message=None):
        return self._response(
            next_state="select_delivery_packaging",
            data={
                # We don't need to send the 'picking' as the mobile frontend
                # already has this info after `select_document` state
                # TODO adapt other endpoints to see if we can get rid of the
                # 'picking' data
                "packaging": self._data_for_delivery_packaging(packaging),
            },
            message=message,
        )

    def _response_for_change_packaging(self, picking, package, packaging_list):
        if not package:
            return self._response_for_summary(
                picking, message=self.msg_store.record_not_found()
            )

        return self._response(
            next_state="change_packaging",
            data={
                "picking": self.data.picking(picking),
                "package": self.data.package(
                    package, picking=picking, with_packaging=True
                ),
                "packaging": self.data.packaging_list(packaging_list.sorted()),
            },
        )

    def scan_document(self, barcode):
        """Scan a package, a product, a transfer or a location

        When a location is scanned, if all the move lines from this destination
        are for the same stock.picking, the stock.picking is used for the
        next steps.

        When a package is scanned, if the package has a move line to move it
        from a location/sublocation of the current stock.picking.type, the
        stock.picking for the package is used for the next steps.

        When a product is scanned, use the first picking (ordered by priority desc,
        scheduled_date asc, id desc) which has an ongoing move line with no source
        package for the given product.

        When a stock.picking is scanned, it is used for the next steps.

        In every case above, the stock.picking must be entirely available and
        must match the current picking type.

        Transitions:
        * select_document: when no stock.picking could be found
        * select_line: a stock.picking is selected
        * summary: stock.picking is selected and all its lines have a
          destination pack set
        """
        search_result = self._scan_document_find(barcode)
        result_handler = getattr(self, "_select_document_from_" + search_result.type)
        return result_handler(search_result.record)

    def _scan_document_find(self, barcode, search_types=None):
        search = self._actions_for("search")
        search_types = (
            "picking",
            "location",
            "package",
            "packaging",
        ) + (("product",) if not self.work.menu.scan_location_or_pack_first else ())
        return search.find(
            barcode,
            types=search_types,
        )

    def _select_document_from_picking(self, picking, **kw):
        return self._select_picking(picking, "select_document")

    def _select_document_from_location(self, location, **kw):
        if not self.is_src_location_valid(location):
            return self._response_for_select_document(
                message=self.msg_store.location_not_allowed()
            )
        lines = location.source_move_line_ids
        pickings = lines.mapped("picking_id")
        if len(pickings) > 1:
            return self._response_for_select_document(
                message={
                    "message_type": "error",
                    "body": _(
                        "Several transfers found, please scan a package"
                        " or select a transfer manually."
                    ),
                }
            )
        return self._select_picking(pickings, "select_document")

    def _select_document_from_package(self, package, **kw):
        pickings = package.move_line_ids.filtered(
            lambda ml: ml.state not in ("cancel", "done")
        ).picking_id
        if len(pickings) > 1:
            # Filter only if we find several pickings to narrow the
            # selection to one of the good type. If we have one picking
            # of the wrong type, it will be caught in _select_picking
            # with the proper error message.
            # Side note: rather unlikely to have several transfers ready
            # and moving the same things
            pickings = pickings.filtered(
                lambda p: p.picking_type_id in self.picking_types
            )
        return self._select_picking(fields.first(pickings), "select_document")

    def _select_document_from_product(self, product, line_domain=None, **kw):
        line_domain = line_domain or []
        line_domain.extend(
            [
                ("product_id", "=", product.id),
                ("state", "not in", ("cancel", "done")),
                ("package_id", "=", False),
            ]
        )
        lines = self.env["stock.move.line"].search(line_domain)
        picking = self.env["stock.picking"].search(
            [
                ("id", "in", lines.move_id.picking_id.ids),
                ("picking_type_id", "in", self.picking_types.ids),
            ],
            order="priority desc, scheduled_date asc, id desc",
            limit=1,
        )
        return self._select_picking(picking, "select_document")

    def _select_document_from_packaging(self, packaging, **kw):
        # And retrieve its product
        product = packaging.product_id
        # The picking should have a move line for the product
        # where qty >= packaging.qty, since it doesn't makes sense
        # to select a move line which have less qty than the packaging
        line_domain = [("product_uom_qty", ">=", packaging.qty)]
        return self._select_document_from_product(product, line_domain=line_domain)

    def _select_document_from_none(self, picking, **kw):
        """Handle result when no record is found."""
        return self._select_picking(picking, "select_document")

    def _select_picking(self, picking, state_for_error):
        if not picking:
            if state_for_error == "manual_selection":
                return self._response_for_manual_selection(
                    message=self.msg_store.stock_picking_not_found()
                )
            return self._response_for_select_document(
                message=self.msg_store.barcode_not_found()
            )
        if picking.picking_type_id not in self.picking_types:
            if state_for_error == "manual_selection":
                return self._response_for_manual_selection(
                    message=self.msg_store.cannot_move_something_in_picking_type()
                )
            return self._response_for_select_document(
                message=self.msg_store.cannot_move_something_in_picking_type()
            )
        if picking.state != "assigned":
            if state_for_error == "manual_selection":
                return self._response_for_manual_selection(
                    message=self.msg_store.stock_picking_not_available(picking)
                )
            return self._response_for_select_document(
                message=self.msg_store.stock_picking_not_available(picking)
            )
        return self._response_for_select_line(picking)

    def _data_for_move_lines(self, lines, **kw):
        return self.data.move_lines(lines, **kw)

    def _data_for_delivery_packaging(self, packaging, **kw):
        return self.data.delivery_packaging_list(packaging, **kw)

    def _data_for_stock_picking(
        self, picking, done=False, with_lines=True, with_location=False
    ):
        data = self.data.picking(picking)
        line_picker = self._lines_checkout_done if done else self._lines_to_pack
        if with_lines:
            data.update(
                {
                    "move_lines": self._data_for_move_lines(
                        self._lines_prepare(picking, line_picker(picking)),
                        with_packaging=done,
                    )
                }
            )
        if with_location:
            data.update({"location_dest": self.data.location(picking.location_dest_id)})
        return data

    def _lines_checkout_done(self, picking):
        return picking.move_line_ids.filtered(self._filter_lines_checkout_done)

    def _lines_to_pack(self, picking):
        return picking.move_line_ids.filtered(self._filter_lines_unpacked)

    def _lines_prepare(self, picking, selected_lines):
        """Hook to manipulate lines' ordering or anything else before sending them back."""
        return selected_lines

    def _domain_for_list_stock_picking(self):
        return [
            ("state", "=", "assigned"),
            ("picking_type_id", "in", self.picking_types.ids),
        ]

    def _order_for_list_stock_picking(self):
        return "priority desc, scheduled_date asc, id asc"

    def list_stock_picking(self):
        """List stock.picking records available

        Returns a list of all the available records for the current picking
        type.

        Transitions:
        * manual_selection: to the selection screen
        """
        return self._response_for_manual_selection()

    def select(self, picking_id):
        """Select a stock picking for the scenario

        Used from the list of stock pickings (manual_selection), from there,
        the user can click on a stock.picking record which calls this method.

        The ``list_stock_picking`` returns only the valid records (same picking
        type, fully available, ...), but this method has to check again in case
        something changed since the list was sent to the client.

        Transitions:
        * manual_selection: stock.picking could finally not be selected (not
          available, ...)
        * summary: goes straight to this state used to set the moves as done when
          all the move lines with a reserved quantity have a 'quantity done'
        * select_line: the "normal" case, when the user has to put in pack/move
          lines
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_manual_selection(message=message)
        return self._select_picking(picking, "manual_selection")

    def _select_lines(self, lines, prefill_qty=0, related_lines=None):
        for i, line in enumerate(lines):
            if line.shopfloor_checkout_done:
                continue
            if self.work.menu.no_prefill_qty and i == 0:
                # For prefill quantity we only want to increment one line
                line.qty_done += prefill_qty
            elif not self.work.menu.no_prefill_qty:
                line.qty_done = line.product_uom_qty
            line.shopfloor_user_id = self.env.user

        picking = lines.mapped("picking_id")
        other_lines = picking.move_line_ids - lines
        self._deselect_lines(other_lines)
        if related_lines:
            lines += related_lines
        return lines

    def _deselect_lines(self, lines):
        lines.filtered(lambda l: not l.shopfloor_checkout_done).write(
            {"qty_done": 0, "shopfloor_user_id": False}
        )

    def scan_line(self, picking_id, barcode, confirm_pack_all=False, confirm_lot=None):
        """Scan move lines of the stock picking

        It allows to select move lines of the stock picking for the next
        screen. Lines can be found either by scanning a package, a product or a
        lot.

        There should be no ambiguity, so for instance if a product is scanned but
        several packs contain it, the endpoint will ask to scan a pack; if the
        product is tracked by lot, to scan a lot.

        Once move lines are found, their ``qty_done`` is set to their reserved
        quantity.

        Transitions:
        * select_line: nothing could be found for the barcode
        * select_package: lines are selected, user is redirected to this
        * summary: delivery package is scanned and all lines are done
        screen to change the qty done and destination pack if needed
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)

        selection_lines = self._lines_to_pack(picking)
        if not selection_lines:
            return self._response_for_summary(picking)

        # Search of the destination package
        search_result = self._scan_line_find(picking, barcode)
        result_handler = getattr(self, "_select_lines_from_" + search_result.type)
        kw = {"confirm_pack_all": confirm_pack_all, "confirm_lot": confirm_lot}
        return result_handler(picking, selection_lines, search_result.record, **kw)

    def _scan_line_find(self, picking, barcode, search_types=None):
        search = self._actions_for("search")
        search_types = (
            "package",
            "product",
            "packaging",
            "lot",
            "serial",
            "delivery_packaging",
        )
        return search.find(
            barcode,
            types=search_types,
            handler_kw=dict(
                lot=dict(products=picking.move_lines.product_id),
                serial=dict(products=picking.move_lines.product_id),
            ),
        )

    def _select_lines_from_none(self, picking, selection_lines, record, **kw):
        """Handle result when no record is found."""
        return self._response_for_select_line(
            picking, message=self.msg_store.barcode_not_found()
        )

    def _select_lines_from_package(
        self, picking, selection_lines, package, prefill_qty=0, **kw
    ):
        lines = selection_lines.filtered(
            lambda l: l.package_id == package and not l.shopfloor_checkout_done
        )
        if not lines:
            return self._response_for_select_line(
                picking,
                message={
                    "message_type": "error",
                    "body": _("Package {} is not in the current transfer.").format(
                        package.name
                    ),
                },
            )
        self._select_lines(lines, prefill_qty=prefill_qty)
        if self.work.menu.no_prefill_qty:
            lines = picking.move_line_ids
        return self._response_for_select_package(picking, lines)

    def _select_lines_from_product(
        self, picking, selection_lines, product, prefill_qty=1, check_lot=True, **kw
    ):
        # TODO: should we propagate 'kw.get("message")' content on each return?
        if product.tracking in ("lot", "serial") and check_lot:
            return self._response_for_select_line(
                picking, message=self.msg_store.scan_lot_on_product_tracked_by_lot()
            )

        lines = selection_lines.filtered(lambda l: l.product_id == product)
        if not lines:
            return self._response_for_select_line(
                picking, message=self.msg_store.product_not_found_in_current_picking()
            )

        # When products are as units outside of packages, we can select them for
        # packing, but if they are in a package, we want the user to scan the packages.
        # If the product is only in one package though, scanning the product selects
        # the package.
        packages = lines.mapped("package_id")
        related_lines = self.env["stock.move.line"].browse()
        # Do not use mapped here: we want to see if we have more than one package,
        # but also if we have one product as a package and the same product as
        # a unit in another line. In both cases, we want the user to scan the
        # package.
        if packages and len({line.package_id for line in lines}) > 1:
            return self._response_for_select_line(
                picking, message=self.msg_store.product_multiple_packages_scan_package()
            )
        elif packages:
            # Select all the lines of the package when we scan a product in a
            # package and we have only one.
            return self._select_lines_from_package(
                picking,
                selection_lines,
                packages,
                prefill_qty=prefill_qty,
                message=kw.get("message"),
            )
        else:
            # There is no package on selected lines, so also select all other lines
            # not in a package. But only the quantity on first selected lines
            # are updated.
            related_lines = selection_lines.filtered(
                lambda l: not l.package_id and l.product_id != product
            )

        lines = self._select_lines(
            lines, prefill_qty=prefill_qty, related_lines=related_lines
        )
        return self._response_for_select_package(
            picking, lines, message=kw.get("message")
        )

    def _select_lines_from_packaging(self, picking, selection_lines, packaging, **kw):
        return self._select_lines_from_product(
            picking, selection_lines, packaging.product_id, prefill_qty=packaging.qty
        )

    def _select_lines_from_lot(
        self, picking, selection_lines, lot, prefill_qty=1, **kw
    ):
        message = None
        lines = self._picking_lines_by_lot(picking, selection_lines, lot)
        if not lines:
            change_package_lot = self._actions_for("change.package.lot")
            if not kw.get("confirm_lot"):
                lines_same_product = (
                    change_package_lot.filter_lines_allowed_to_change_lot(
                        selection_lines, lot
                    )
                )
                # If there's at least one product matching we are good to go.
                # In any case, only the 1st line matching will be affected.
                if lines_same_product:
                    return self._response_for_select_line(
                        picking,
                        message=self.msg_store.lot_different_change(),
                        need_confirm_lot=lot.id,
                    )
                return self._response_for_select_line(
                    picking,
                    message=self.msg_store.lot_not_found_in_picking(lot, picking),
                )
            # Validate the scanned lot against the previous one
            if lot.id != kw["confirm_lot"]:
                expected_lot = lot.browse(kw["confirm_lot"]).exists()
                return self._response_for_select_line(
                    picking,
                    message=self.msg_store.lot_change_wrong_lot(expected_lot.name),
                )
            # Change lot confirmed
            line = fields.first(
                selection_lines.filtered(
                    lambda l: l.product_id == lot.product_id and l.lot_id != lot
                )
            )
            if not line:
                return self._response_for_select_line(
                    picking,
                    message=self.msg_store.lot_change_no_line_found(),
                )
            response_ok_func = self._change_lot_response_handler_ok
            response_error_func = self._change_lot_response_handler_error
            message = change_package_lot.change_lot(
                line, lot, response_ok_func, response_error_func
            )
            if message["message_type"] == "error":
                return self._response_for_select_line(picking, message=message)
            else:
                lines = line
                # Some lines have been recreated, refresh the recordset
                # to avoid CacheMiss error
                selection_lines = self._lines_to_pack(picking)

        # Related lines will be visible with the line picked (qty done changed)
        related_lines = self.env["stock.move.line"]
        packages = lines.mapped("package_id")
        # Do not use mapped here: we want to see if we have more than one
        # package, but also if we have one lot as a package and the same lot as
        # a unit in another line. In both cases, we want the user to scan the
        # package.
        # NOTE: change_pack_lot already checked this, so if we changed the lot
        # we are already safe.
        if packages and len({line.package_id for line in lines}) > 1:
            # The lot is spread out in multiple packages, ask to scan a package
            return self._response_for_select_line(
                picking, message=self.msg_store.lot_multiple_packages_scan_package()
            )
        elif packages:
            # The lot is only in one package
            # Related lines are the one in the same package
            related_lines = selection_lines.filtered(
                lambda l: l.package_id == packages and l.lot_id != lot
            )
        else:
            # Lot as units outside of packages, can be selected for packing.
            # Related lines are all other lines not in a package
            related_lines = selection_lines.filtered(
                lambda l: not l.package_id and l.lot_id != lot
            )
        # Only one line selected should have its quantity done updated
        line_to_update = fields.first(lines)
        if len(lines) > 1:
            related_lines |= lines - line_to_update

        lines = self._select_lines(
            line_to_update, prefill_qty=prefill_qty, related_lines=related_lines
        )
        return self._response_for_select_package(picking, lines, message=message)

    def _picking_lines_by_lot(self, picking, selection_lines, lot):
        """Control filtering of selected lines by given lot."""
        return selection_lines.filtered(lambda l: l.lot_id == lot)

    def _change_lot_response_handler_ok(self, move_line, message=None):
        return message

    def _change_lot_response_handler_error(self, move_line, message=None):
        return message

    def _select_lines_from_serial(self, picking, selection_lines, lot, **kw):
        # Search for serial number is actually the same as searching for lot (as of v14...)
        return self._select_lines_from_lot(picking, selection_lines, lot, **kw)

    # Handling of the destination package scanned
    def _select_lines_from_delivery_packaging(
        self, picking, selection_lines, packaging, confirm_pack_all=None, **kw
    ):
        """Handle delivery packaging.

        A delivery pkg has been scanned:

            1. validate it
            2. no lines to process (no quantities set to done)
                2.a Option no prefill qty, ask to set some quantities
                2.b Otherwise ask confirmation to pack everything if not yet done
            3. if confirmation to pack everything set all quantities.
            4. assign new package and skip `select_package` state

        """
        carrier = self._get_carrier(picking)
        if carrier:
            # Validate against carrier
            is_valid = self._packaging_good_for_carrier(packaging, carrier)
        else:
            is_valid = True
        if carrier and not is_valid:
            return self._response_for_select_line(
                picking,
                message=self.msg_store.packaging_invalid_for_carrier(
                    packaging, carrier
                ),
            )
        message = None
        need_confirm_pack_all = ""
        has_lines_to_pack = any(
            self._filter_lines_to_pack(ml) for ml in selection_lines
        )
        if not has_lines_to_pack:
            if self.work.menu.no_prefill_qty:
                message = self.msg_store.no_lines_to_process_set_quantities()
            elif confirm_pack_all != packaging.barcode:
                need_confirm_pack_all = packaging.barcode
                message = self.msg_store.confirm_put_all_goods_in_delivery_package(
                    packaging
                )
            if message:
                return self._response_for_select_line(
                    picking,
                    message=message,
                    need_confirm_pack_all=need_confirm_pack_all,
                )
        if confirm_pack_all == packaging.barcode:
            self._select_lines(selection_lines)
        return self._create_and_assign_new_packaging(
            picking, selection_lines, packaging=packaging
        )

    def _select_line_package(self, picking, selection_lines, package):
        if not package:
            return self._response_for_select_line(
                picking, message=self.msg_store.record_not_found()
            )
        return self._select_lines_from_package(picking, selection_lines, package)

    def _select_line_move_line(self, picking, selection_lines, move_line):
        if not move_line:
            return self._response_for_select_line(
                picking, message=self.msg_store.record_not_found()
            )
        # normally, the client should sent only move lines out of packages, but
        # in case there is a package, handle it as a package
        if move_line.package_id:
            return self._select_lines_from_package(
                picking, selection_lines, move_line.package_id
            )

        related_lines = selection_lines.filtered(
            lambda l: not l.package_id and l.product_id != move_line.product_id
        )
        lines = self._select_lines(move_line, related_lines=related_lines)
        return self._response_for_select_package(picking, lines)

    def select_line(self, picking_id, package_id=None, move_line_id=None):
        """Select move lines of the stock picking

        This is the same as ``scan_line``, except that a package id or a
        move_line_id is given by the client (user clicked on a list).

        It returns a list of move line ids that will be displayed by the
        screen ``select_package``. This screen will have to send this list to
        the endpoints it calls, so we can select/deselect lines but still
        show them in the list of the client application.

        Transitions:
        * select_line: nothing could be found for the barcode
        * select_package: lines are selected, user is redirected to this
        screen to change the qty done and destination package if needed
        """
        assert package_id or move_line_id

        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)

        selection_lines = self._lines_to_pack(picking)
        if not selection_lines:
            return self._response_for_summary(picking)

        if package_id:
            package = self.env["stock.quant.package"].browse(package_id).exists()
            return self._select_line_package(picking, selection_lines, package)
        if move_line_id:
            move_line = self.env["stock.move.line"].browse(move_line_id).exists()
            return self._select_line_move_line(picking, selection_lines, move_line)

    def _change_line_qty(
        self, picking_id, selected_line_ids, move_line_ids, quantity_func
    ):
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)

        move_lines = self.env["stock.move.line"].browse(move_line_ids).exists()

        message = None
        if not move_lines:
            message = self.msg_store.record_not_found()
        for move_line in move_lines:
            qty_done = quantity_func(move_line)
            if qty_done < 0:
                message = {
                    "body": _("Negative quantity not allowed."),
                    "message_type": "error",
                }
            else:
                new_line = self.env["stock.move.line"]
                if qty_done > 0:
                    new_line, qty_check = move_line._split_qty_to_be_done(
                        qty_done,
                        split_partial=False,
                        result_package_id=False,
                    )
                move_line.qty_done = qty_done
                if new_line:
                    selected_line_ids.append(new_line.id)
                if qty_done > move_line.product_uom_qty:
                    return self._response_for_select_package(
                        picking,
                        self.env["stock.move.line"].browse(selected_line_ids).exists(),
                        message=self.msg_store.line_scanned_qty_done_higher_than_allowed(),
                    )
        return self._response_for_select_package(
            picking,
            self.env["stock.move.line"].browse(selected_line_ids).exists(),
            message=message,
        )

    def reset_line_qty(self, picking_id, selected_line_ids, move_line_id):
        """Reset qty_done of a move line to zero

        Used to deselect a line in the "select_package" screen.
        The selected_line_ids parameter is used to keep the selection of lines
        stateless.

        Transitions:
        * select_package: goes back to the same state, the line will appear
        as deselected
        """
        return self._change_line_qty(
            picking_id, selected_line_ids, [move_line_id], lambda __: 0
        )

    def set_line_qty(self, picking_id, selected_line_ids, move_line_id):
        """Set qty_done of a move line to its reserved quantity

        Used to select a line in the "select_package" screen.
        The selected_line_ids parameter is used to keep the selection of lines
        stateless.

        Transitions:
        * select_package: goes back to the same state, the line will appear
        as selected
        """
        return self._change_line_qty(
            picking_id, selected_line_ids, [move_line_id], lambda l: l.product_uom_qty
        )

    def set_custom_qty(self, picking_id, selected_line_ids, move_line_id, qty_done):
        """Change qty_done of a move line with a custom value

        The selected_line_ids parameter is used to keep the selection of lines
        stateless.

        Transitions:
        * select_package: goes back to this screen showing all the lines after
          we changed the qty
        """
        return self._change_line_qty(
            picking_id, selected_line_ids, [move_line_id], lambda __: qty_done
        )

    def _switch_line_qty_done(self, picking, selected_lines, switch_lines):
        """Switch qty_done on lines and return to the 'select_package' state

        If at least one of the lines to switch has a qty_done, set them all
        to zero. If all the lines to switch have a zero qty_done, switch them
        to their quantity to deliver.
        """
        if any(line.qty_done for line in switch_lines):
            return self._change_line_qty(
                picking.id, selected_lines.ids, switch_lines.ids, lambda __: 0
            )
        else:
            return self._change_line_qty(
                picking.id,
                selected_lines.ids,
                switch_lines.ids,
                lambda l: l.product_uom_qty,
            )

    def _increment_custom_qty(
        self, picking, selected_lines, increment_lines, qty_increment
    ):
        """Increment the  qty_done of a move line with a custom value

        The selected_line parameter is used to keep the selection of lines
        stateless.

        Transitions:
        * select_package: goes back to this screen showing all the lines after
          we changed the qty
        """
        return self._change_line_qty(
            picking.id,
            selected_lines.ids,
            increment_lines.ids,
            lambda line: line.qty_done + qty_increment,
        )

    @staticmethod
    def _filter_lines_unpacked(move_line):
        return (
            move_line.qty_done == 0 or move_line.shopfloor_user_id
        ) and not move_line.shopfloor_checkout_done

    @staticmethod
    def _filter_lines_to_pack(move_line):
        return move_line.qty_done > 0 and not move_line.shopfloor_checkout_done

    @staticmethod
    def _filter_lines_checkout_done(move_line):
        return move_line.qty_done > 0 and move_line.shopfloor_checkout_done

    def _is_package_allowed(self, picking, package):
        """Check if a package is allowed as a destination/delivery package.

        A package is allowed as a destination one if it is present among
        `picking` lines and qualified as a "delivery package" (having a
        delivery packaging set on it).
        """
        existing_packages = picking.mapped("move_line_ids.result_package_id").filtered(
            "packaging_id"
        )
        return package in existing_packages

    def _put_lines_in_package(self, picking, selected_lines, package):
        """Put the current selected lines with a qty_done in a package

        Note: only packages which are already a delivery package for another
        line of the stock picking can be selected. Packages which are the
        source packages are allowed too only if it is a delivery package (we
        keep the current package).
        """
        if not self._is_package_allowed(picking, package):
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=self.msg_store.dest_package_not_valid(package),
            )
        return self._pack_lines(picking, selected_lines, package)

    def _put_lines_in_allowed_package(self, picking, lines_to_pack, package):
        for line in lines_to_pack:
            if line.qty_done < line.product_uom_qty:
                line._split_partial_quantity_to_be_done(line.qty_done, {})
        lines_to_pack.write(
            {"result_package_id": package.id, "shopfloor_checkout_done": True}
        )
        self._post_put_lines_in_package(lines_to_pack)
        # Hook to this method to override the response
        # if anything else has to be handled
        # before auto posting the lines.
        return {}

    def _post_put_lines_in_package(self, lines_packaged):
        """Hook to override."""

    def _create_and_assign_new_packaging(self, picking, selected_lines, packaging=None):
        actions = self._actions_for("packaging")
        package = actions.create_package_from_packaging(packaging=packaging)
        return self._pack_lines(picking, selected_lines, package)

    def _pack_lines(self, picking, selected_lines, package):
        lines_to_pack = selected_lines.filtered(self._filter_lines_to_pack)
        if not lines_to_pack:
            message = self.msg_store.no_line_to_pack()
            return self._response_for_select_line(
                picking,
                message=message,
            )
        response = self._put_lines_in_allowed_package(picking, lines_to_pack, package)
        if response:
            return response
        if self.work.menu.auto_post_line:
            # If option auto_post_line is active in the shopfloor menu,
            # create a split order with these packed lines.
            self._auto_post_lines(lines_to_pack)
        message = self.msg_store.goods_packed_in(package)
        # go back to the screen to select the next lines to pack
        return self._response_for_select_line(
            picking,
            message=message,
        )

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
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)

        selected_lines = self.env["stock.move.line"].browse(selected_line_ids).exists()
        search_result = self._scan_package_find(picking, barcode)
        message = self._check_scan_package_find(picking, search_result)
        if message:
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=message,
            )
        result_handler = getattr(
            self, "_scan_package_action_from_" + search_result.type
        )
        return result_handler(picking, selected_lines, search_result.record)

    def _scan_package_find(self, picking, barcode, search_types=None):
        search = self._actions_for("search")
        search_types = (
            "package",
            "product",
            "packaging",
            "lot",
            "serial",
            "delivery_packaging",
        )
        return search.find(
            barcode,
            types=search_types,
            handler_kw=dict(
                lot=dict(products=picking.move_lines.product_id),
                serial=dict(products=picking.move_lines.product_id),
            ),
        )

    def _check_scan_package_find(self, picking, search_result):
        # Used by inheriting modules
        return False

    def _find_line_to_increment(self, product_lines):
        """Find which line should have its qty incremented.

        Return the first line for the scanned product
        which still has some qty todo.
        If none are found, return the first line for that product.
        """
        return next(
            (line for line in product_lines if line.qty_done < line.product_uom_qty),
            fields.first(product_lines),
        )

    def _scan_package_action_from_product(
        self, picking, selected_lines, product, packaging=None, **kw
    ):
        if product.tracking in ("lot", "serial"):
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=self.msg_store.scan_lot_on_product_tracked_by_lot(),
            )
        product_lines = selected_lines.filtered(lambda l: l.product_id == product)
        if self.work.menu.no_prefill_qty:
            quantity_increment = packaging.qty if packaging else 1
            return self._increment_custom_qty(
                picking,
                selected_lines,
                self._find_line_to_increment(product_lines),
                quantity_increment,
            )
        return self._switch_line_qty_done(picking, selected_lines, product_lines)

    def _scan_package_action_from_packaging(
        self, picking, selected_lines, packaging, **kw
    ):
        return self._scan_package_action_from_product(
            picking, selected_lines, packaging.product_id, packaging=packaging
        )

    def _scan_package_action_from_lot(self, picking, selected_lines, lot, **kw):
        lot_lines = selected_lines.filtered(lambda l: l.lot_id == lot)
        if self.work.menu.no_prefill_qty:
            return self._increment_custom_qty(
                picking, selected_lines, self._find_line_to_increment(lot_lines), 1
            )
        return self._switch_line_qty_done(picking, selected_lines, lot_lines)

    def _scan_package_action_from_serial(self, picking, selection_lines, lot, **kw):
        # Search for serial number is actually the same as searching for lot (as of v14...)
        return self._scan_package_action_from_lot(picking, selection_lines, lot, **kw)

    def _scan_package_action_from_package(self, picking, selected_lines, package, **kw):
        if not package.packaging_id:
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=self.msg_store.dest_package_not_valid(package),
            )
        return self._put_lines_in_package(picking, selected_lines, package)

    def _scan_package_action_from_delivery_packaging(
        self, picking, selected_lines, packaging, **kw
    ):
        carrier = self._get_carrier(picking)
        if carrier:
            # Validate against carrier
            is_valid = self._packaging_good_for_carrier(packaging, carrier)
        else:
            is_valid = True
        if carrier and not is_valid:
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=self.msg_store.packaging_invalid_for_carrier(
                    packaging, carrier
                ),
            )
        return self._create_and_assign_new_packaging(picking, selected_lines, packaging)

    def _scan_package_action_from_none(self, picking, selected_lines, record, **kw):
        return self._response_for_select_package(
            picking, selected_lines, message=self.msg_store.barcode_not_found()
        )

    def _get_carrier(self, picking):
        return picking.ship_carrier_id or picking.carrier_id

    def _packaging_good_for_carrier(self, packaging, carrier):
        actions = self._actions_for("packaging")
        return actions.packaging_valid_for_carrier(packaging, carrier)

    def _get_available_delivery_packaging(self, picking):
        model = self.env["product.packaging"]
        carrier = picking.ship_carrier_id or picking.carrier_id
        if not carrier:
            return model.browse()
        return model.search(
            [
                ("product_id", "=", False),
                ("package_carrier_type", "=", carrier.delivery_type or "none"),
            ],
            order="name",
        )

    def list_delivery_packaging(self, picking_id, selected_line_ids):
        """List available delivery packaging for given picking.

        Transitions:
        * select_delivery_packaging: list available delivery packaging, the
        user has to choose one to create the new package
        * select_package: when no delivery packaging is available
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
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

    def new_package(self, picking_id, selected_line_ids, packaging_id=None):
        """Add all selected lines in a new package

        It creates a new package and set it as the destination package of all
        the selected lines.

        Selected lines are move lines in the list of ``move_line_ids`` where
        ``qty_done`` > 0 and have no destination package
        (shopfloor_checkout_done is False).

        Transitions:
        * select_line: goes back to selection of lines to work on next lines
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        packaging = None
        if packaging_id:
            packaging = self.env["product.packaging"].browse(packaging_id).exists()
        selected_lines = self.env["stock.move.line"].browse(selected_line_ids).exists()
        return self._create_and_assign_new_packaging(picking, selected_lines, packaging)

    def no_package(self, picking_id, selected_line_ids):
        """Process all selected lines without any package.

        Selected lines are move lines in the list of ``move_line_ids`` where
        ``qty_done`` > 0 and have no destination package
        (shopfloor_checkout_done is False).

        Transitions:
        * select_line: goes back to selection of lines to work on next lines
        """
        if self.options.get("checkout__disable_no_package"):
            raise BadRequest("`checkout.no_package` endpoint is not enabled")
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        selected_lines = self.env["stock.move.line"].browse(selected_line_ids).exists()
        selected_lines_with_qty_done = selected_lines.filtered(
            lambda line: line.qty_done > 0
        )
        selected_lines_with_qty_done.write(
            {"shopfloor_checkout_done": True, "result_package_id": False}
        )
        response = self._check_allowed_qty_done(picking, selected_lines)
        if response:
            return response
        return self._response_for_select_line(
            picking,
            message={
                "message_type": "success",
                "body": _("Product(s) processed as raw product(s)"),
            },
        )

    def list_dest_package(self, picking_id, selected_line_ids):
        """Return a list of packages the user can select for the lines

        Only valid packages must be proposed. Look at ``scan_dest_package``
        for the conditions to be valid.

        Transitions:
        * select_dest_package: selection screen
        * select_package: when no package is available
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        lines = self.env["stock.move.line"].browse(selected_line_ids).exists()
        response = self._check_allowed_qty_done(picking, lines)
        if response:
            return response
        return self._response_for_select_dest_package(picking, lines)

    def _check_allowed_qty_done(self, picking, lines):
        for line in lines:
            # Do not allow to proceed if the qty_done of
            # any of the selected lines
            # is higher than the quantity to do.
            if line.qty_done > line.product_uom_qty:
                return self._response_for_select_package(
                    picking,
                    lines,
                    message=self.msg_store.selected_lines_qty_done_higher_than_allowed(),
                )

    def _set_dest_package_from_selection(self, picking, selected_lines, package):
        if not self._is_package_allowed(picking, package):
            return self._response_for_select_dest_package(
                picking,
                selected_lines,
                message=self.msg_store.dest_package_not_valid(package),
            )
        return self._pack_lines(picking, selected_lines, package)

    def scan_dest_package(self, picking_id, selected_line_ids, barcode):
        """Scan destination package for lines

        Set the destination package on the selected lines with a `qty_done` if
        the package is valid. It is valid when one of:

        * it is already the destination package of another line of the stock.picking
        * it is the source package of the selected lines

        Note: by default, Odoo puts the same destination package as the source
        package on lines.

        Transitions:
        * select_dest_package: error when scanning package
        * select_line: lines to package remain
        * summary: all lines are put in packages
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        lines = self.env["stock.move.line"].browse(selected_line_ids).exists()
        search = self._actions_for("search")
        package = search.package_from_scan(barcode)
        if not package:
            return self._response_for_select_dest_package(
                picking,
                lines,
                message=self.msg_store.package_not_found_for_barcode(barcode),
            )
        return self._set_dest_package_from_selection(picking, lines, package)

    def set_dest_package(self, picking_id, selected_line_ids, package_id):
        """Set destination package for lines from a package id

        Used by the list obtained from ``list_dest_package``.

        The validity is the same as ``scan_dest_package``.

        Transitions:
        * select_dest_package: error when selecting package
        * select_line: lines to package remain
        * summary: all lines are put in packages
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        lines = self.env["stock.move.line"].browse(selected_line_ids).exists()
        package = self.env["stock.quant.package"].browse(package_id).exists()
        if not package:
            return self._response_for_select_dest_package(
                picking,
                lines,
                message=self.msg_store.record_not_found(),
            )
        return self._set_dest_package_from_selection(picking, lines, package)

    def _auto_post_lines(self, selected_lines):
        moves = self.env["stock.move"]
        for line in selected_lines:
            move = line.move_id.split_other_move_lines(line, intersection=True)
            moves = moves | move
        moves.extract_and_action_done()

    def summary(self, picking_id):
        """Return information for the summary screen

        Transitions:
        * summary
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        return self._response_for_summary(picking)

    def _get_allowed_packaging(self):
        return self.env["product.packaging"].search([("product_id", "=", False)])

    def list_packaging(self, picking_id, package_id):
        """List the available package types for a package

        For a package, we can change the packaging. The available
        packaging are the ones with no product.

        Transitions:
        * change_packaging
        * summary: if the package_id no longer exists
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        package = self.env["stock.quant.package"].browse(package_id).exists()
        packaging_list = self._get_allowed_packaging()
        return self._response_for_change_packaging(picking, package, packaging_list)

    def set_packaging(self, picking_id, package_id, packaging_id):
        """Set a package type on a package

        Transitions:
        * change_packaging: in case of error
        * summary
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)

        package = self.env["stock.quant.package"].browse(package_id).exists()
        packaging = self.env["product.packaging"].browse(packaging_id).exists()
        if not (package and packaging):
            return self._response_for_summary(
                picking, message=self.msg_store.record_not_found()
            )
        package.packaging_id = packaging
        return self._response_for_summary(
            picking,
            message={
                "message_type": "success",
                "body": _("Packaging changed on package {}").format(package.name),
            },
        )

    def cancel_line(self, picking_id, package_id=None, line_id=None):
        """Cancel work done on given line or package.

        If package, remove destination package from lines and set qty done to 0.
        If line is a raw product, set qty done to 0.

        All the move lines with the package as ``result_package_id`` have their
        ``result_package_id`` reset to the source package (default odoo behavior)
        and their ``qty_done`` set to 0.

        It flags ``shopfloor_checkout_done`` to False
        so they have to be processed again.

        Transitions:
        * summary: if package or line are not found
        * select_line: when package or line has been canceled
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)

        package = self.env["stock.quant.package"].browse(package_id).exists()
        line = self.env["stock.move.line"].browse(line_id).exists()
        if not package and not line:
            return self._response_for_summary(
                picking, message=self.msg_store.record_not_found()
            )

        if package:
            move_lines = picking.move_line_ids.filtered(
                lambda l: self._filter_lines_checkout_done(l)
                and l.result_package_id == package
            )
            for move_line in move_lines:
                move_line.write(
                    {
                        "qty_done": 0,
                        "result_package_id": move_line.package_id,
                        "shopfloor_checkout_done": False,
                    }
                )
            msg = _("Package cancelled")
        if line:
            line.write({"qty_done": 0, "shopfloor_checkout_done": False})
            msg = _("Line cancelled")
        return self._response_for_select_line(
            picking, message={"message_type": "success", "body": msg}
        )

    def done(self, picking_id, confirmation=False):
        """Set the moves as done

        If some lines have not the full ``qty_done`` or no destination package set,
        a confirmation is asked to the user.

        Transitions:
        * summary: in case of error
        * select_document: after done, goes back to start
        * confirm_done: confirm a partial
        * select_child_location: there are child destination locations
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        lines = picking.move_line_ids
        if not confirmation:
            if not all(line.qty_done == line.product_uom_qty for line in lines):
                return self._response_for_summary(
                    picking,
                    need_confirm=True,
                    message=self.msg_store.transfer_confirm_done(),
                )
            elif not all(line.shopfloor_checkout_done for line in lines):
                return self._response_for_summary(
                    picking,
                    need_confirm=True,
                    message={
                        "message_type": "warning",
                        "body": _("Remaining raw product not packed, proceed anyway?"),
                    },
                )
        lines_done = self._lines_checkout_done(picking)
        dest_location = lines_done.move_id.location_dest_id
        if len(dest_location) != 1 or dest_location.usage == "view":
            return self._response_for_select_child_location(
                picking,
            )
        stock = self._actions_for("stock")
        stock.validate_moves(lines_done.move_id)
        return self._response_for_select_document(
            message=self.msg_store.transfer_done_success(lines_done.picking_id)
        )

    def scan_dest_location(self, picking_id, barcode):
        """Select a location destination

        When setting the move as done, if the destination location
        has children locations, ask the user to scan one of them.

        Transitions:
        * select_document: after done, goes back to start
        * select_child_location: in case of error
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        search = self._actions_for("search")
        scanned_location = search.location_from_scan(barcode)
        if not scanned_location:
            return self._response_for_select_child_location(
                picking,
                message=self.msg_store.location_not_found(),
            )
        allowed_locations = self.env["stock.location"].search(
            [("id", "child_of", picking.location_dest_id.id), ("usage", "!=", "view")]
        )
        if scanned_location not in allowed_locations:
            return self._response_for_select_child_location(
                picking,
                message=self.msg_store.dest_location_not_allowed(),
            )
        lines_done = self._lines_checkout_done(picking)
        for line in lines_done:
            line.update({"location_dest_id": scanned_location.id})
        stock = self._actions_for("stock")
        stock.validate_moves(lines_done.move_id)
        return self._response_for_select_document(
            message=self.msg_store.transfer_done_success(lines_done.picking_id)
        )


class ShopfloorCheckoutValidator(Component):
    """Validators for the Checkout endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.checkout.validator"
    _usage = "checkout.validator"

    def scan_document(self):
        return {"barcode": {"required": True, "type": "string"}}

    def list_stock_picking(self):
        return {}

    def select(self):
        return {"picking_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def scan_line(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "confirm_pack_all": {
                "type": "string",
                "nullable": True,
                "required": False,
            },
            "confirm_lot": {
                "type": "integer",
                "nullable": True,
                "required": False,
            },
        }

    def select_line(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": False, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": False, "type": "integer"},
        }

    def reset_line_qty(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_line_qty(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_custom_qty(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "qty_done": {"coerce": to_float, "required": True, "type": "float"},
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

    def list_delivery_packaging(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
        }

    def new_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "packaging_id": {"coerce": to_int, "required": False, "type": "integer"},
        }

    def no_package(self):
        return self.new_package()

    def list_dest_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
        }

    def scan_dest_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "barcode": {"required": True, "type": "string"},
        }

    def set_dest_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def summary(self):
        return {"picking_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def list_packaging(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_packaging(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
            "packaging_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def cancel_line(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {
                "coerce": to_int,
                "required": False,
                "type": "integer",
                # excludes does not set the other as not required??? :/
                "excludes": "line_id",
            },
            "line_id": {
                "coerce": to_int,
                "required": False,
                "type": "integer",
                "excludes": "package_id",
            },
        }

    def done(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def scan_dest_location(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }


class ShopfloorCheckoutValidatorResponse(Component):
    """Validators for the Checkout endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.checkout.validator.response"
    _usage = "checkout.validator.response"

    _start_state = "select_document"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "select_document": self._schema_for_select_document,
            "manual_selection": self._schema_selection_list,
            "select_line": self._schema_stock_picking_details,
            "select_package": dict(
                self._schema_selected_lines,
                packing_info={"type": "string", "nullable": True},
                no_package_enabled={
                    "type": "boolean",
                    "nullable": True,
                    "required": False,
                },
                package_allowed={
                    "type": "boolean",
                    "nullable": True,
                    "required": False,
                },
            ),
            "change_quantity": self._schema_selected_lines,
            "select_dest_package": self._schema_select_package,
            "select_delivery_packaging": self._schema_select_delivery_packaging,
            "summary": self._schema_summary,
            "change_packaging": self._schema_select_packaging,
            "confirm_done": self._schema_confirm_done,
            "select_child_location": self._schema_select_child_location,
        }

    @property
    def _schema_for_select_document(self):
        return {
            "restrict_scan_first": {
                "type": "boolean",
                "nullable": False,
                "required": True,
            },
        }

    def _schema_stock_picking(self, lines_with_packaging=False):
        schema = self.schemas.picking()
        schema.update(
            {
                "move_lines": self.schemas._schema_list_of(
                    self.schemas.move_line(with_packaging=lines_with_packaging)
                )
            }
        )
        return {"picking": self.schemas._schema_dict_of(schema, required=True)}

    @property
    def _schema_stock_picking_details(self):
        return dict(
            self._schema_stock_picking(),
            group_lines_by_location={"type": "boolean"},
            show_oneline_package_content={"type": "boolean"},
            need_confirm_pack_all={"type": "string"},
            need_confirm_lot={"type": "integer", "nullable": True},
        )

    @property
    def _schema_summary(self):
        return dict(
            self._schema_stock_picking(lines_with_packaging=True),
            all_processed={"type": "boolean"},
        )

    @property
    def _schema_confirm_done(self):
        return self._schema_stock_picking(lines_with_packaging=True)

    @property
    def _schema_select_child_location(self):
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    @property
    def _schema_selection_list(self):
        return {
            "pickings": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.picking()},
            }
        }

    @property
    def _schema_select_package(self):
        return {
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "packages": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": self.schemas.package(with_packaging=True),
                },
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    @property
    def _schema_select_delivery_packaging(self):
        return {
            "packaging": self.schemas._schema_list_of(
                self.schemas.delivery_packaging()
            ),
        }

    @property
    def _schema_select_packaging(self):
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "package": {
                "type": "dict",
                "schema": self.schemas.package(with_packaging=True),
            },
            "packaging": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.packaging()},
            },
        }

    @property
    def _schema_selected_lines(self):
        return {
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    def scan_document(self):
        return self._response_schema(
            next_states={"select_document", "select_line", "summary"}
        )

    def list_stock_picking(self):
        return self._response_schema(next_states={"manual_selection"})

    def select(self):
        return self._response_schema(
            next_states={"manual_selection", "summary", "select_line"}
        )

    def scan_line(self):
        return self._response_schema(
            next_states={"select_line", "select_package", "summary"}
        )

    def select_line(self):
        return self.scan_line()

    def reset_line_qty(self):
        return self._response_schema(next_states={"select_package"})

    def set_line_qty(self):
        return self._response_schema(next_states={"select_package"})

    def set_custom_qty(self):
        return self._response_schema(next_states={"select_package"})

    def scan_package_action(self):
        return self._response_schema(
            next_states={"select_package", "select_line", "summary"}
        )

    def list_delivery_packaging(self):
        return self._response_schema(
            next_states={"select_delivery_packaging", "select_package"}
        )

    def new_package(self):
        return self._response_schema(next_states={"select_line", "summary"})

    def no_package(self):
        return self.new_package()

    def list_dest_package(self):
        return self._response_schema(
            next_states={"select_dest_package", "select_package"}
        )

    def scan_dest_package(self):
        return self._response_schema(
            next_states={
                "select_dest_package",
                "select_package",
                "select_line",
                "summary",
            }
        )

    def set_dest_package(self):
        return self._response_schema(
            next_states={
                "select_dest_package",
                "select_package",
                "select_line",
                "summary",
            }
        )

    def summary(self):
        return self._response_schema(next_states={"summary"})

    def list_packaging(self):
        return self._response_schema(next_states={"change_packaging", "summary"})

    def set_packaging(self):
        return self._response_schema(next_states={"change_packaging", "summary"})

    def cancel_line(self):
        return self._response_schema(next_states={"summary", "select_line"})

    def done(self):
        return self._response_schema(
            next_states={"summary", "confirm_done", "select_child_location"}
        )

    def scan_dest_location(self):
        return self._response_schema(
            next_states={"confirm_done", "select_document", "select_child_location"}
        )
