# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import math

from odoo import api, fields, models, tools

from ..exceptions import NoPickingCandidateError, NoSuitableDeviceError


class MakePickingBatch(models.TransientModel):

    _name = "make.picking.batch"

    picking_type_ids = fields.Many2many(
        comodel_name="stock.picking.type",
        relation="make_picking_batch_picking_type_rel",
        column1="batch_id",
        column2="picking_type_id",
        string="Default operation types",
        help="Default list of eligible operation types when creating a batch transfer",
    )
    stock_device_type_ids = fields.Many2many(
        comodel_name="stock.device.type",
        relation="make_picking_batch_device_type_rel",
        column1="batch_id",
        column2="device_type_id",
        string="Default device types",
        help="Default list of eligible device types when creating a batch transfer",
    )
    user_id = fields.Many2one("res.users", string="Responsible")
    maximum_number_of_preparation_lines = fields.Integer(
        default=20,
        string="Maximum number of preparation lines for the batch",
        required=True,
    )

    @api.multi
    def create_batch(self):
        self.ensure_one()
        batch = self._create_batch(raise_if_not_possible=True)
        action = {
            "type": "ir.actions.act_window",
            "name": batch.name,
            "res_model": "stock.picking.wave",
            "res_id": batch.id,
            "view_mode": "form",
            "target": "current",
        }
        return action

    def _search_pickings(self, user=None):
        domain = self._search_pickings_domain(user=user)
        pickings = self.env["stock.picking"].search(domain)
        return pickings

    def _search_pickings_domain(self, user=None):
        domain = [
            ("picking_type_id", "in", self.picking_type_ids.ids),
            ("state", "in", ("partially_available", "assigned")),
            ("wave_id", "=", False),
            ("user_id", "=", user.id if user else False),
        ]
        if not user:
            domain.append(("printed", "=", False))
        return domain

    def _candidates_pickings_to_batch(self, user=None):
        candidates_pickings = self._search_pickings(user=user)
        if not candidates_pickings:
            candidates_pickings = self._search_pickings()
        return candidates_pickings

    def _compute_device_to_use(self, picking):
        recommended_device = None
        available_devices = self.stock_device_type_ids.sorted(lambda d: d.sequence)
        picking_volume = self._picking_volume(picking)
        for device in available_devices:
            if self._volume_condition_for_device_choice(
                device.min_volume, picking_volume, device.max_volume
            ):
                recommended_device = device
                break
        return recommended_device

    def _volume_condition_for_device_choice(
        self, min_volume, picking_volume, max_volume
    ):
        lower_bound = tools.float_compare(picking_volume, min_volume, 2) >= 0
        upper_bound = tools.float_compare(max_volume, picking_volume, 2) >= 0
        return lower_bound and upper_bound

    def _picking_nbr_lines(self, picking):
        return len(picking.pack_operation_ids)

    def _get_first_suitable_device_and_picks(self, pickings):
        """Get the first suitable device and the list of pickings where all the
        pickings before the first one providing a suitable device are removed
        """
        excluded_ids = set()
        for pick in pickings:
            device = self._compute_device_to_use(pick)
            if device:
                return (
                    device,
                    self.env["stock.picking"].browse(
                        [p.id for p in pickings if p.id not in excluded_ids]
                    ),
                )
        else:
            excluded_ids.add(pick.id)
        return (
            self.env["stock.device.type"].browse(),
            self.env["stock.picking"].browse(),
        )

    def _create_batch(self, raise_if_not_possible=False):
        user = self.user_id if self.user_id else self.env.user
        device = None
        candidates_pickings_to_batch = self._candidates_pickings_to_batch(user=user)
        if not candidates_pickings_to_batch:
            if raise_if_not_possible:
                raise NoPickingCandidateError()
            return self.env["stock.picking.wave"].browse()

        (
            device,
            candidates_pickings_to_batch,
        ) = self._get_first_suitable_device_and_picks(candidates_pickings_to_batch)

        if not device:
            if raise_if_not_possible:
                raise NoSuitableDeviceError()
            return self.env["stock.picking.wave"].browse()

        selected_pickings, unselected_pickings = self._apply_limits(
            candidates_pickings_to_batch, device
        )
        vals = self._create_batch_values(user, device, selected_pickings)
        batch = self.env["stock.picking.wave"].create(vals)
        self._assign_operator_on_selected_pickings(batch, user)
        return batch

    def _assign_operator_on_selected_pickings(self, batch, user):
        batch.picking_ids.write({"user_id": user.id})

    def _precision_weight(self):
        return self.env["decimal.precision"].precision_get("Product Unit of Measure")

    def _precision_volume(self):
        return max(
            6,
            self.env["decimal.precision"].precision_get("Product Unit of Measure") * 2,
        )

    def _apply_limits(self, pickings, device, max_pickings=0):
        """
        Once we have the candidates pickings for clustering, we need to decide when to stop
        the cluster (i.e.,  when to stop adding pickings in it)
        We add pickings in the cluster as long as the conditions are respected
        """
        selected_picking_ids = []
        total_weight = 0.0
        total_volume = 0.0
        total_nbr_picking_lines = 0
        precision_weight = self._precision_weight()
        precision_volume = self._precision_volume()

        def gt(value1, value2, digits):
            """Return True if value1 is greater than value2"""
            return tools.float_compare(value1, value2, precision_digits=digits) == 1

        # # Add pickings to the first one as long as
        # # - total volume is not outreached
        # # - total weight is not outreached
        # # - maximum number of preparation lines is not outreached
        # # - numbers of bins available is greater than 0
        # # - The device for the current picking is supposed to be
        available_nbr_bins = device.nbr_bins
        volume_per_bin = device.max_volume / device.nbr_bins
        for picking in pickings:
            if available_nbr_bins == 0:
                break

            if max_pickings and len(selected_picking_ids) == max_pickings:
                # selected enough!
                break

            # Check that the picking can go on the selected device
            picking_device = self._compute_device_to_use(picking)
            if device != picking_device:
                continue

            picking.total_weight_batch_picking = self._picking_weight(picking)
            picking.total_volume_batch_picking = self._picking_volume(picking)
            picking.nbr_picking_lines = self._picking_nbr_lines(picking)
            picking.nbr_bins_batch_picking = math.ceil(
                picking.total_volume_batch_picking / volume_per_bin
            )

            available_bins_outreached = (
                available_nbr_bins - picking.nbr_bins_batch_picking < 0
            )
            if available_bins_outreached:
                continue

            weight_limit_outreached = device.max_weight and gt(
                total_weight + picking.total_weight_batch_picking,
                device.max_weight,
                precision_weight,
            )
            if weight_limit_outreached:
                continue

            volume_limit_outreached = device.max_volume and gt(
                total_volume + picking.total_volume_batch_picking,
                device.max_volume,
                precision_volume,
            )
            if volume_limit_outreached:
                continue

            nbr_lines_limit_outreached = (
                self.maximum_number_of_preparation_lines
                and gt(
                    total_nbr_picking_lines + picking.nbr_picking_lines,
                    self.maximum_number_of_preparation_lines,
                    1,
                )
            )
            if nbr_lines_limit_outreached:
                continue

            # All conditions are OK : we keep the picking in the cluster
            selected_picking_ids.append(picking.id)
            total_weight += picking.total_weight_batch_picking
            total_volume += picking.total_volume_batch_picking
            total_nbr_picking_lines += picking.nbr_picking_lines
            available_nbr_bins -= picking.nbr_bins_batch_picking

        selected_pickings = self.env["stock.picking"].browse(selected_picking_ids)
        unselected_pickings = pickings - selected_pickings
        return selected_pickings, unselected_pickings

    def _picking_weight(self, picking):
        weight = 0.0
        for line in picking.move_lines:
            weight += line.product_id.get_total_weight_from_packaging(
                line.product_uom_qty
            )
        return weight

    def _picking_volume(self, picking):
        volume = 0.0
        with self.env["product.product"].product_qty_by_packaging_arg_ctx(
            packaging_filter=lambda p: p.volume
        ):
            for line in picking.move_lines:
                product = line.product_id
                packagings_with_volume = product.product_qty_by_packaging(
                    line.product_uom_qty
                )
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

    def _create_batch_values(self, user, device, pickings):
        return {
            "picking_ids": [(6, 0, pickings.ids)],
            "user_id": user.id,
            "state": "draft",
            "wave_weight": sum(
                [picking.total_weight_batch_picking for picking in pickings]
            ),
            "wave_volume": sum(
                [picking.total_volume_batch_picking for picking in pickings]
            ),
            "wave_nbr_bins": sum(
                [picking.nbr_bins_batch_picking for picking in pickings]
            ),
            "wave_nbr_lines": sum([picking.nbr_picking_lines for picking in pickings]),
            "picking_device_id": device.id if device else None,
        }
