# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

# The field shopfloor_packing_info on res.partner contained a text
# that, although not necessarily equal for all the customers, it is
# expected that many of them share similar, or equal, messages. For
# this, a new model was declared having as purpose storing these
# different messages, so that customers can select the one that best
# suits them, or create a new one that can be reused for another
# customer.
#     This model was extracted from the original module 'shopfloor'
# and placed in this new module, 'shopfloor_packing_info'. The idea
# is to copy the contents of the existing column to the new model,
# and link the new record to the customer having as content the one
# used to create the new record. The following hooks deal with this
# process:
#     1. pre-init will copy, in a temporary column, the contents
#        of the column that is going to be removed when the update
#        on 'shopfloor' is done.
#     2. post-init will get the values from that temporary column,
#        (because the update would have removed the original column)
#        and use them to populate the new records for the new model,
#        and link them to the corresponding customers. The temporal
#        column will be removed afterwards.

import os

from odoo.api import SUPERUSER_ID, Environment
from odoo.tools.sql import column_exists


def pre_init_hook(cr):
    if column_exists(cr, "res_partner", "shopfloor_packing_info"):
        cr.execute(
            """
            ALTER TABLE res_partner
            ADD COLUMN shopfloor_packing_info_tmp TEXT;

            UPDATE res_partner
            SET shopfloor_packing_info_tmp=shopfloor_packing_info;"""
        )


def post_init_hook(cr, registry):
    if column_exists(cr, "res_partner", "shopfloor_packing_info_tmp"):
        copy_into_new_model(cr)
        cr.execute(
            """
            ALTER TABLE res_partner
            DROP COLUMN shopfloor_packing_info_tmp;"""
        )


def copy_into_new_model(cr):
    env = Environment(cr, SUPERUSER_ID, {})
    shopfloor_packing_info = env["shopfloor.packing.info"]
    res_partner = env["res.partner"]

    env.cr.execute(
        """
        SELECT id, COALESCE(shopfloor_packing_info_tmp, '') AS packing_info_old
        FROM res_partner
        WHERE active = TRUE;
        """
    )

    for row in env.cr.dictfetchall():
        partner_id = int(row["id"])
        packing_info_full = row["packing_info_old"].strip()
        if packing_info_full:
            partner = res_partner.browse(partner_id)

            # We assume the name is the first line, if there are several.
            linesep_pos = packing_info_full.find(os.linesep)
            if linesep_pos == -1:
                packing_info_name = packing_info_full
            else:
                packing_info_name = packing_info_full[:linesep_pos]

            # If a record already exists, assign it; otherwise: create and assign.
            packing_info_record = shopfloor_packing_info.search(
                [("name", "=", packing_info_name), ("text", "=", packing_info_full)],
                limit=1,
            )
            if packing_info_record:
                partner.shopfloor_packing_info_id = packing_info_record
            else:
                packing_info_record = shopfloor_packing_info.create(
                    {"name": packing_info_name, "text": packing_info_full}
                )
                partner.shopfloor_packing_info_id = packing_info_record
