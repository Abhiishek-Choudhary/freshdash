from rest_framework.permissions import BasePermission

from apps.accounts.models import UserRole


class IsRole(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )


class IsCustomer(IsRole):
    allowed_roles = (UserRole.USER,)


class IsVendor(IsRole):
    allowed_roles = (UserRole.VENDOR,)


class IsStaffMember(IsRole):
    allowed_roles = (UserRole.STAFF,)


class IsVendorOrStaff(IsRole):
    allowed_roles = (UserRole.VENDOR, UserRole.STAFF)


class IsDeliveryPartner(IsRole):
    allowed_roles = (UserRole.DELIVERY_PARTNER,)


class IsAdminRole(IsRole):
    allowed_roles = (UserRole.ADMIN,)


class IsAdminOrVendor(IsRole):
    allowed_roles = (UserRole.ADMIN, UserRole.VENDOR)
