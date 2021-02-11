# -*- coding: utf-8 -*-
# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from psycopg2 import OperationalError

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):

    _inherit = "stock.quant"

    @api.constrains("package_id", "location_id", "lot_id", "product_id")
    def _check_storage_type(self):
        """
        Check if at least one location storage type allows the package storage
        type into the quant's location
        """
        for quant in self:
            location = quant.location_id
            pack_storage_type = quant.package_id.package_storage_type_id
            loc_storage_types = location.allowed_location_storage_type_ids
            if not quant.package_id or not pack_storage_type or not loc_storage_types:
                continue
            lst_allowed_for_pst = loc_storage_types.filtered(
                lambda lst: pack_storage_type in lst.package_storage_type_ids
            )
            if not lst_allowed_for_pst:
                raise ValidationError(
                    _("Package storage type %s is not allowed into " "Location %s")
                    % (pack_storage_type.name, location.name)
                )
            allowed = False
            package_weight = quant.package_id.pack_weight
            package_quants = quant.package_id.mapped("quant_ids")
            package_products = package_quants.mapped("product_id")
            package_lots = package_quants.mapped("lot_id")
            other_quants_in_location = self.search(
                [
                    ("location_id", "=", location.id),
                    ("id", "not in", package_quants.ids),
                    ("qty", ">", 0),
                ]
            )
            products_in_location = other_quants_in_location.mapped("product_id")
            lots_in_location = other_quants_in_location.mapped("lot_id")
            lst_fails = []
            for loc_storage_type in lst_allowed_for_pst:
                # Check content constraints
                if loc_storage_type.only_empty and other_quants_in_location:
                    lst_fails.append(
                        _(
                            "Location storage type %s is flagged 'only empty'"
                            " with other quants in location." % loc_storage_type.name
                        )
                    )
                    continue
                if loc_storage_type.do_not_mix_products and (
                    len(package_products) > 1
                    or len(products_in_location) >= 1
                    and package_products != products_in_location
                ):
                    lst_fails.append(
                        _(
                            "Location storage type %s is flagged 'do not mix"
                            " products' but there are other products in "
                            "location." % loc_storage_type.name
                        )
                    )
                    continue
                if loc_storage_type.do_not_mix_lots and (
                    len(package_lots) > 1
                    or len(lots_in_location) >= 1
                    and package_lots != lots_in_location
                ):
                    lst_fails.append(
                        _(
                            "Location storage type %s is flagged 'do not mix"
                            " lots' but there are other lots in "
                            "location." % loc_storage_type.name
                        )
                    )
                    continue
                # Check size constraint
                if (
                    loc_storage_type.max_height
                    and quant.package_id.height > loc_storage_type.max_height
                ):
                    lst_fails.append(
                        _(
                            "Location storage type %s defines max height of %s"
                            " but the package is bigger: %s."
                            % (
                                loc_storage_type.name,
                                loc_storage_type.max_height,
                                quant.package_id.height,
                            )
                        )
                    )
                    continue
                if (
                    loc_storage_type.max_weight
                    and package_weight > loc_storage_type.max_weight
                ):
                    lst_fails.append(
                        _(
                            "Location storage type %s defines max weight of %s"
                            " but the package is heavier: %s."
                            % (
                                loc_storage_type.name,
                                loc_storage_type.max_weight,
                                package_weight,
                            )
                        )
                    )
                    continue
                # If we get here, it means there is a location storage type
                #  allowing the package into the location
                allowed = True
                break
            if not allowed:
                raise ValidationError(
                    _(
                        "Package %s is not allowed into location %s, because "
                        "there isn't any location storage type that allows "
                        "package storage type %s into it:\n\n%s"
                    )
                    % (
                        quant.package_id.name,
                        location.complete_name,
                        pack_storage_type.name,
                        "\n".join(lst_fails),
                    )
                )

    def write(self, vals):
        res = super(StockQuant, self).write(vals)
        self._invalidate_package_level_allowed_location_dest_domain()
        return res

    @api.model
    def create(self, vals):
        res = super(StockQuant, self).create(vals)
        self._invalidate_package_level_allowed_location_dest_domain()
        return res

    def _invalidate_package_level_allowed_location_dest_domain(self):
        self.env["stock.pack.operation"].invalidate_cache(
            fnames=["allowed_location_dest_domain"]
        )

    @api.model
    def _get_removal_strategy(self, product_id, location_id):
        if product_id.categ_id.removal_strategy_id:
            return product_id.categ_id.removal_strategy_id.method
        loc = location_id
        while loc:
            if loc.removal_strategy_id:
                return loc.removal_strategy_id.method
            loc = loc.location_id
        return "fifo"

    def _gather(
        self,
        product_id,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=False,
    ):
        from odoo.osv import expression

        removal_strategy = self._get_removal_strategy(product_id, location_id)
        removal_strategy_order = self._quants_removal_get_order(removal_strategy)
        domain = [
            ("product_id", "=", product_id.id),
        ]
        if not strict:
            if lot_id:
                domain = expression.AND([[("lot_id", "=", lot_id.id)], domain])
            if package_id:
                domain = expression.AND([[("package_id", "=", package_id.id)], domain])
            if owner_id:
                domain = expression.AND([[("owner_id", "=", owner_id.id)], domain])
            domain = expression.AND(
                [[("location_id", "child_of", location_id.id)], domain]
            )
        else:
            domain = expression.AND(
                [[("lot_id", "=", lot_id and lot_id.id or False)], domain]
            )
            domain = expression.AND(
                [[("package_id", "=", package_id and package_id.id or False)], domain]
            )
            domain = expression.AND(
                [[("owner_id", "=", owner_id and owner_id.id or False)], domain]
            )
            domain = expression.AND([[("location_id", "=", location_id.id)], domain])

        # Copy code of _search for special NULLS FIRST/LAST order
        self.check_access_rights("read")
        query = self._where_calc(domain)
        self._apply_ir_rules(query, "read")
        from_clause, where_clause, where_clause_params = query.get_sql()
        where_str = where_clause and (" WHERE %s" % where_clause) or ""
        query_str = (
            'SELECT "%s".id FROM ' % self._table
            + from_clause
            + where_str
            + " ORDER BY "
            + removal_strategy_order
        )
        # pylint: disable=sql-injection
        self._cr.execute(query_str, where_clause_params)
        res = self._cr.fetchall()
        # No uniquify list necessary as auto_join is not applied anyways...
        return self.browse([x[0] for x in res])

    @api.model
    def _update_available_quantity(
        self,
        product_id,
        location_id,
        quantity,
        lot_id=None,
        package_id=None,
        owner_id=None,
        in_date=None,
    ):
        """ Increase or decrease `reserved_quantity` of a set of quants for a given set of
        product_id/location_id/lot_id/package_id/owner_id.

        :param product_id:
        :param location_id:
        :param quantity:
        :param lot_id:
        :param package_id:
        :param owner_id:
        :param datetime in_date: Should only be passed when calls to this method are done in
                                 order to move a quant. When creating a tracked quant, the
                                 current datetime will be used.
        :return: tuple (available_quantity, in_date as a datetime)
        """
        self = self.sudo()
        quants = self._gather(
            product_id,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=True,
        )

        incoming_dates = [d for d in quants.mapped("in_date") if d]
        incoming_dates = [
            fields.Datetime.from_string(incoming_date)
            for incoming_date in incoming_dates
        ]
        if in_date:
            incoming_dates += [in_date]
        # If multiple incoming dates are available for a given lot_id/package_id/owner_id, we
        # consider only the oldest one as being relevant.
        if incoming_dates:
            in_date = fields.Datetime.to_string(min(incoming_dates))
        else:
            in_date = fields.Datetime.now()

        for quant in quants:
            try:
                with self._cr.savepoint():
                    self._cr.execute(
                        "SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT",
                        [quant.id],
                        log_exceptions=False,
                    )
                    quant.write({"qty": quant.quantity + quantity, "in_date": in_date})
                    break
            except OperationalError as e:
                if e.pgcode == "55P03":  # could not obtain the lock
                    continue
                else:
                    raise
        else:
            self.create(
                {
                    "product_id": product_id.id,
                    "location_id": location_id.id,
                    "qty": quantity,
                    "lot_id": lot_id and lot_id.id,
                    "package_id": package_id and package_id.id,
                    "owner_id": owner_id and owner_id.id,
                    "in_date": in_date,
                }
            )
