# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, exceptions

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

    def _check_picking_status(self, pickings):
        """Check if given pickings can be processed.

        If the picking is already done, canceled or didn't belong to the
        expected picking type, a message is returned.
        """
        for picking in pickings:
            if not picking.exists():
                return self.msg_store.stock_picking_not_found()
            if picking.state == "done":
                return self.msg_store.already_done()
            if picking.state != "assigned":  # the picking must be ready
                return self.msg_store.stock_picking_not_available(picking)
            if picking.picking_type_id not in self.picking_types:
                return self.msg_store.cannot_move_something_in_picking_type()
