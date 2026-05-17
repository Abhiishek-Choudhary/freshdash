from apps.accounts.models import UserRole


def get_user_store(user):
    """Return Store for vendor or staff user."""
    from apps.stores.models import Store, StoreStaff

    if user.role == UserRole.VENDOR and hasattr(user, "vendor_profile"):
        return Store.objects.filter(owner=user.vendor_profile).first()
    if user.role == UserRole.STAFF:
        staff = StoreStaff.objects.filter(user=user, is_active=True).select_related("store").first()
        return staff.store if staff else None
    return None
