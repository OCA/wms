# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# Copyright 2020-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, exceptions, fields
from odoo.osv.expression import AND

from odoo.addons.component.core import AbstractComponent


class BaseShopfloorService(AbstractComponent):
    """Base class for REST services"""

    _inherit = "base.shopfloor.service"

    @property
    def search_move_line(self):
        # TODO: propagating `picking_types` should probably be default
        return self._actions_for("search_move_line", propagate_kwargs=["picking_types"])


class BaseShopfloorProcess(AbstractComponent):

    _inherit = "base.shopfloor.process"

    def _get_process_picking_types(self):
        """Return picking types for the menu"""
        return self.work.menu.picking_type_ids

    def _get_pickings_base_domain(self):
        return [
            ("state", "not in", ("done", "cancel")),
            ("location_id", "child_of", self.picking_types.default_location_src_id.ids),
        ]

    def _get_pickings_for_package(self, package, **kwargs):
        domain = self._get_pickings_base_domain()
        package_domain = [("move_line_ids.package_id", "=", package.id)]
        return self.env["stock.picking"].search(AND([domain, package_domain]), **kwargs)

    def _get_pickings_for_product(self, product, **kwargs):
        domain = self._get_pickings_base_domain()
        product_domain = [("move_line_ids.product_id", "=", product.id)]
        return self.env["stock.picking"].search(AND([domain, product_domain]), **kwargs)

    @property
    def picking_types(self):
        if not hasattr(self.work, "picking_types"):
            self.work.picking_types = self._get_process_picking_types()
        if not self.work.picking_types:
            raise exceptions.UserError(
                _("No operation types configured on menu {}.").format(
                    self.work.menu.name
                )
            )
        return self.work.picking_types

    @property
    def search_move_line(self):
        # TODO: picking types should be set somehow straight in the work context
        # by `_validate_headers_update_work_context` in this way
        # we can remove this override and the need to call `_get_process_picking_types`
        # every time.
        return self._actions_for("search_move_line", picking_types=self.picking_types)

    def _check_picking_consistency(self, pickings):
        if not pickings.exists():
            return self.msg_store.stock_picking_not_found()

    def _check_picking_type(self, pickings):
        """Check if the pickings have the right expected type."""
        if not any(
            picking.picking_type_id in self.picking_types for picking in pickings
        ):
            return self.msg_store.reserved_for_other_picking_type(
                fields.first(pickings)
            )

    def _check_picking_status(self, pickings, states=("assigned",)):
        """Checks if the picking exists, is already done or canceled."""
        if not any(picking.state != "done" for picking in pickings):
            return self.msg_store.already_done()
        if not any(picking.state != "cancel" for picking in pickings):
            return self.msg_store.transfer_canceled()
        if not any(
            picking.state in states for picking in pickings
        ):  # the picking must be ready
            return self.msg_store.stock_picking_not_available(fields.first(pickings))

    def _check_picking_processible(self, pickings, states=("assigned",)):
        """Check if given pickings can be processed"""
        message = self._check_picking_consistency(pickings)
        if message:
            return message
        message = self._check_picking_type(pickings)
        if message:
            return message
        message = self._check_picking_status(pickings, states=states)
        if message:
            return message

    def is_src_location_valid(self, location):
        """Check the source location is valid for given process.

        We ensure the source is valid regarding one of the picking types of the
        process.
        """
        return location.is_sublocation_of(self.picking_types.default_location_src_id)

    def is_dest_location_valid(self, moves, location):
        """Check the destination location is valid for given moves.

        We ensure the destination is either valid regarding the picking
        destination location or the move destination location. With the push
        rules in the module stock_dynamic_routing in OCA/wms, it is possible
        that the move destination is not anymore a child of the picking default
        destination (as it is the last pushed move that now respects this
        condition and not anymore this one that has a destination to an
        intermediate location)
        """
        return location.is_sublocation_of(
            moves.picking_id.location_dest_id, func=all
        ) or location.is_sublocation_of(moves.location_dest_id, func=all)

    def is_dest_location_to_confirm(self, location_dest_id, location):
        """Check the destination location requires confirmation

        The location is valid but not the expected one: ask for confirmation
        """
        return not location.is_sublocation_of(location_dest_id)

    def is_allow_move_create(self):
        """Check a new operation can be created

        The menu is configured to allow the creation of moves
        The menu is bind to one picking type
        """
        return self.work.menu.allow_move_create and len(self.picking_types) == 1
