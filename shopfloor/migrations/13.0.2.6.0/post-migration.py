# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import hashlib
import os

from openupgradelib import openupgrade  # pylint: disable=W7936


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    shopfloor_packing_info = env["shopfloor.packing.info"]
    res_partner = env["res.partner"]
    ir_model_data = env["ir.model.data"]

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
                xml_id = hashlib.md5(packing_info_full.encode("utf-8")).hexdigest()
                ir_model_data._update_xmlids(
                    [
                        {
                            "xml_id": "shopfloor.packing_info_{}".format(xml_id),
                            "record": packing_info_record,
                            "noupdate": True,
                        }
                    ]
                )
    openupgrade.drop_columns(env.cr, [("res_partner", "shopfloor_packing_info_tmp")])
