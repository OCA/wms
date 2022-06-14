# Copyright 2022 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _
from odoo.exceptions import UserError


class ShopfloorDispatchError(UserError):
    def __init__(self, payload):
        payload["no_wrap"] = True
        self.rest_json_info = payload
        super().__init__(payload["message"]["body"])


class ShopfloorError(Exception):
    """Base Error for shopfloor apps"""

    def __init__(
        self, message, base_response=None, data=None, next_state=None, popup=None
    ):
        self.base_response = base_response
        self.data = data
        self.next_state = next_state
        self.popup = popup
        super().__init__(message)


class NoPackInLocation(ShopfloorError):
    def __init__(
        self, location, base_response=None, data=None, next_state=None, popup=None
    ):
        super().__init__(
            _("Location %s doesn't contain any package.") % location.name,
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class SeveralPacksInLocation(ShopfloorError):
    def __init__(
        self, location, base_response=None, data=None, next_state=None, popup=None
    ):
        super().__init__(
            _("Several packages found in %s, please scan a package.") % location.name,
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class PackageNotFoundForBarcode(ShopfloorError):
    def __init__(
        self, barcode, base_response=None, data=None, next_state=None, popup=None
    ):
        super().__init__(
            _("The package %s doesn't exist") % barcode,
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class PackageHasNoProductToTake(ShopfloorError):
    def __init__(
        self, barcode, base_response=None, data=None, next_state=None, popup=None
    ):
        super().__init__(
            _("The package %s doesn't contain any product to take.") % barcode,
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class PackageNotAllowedInSrcLocation(ShopfloorError):
    def __init__(
        self,
        barcode,
        picking_types,
        base_response=None,
        data=None,
        next_state=None,
        popup=None,
    ):
        super().__init__(
            _("You cannot work on a package (%s) outside of locations: %s")
            % (
                barcode,
                ", ".join(picking_types.mapped("default_location_src_id.name")),
            ),
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class PackageAlreadyPickedBy(ShopfloorError):
    def __init__(
        self,
        package,
        picking,
        base_response=None,
        data=None,
        next_state=None,
        popup=None,
    ):
        super().__init__(
            _("Package {} cannot be picked, already moved by transfer {}.").format(
                package.name, picking.name
            ),
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class NoPendingOperationForPack(ShopfloorError):
    def __init__(
        self, package, base_response=None, data=None, next_state=None, popup=None
    ):
        super().__init__(
            _("No pending operation for package %s.") % package.name,
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class NoPutawayDestinationAvailable(ShopfloorError):
    def __init__(self, base_response=None, data=None, next_state=None, popup=None):
        super().__init__(
            _("No putaway destination is available."),
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class PackageUnableToTransfer(ShopfloorError):
    def __init__(
        self, package, base_response=None, data=None, next_state=None, popup=None
    ):
        super().__init__(
            _("The package %s cannot be transferred with this scenario.")
            % package.name,
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class OperationNotFound(ShopfloorError):
    def __init__(self, base_response=None, data=None, next_state=None, popup=None):
        super().__init__(
            _("This operation does not exist anymore."),
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class OperationHasBeenCanceledElsewhere(ShopfloorError):
    def __init__(self, base_response=None, data=None, next_state=None, popup=None):
        super().__init__(
            _("Restart the operation, someone has canceled it."),
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class NoLocationFound(ShopfloorError):
    def __init__(self, base_response=None, data=None, next_state=None, popup=None):
        super().__init__(
            _("No location found for this barcode."),
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class DestLocationNotAllowed(ShopfloorError):
    def __init__(self, base_response=None, data=None, next_state=None, popup=None):
        super().__init__(
            _("You cannot place it here"),
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )


class AlreadyDone(ShopfloorError):
    def __init__(self, base_response=None, data=None, next_state=None, popup=None):
        super().__init__(
            _("Operation already processed."),
            base_response=base_response,
            data=data,
            next_state=next_state,
            popup=popup,
        )
