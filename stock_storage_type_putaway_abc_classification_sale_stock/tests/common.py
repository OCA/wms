# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from psycopg2.extensions import AsIs

from odoo.addons.product_abc_classification.tests import common
from odoo.addons.stock_storage_type.tests.common import TestStorageTypeCommon


class ABCClassificationLevelCase(
    TestStorageTypeCommon, common.ABCClassificationLevelCase
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "type": "product",
                "weight": 10.0,
            }
        )
        # force profile using SQL to avoid trouble if tests are ran with
        # alc_product_abc_classification_picking_zone installed

        cls._link_profile(cls.product, cls.classification_profile)

    @classmethod
    def _link_profile(cls, products, profile):
        product_profiles_field = cls.env["product.product"]._fields[
            "abc_classification_profile_ids"
        ]
        product_profiles_product_col = product_profiles_field.column1
        product_profiles_profile_col = product_profiles_field.column2
        product_profiles_table = product_profiles_field.relation

        template_profiles_field = cls.env["product.template"]._fields[
            "abc_classification_profile_ids"
        ]
        template_profiles_product_col = template_profiles_field.column1
        template_profiles_profile_col = template_profiles_field.column2
        template_profiles_table = template_profiles_field.relation

        for product in products:
            cls.env.cr.execute(
                """
                INSERT into %(table)s (%(product_col)s, %(profile_col)s)
                VALUES (%(product_id)s, %(profile_id)s)
                ;
            """,
                {
                    "table": AsIs(product_profiles_table),
                    "product_col": AsIs(product_profiles_product_col),
                    "profile_col": AsIs(product_profiles_profile_col),
                    "product_id": product.id,
                    "profile_id": profile.id,
                },
            )
            cls.env.cr.execute(
                """
                INSERT into %(table)s (%(product_col)s, %(profile_col)s)
                VALUES (%(template_id)s, %(profile_id)s)
            """,
                {
                    "table": AsIs(template_profiles_table),
                    "product_col": AsIs(template_profiles_product_col),
                    "profile_col": AsIs(template_profiles_profile_col),
                    "template_id": product.product_tmpl_id.id,
                    "profile_id": profile.id,
                },
            )

    @classmethod
    def _set_abc_level(cls, product, level):
        product.abc_classification_product_level_ids.filtered(
            lambda a, lvl=level: a.profile_id == lvl.profile_id
        ).unlink()
        product.abc_classification_product_level_ids.create(
            {
                "product_id": product.id,
                "computed_level_id": level.id,
                "profile_id": level.profile_id.id,
            }
        )
