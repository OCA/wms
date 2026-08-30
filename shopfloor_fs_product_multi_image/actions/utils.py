# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def _replace_image_fields(parser_res, image_url_provider):
    # If fs_product_multi_image is installed, we should use "image" and "image_medium"
    # fieds and not base "image_x" fields
    res = [
        item
        for item in parser_res
        if not (
            # If it's a tuple/list, check the first element
            (
                isinstance(item, (tuple, list))
                and item
                and isinstance(item[0], str)
                and (item[0].endswith("image") or ":image" in item[0])
            )
            # If it's just a raw string, check the string itself
            or (isinstance(item, str) and (item.startswith("image")))
        )
    ]

    res.append(("image_medium:image", image_url_provider))
    return res
