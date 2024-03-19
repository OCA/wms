# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from openupgradelib import openupgrade


def move_fields_to_new_module(cr):
    # is_shopfloor_created has been wrongly put in shopfloor_reception.
    # this script moves it in shopfloor.
    openupgrade.update_module_moved_fields(
        cr, "stock.picking", "is_shopfloor_created", "shopfloor_reception", "shopfloor"
    )


def migrate(cr, version):
    move_fields_to_new_module(cr)
