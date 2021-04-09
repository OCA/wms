# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import hashlib
import logging
import struct

from odoo import fields, tools

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class PickingBatchAutoCreateAction(Component):
    """Automatic creation of picking batches"""

    _name = "shopfloor.picking.batch.auto.create"
    _inherit = "shopfloor.process.action"
    _usage = "picking.batch.auto.create"

    _advisory_lock_name = "shopfloor_batch_picking_create"

    def create_batch(
        self,
        picking_types,
        max_pickings=0,
        max_weight=0,
        max_volume=0,
        group_by_commercial_partner=False,
    ):
        self._lock()
        search_user = self.env.user
        pickings = self._search_pickings(picking_types, user=search_user)
        if not pickings:
            search_user = None
            pickings = self._search_pickings(picking_types)
        pickings = self._sort(pickings)
        if group_by_commercial_partner:
            # From the first operation we got, get all operations having the
            # same commercial entity
            picking = fields.first(pickings)
            commercial_partner = picking.partner_id.commercial_partner_id
            pickings = self._search_pickings(
                picking_types, user=search_user, commercial_partner=commercial_partner
            )
        else:
            # Otherwise process by priorities by applying the limits
            pickings = self._apply_limits(
                pickings, max_pickings, max_weight, max_volume
            )
        if not pickings:
            return self.env["stock.picking.batch"].browse()
        return self._create_batch(pickings)

    def _lock(self):
        """Lock to prevent concurrent creation of batch

        Use a blocking advisory lock to prevent 2 transactions to create
        a batch at the same time. The lock is released at the commit or
        rollback of the transaction.

        The creation of a new batch should be short enough not to block
        the users for too long.
        """
        _logger.info(
            "trying to acquire lock to create a picking batch (%s)", self.env.user.login
        )
        hasher = hashlib.sha1(str(self._advisory_lock_name).encode())
        # pg_lock accepts an int8 so we build an hash composed with
        # contextual information and we throw away some bits
        int_lock = struct.unpack("q", hasher.digest()[:8])

        self.env.cr.execute("SELECT pg_advisory_xact_lock(%s);", (int_lock,))
        self.env.cr.fetchone()[0]
        # Note: if the lock had to wait, the snapshot of the transaction is
        # very much probably outdated already (i.e. if the transaction which
        # had the lock before this one set a 'batch_id' on stock.picking this
        # transaction will not be aware of), we'll probably have a retry. But
        # the lock can help limit the number of retries.
        _logger.info(
            "lock acquired to create a picking batch (%s)", self.env.user.login
        )

    def _search_pickings_domain(
        self, picking_types, user=None, commercial_partner=None
    ):
        domain = [
            ("picking_type_id", "in", picking_types.ids),
            ("state", "in", ("assigned", "partially_available")),
            ("batch_id", "=", False),
            ("user_id", "=", user.id if user else False),
        ]
        if commercial_partner:
            domain.append(
                ("partner_id.commercial_partner_id", "=", commercial_partner.id)
            )
        return domain

    def _search_pickings(self, picking_types, user=None, commercial_partner=None):
        # We can't use a limit in the SQL search because the 'priority' fields
        # is sometimes empty (it seems the inverse StockPicking.priority field
        # mess up with default on stock.move), we have to sort in Python.
        return self.env["stock.picking"].search(
            self._search_pickings_domain(
                picking_types, user=user, commercial_partner=commercial_partner
            )
        )

    def _sort(self, pickings):
        return pickings.sorted(
            lambda picking: (
                -(int(picking.priority) if picking.priority else 1),
                picking.scheduled_date,
                picking.id,
            )
        )

    def _precision_weight(self):
        return self.env["decimal.precision"].precision_get("Product Unit of Measure")

    def _precision_volume(self):
        return max(
            6,
            self.env["decimal.precision"].precision_get("Product Unit of Measure") * 2,
        )

    def _apply_limits(self, pickings, max_pickings, max_weight, max_volume):
        first_picking = fields.first(pickings)
        current_priority = first_picking.priority or "1"
        # Always take the first picking even if it doesn't fullfill the
        # weight/volume criteria. This allows to always process at least
        # one picking which won't be processed otherwise
        selected_pickings = first_picking

        precision_weight = self._precision_weight()
        precision_volume = self._precision_volume()

        def gt(value1, value2, digits):
            """Return True if value1 is greater than value2"""
            return tools.float_compare(value1, value2, precision_digits=digits) == 1

        total_weight = self._picking_weight(first_picking)
        total_volume = self._picking_volume(first_picking)
        for picking in pickings[1:]:
            if max_pickings and len(selected_pickings) == max_pickings:
                # selected enough!
                break
            if (picking.priority or "1") != current_priority:
                # as we sort by priority, exit as soon as the priority changes,
                # we do not mix priorities to make delivery of high priority
                # transfers faster
                break

            weight = self._picking_weight(picking)
            volume = self._picking_volume(picking)
            if max_weight and gt(total_weight + weight, max_weight, precision_weight):
                continue

            if max_volume and gt(total_volume + volume, max_volume, precision_volume):
                continue

            selected_pickings |= picking
            total_weight += weight
            total_volume += volume

        return selected_pickings

    def _picking_weight(self, picking):
        weight = 0.0
        for line in picking.move_lines:
            weight += line.product_id.get_total_weight_from_packaging(
                line.product_uom_qty
            )
        return weight

    def _picking_volume(self, picking):
        volume = 0.0
        for line in picking.move_lines:
            product = line.product_id
            packagings_with_volume = product.with_context(
                _packaging_filter=lambda p: p.volume
            ).product_qty_by_packaging(line.product_uom_qty)
            for packaging_info in packagings_with_volume:
                if packaging_info.get("is_unit"):
                    pack_volume = product.volume
                else:
                    packaging = self.env["product.packaging"].browse(
                        packaging_info["id"]
                    )
                    pack_volume = packaging.volume

                volume += pack_volume * packaging_info["qty"]
        return volume

    def _create_batch(self, pickings):
        return self.env["stock.picking.batch"].create(
            self._create_batch_values(pickings)
        )

    def _create_batch_values(self, pickings):
        return {"picking_ids": [(6, 0, pickings.ids)]}
