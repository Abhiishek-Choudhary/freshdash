from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import DeliveryPartnerProfile, User, UserRole, VendorProfile
from apps.catalog.models import Product, ProductBadge
from apps.orders.models import Coupon, DeliverySlotConfig
from apps.stores.models import Store


class Command(BaseCommand):
    help = "Seed FreshDash demo data"

    def handle(self, *args, **options):
        customer, _ = User.objects.get_or_create(
            phone="+919876543210",
            defaults={"name": "Demo Customer", "email": "customer@freshdash.demo", "role": UserRole.USER},
        )
        if not customer.has_usable_password():
            customer.set_password("password123")
            customer.save()

        vendor_user, _ = User.objects.get_or_create(
            phone="+919876543211",
            defaults={"name": "Green Valley", "email": "vendor@freshdash.demo", "role": UserRole.VENDOR},
        )
        if not vendor_user.has_usable_password():
            vendor_user.set_password("password123")
            vendor_user.save()
        vendor_profile, _ = VendorProfile.objects.get_or_create(
            user=vendor_user, defaults={"business_name": "Green Valley Market"}
        )

        store, _ = Store.objects.get_or_create(
            owner=vendor_profile,
            defaults={
                "name": "Green Valley Market",
                "latitude": Decimal("28.6139"),
                "longitude": Decimal("77.2090"),
                "delivery_time_min": 15,
                "delivery_time_max": 25,
                "delivery_fee": Decimal("29"),
                "rating": Decimal("4.7"),
                "review_count": 1284,
                "is_open": True,
            },
        )
        if store.name != "Green Valley Market":
            store.name = "Green Valley Market"
            store.save()

        delivery_user, _ = User.objects.get_or_create(
            phone="+919876543212",
            defaults={"name": "Marcus Chen", "email": "driver@freshdash.demo", "role": UserRole.DELIVERY_PARTNER},
        )
        if not delivery_user.has_usable_password():
            delivery_user.set_password("password123")
            delivery_user.save()
        DeliveryPartnerProfile.objects.get_or_create(user=delivery_user, defaults={"is_online": True})

        products_data = [
            ("e1", "Organic Bananas", "Fruits", "89", "1 kg", 50, ProductBadge.ORGANIC),
            ("e2", "Farm Fresh Milk", "Dairy & Eggs", "65", "1 L", 80, None),
            ("e3", "Whole Wheat Bread", "Bakery", "45", "400 g", 30, None),
            ("e4", "Cherry Tomatoes", "Vegetables", "120", "500 g", 25, ProductBadge.SALE),
            ("p1", "Amul Butter", "Dairy & Eggs", "55", "100 g", 60, None),
            ("p2", "Lays Classic", "Snacks", "20", "52 g", 100, None),
        ]
        for sku, name, category, price, unit, stock, badge in products_data:
            Product.objects.update_or_create(
                store=store,
                sku=sku,
                defaults={
                    "name": name,
                    "category": category,
                    "price": Decimal(price),
                    "unit": unit,
                    "stock_count": stock,
                    "low_stock_threshold": 5,
                    "in_stock": True,
                    "badge": badge,
                    "description": f"Fresh {name}",
                    "barcode": f"890{sku}",
                    "nutrition": {
                        "calories": "120",
                        "fiber": "3g",
                        "sugar": "10g",
                        "vitaminC": "15mg",
                    },
                },
            )

        now = timezone.now()
        Coupon.objects.get_or_create(
            code="FRESH50",
            defaults={
                "discount_type": "fixed",
                "value": Decimal("50"),
                "min_order": Decimal("200"),
                "valid_from": now - timedelta(days=1),
                "valid_to": now + timedelta(days=365),
                "is_active": True,
            },
        )

        for slot_id, label, sublabel, express in [
            ("express", "Express", "15 - 20 Mins", True),
            ("slot1", "Morning", "9 AM - 12 PM", False),
            ("slot2", "Afternoon", "12 PM - 4 PM", False),
        ]:
            DeliverySlotConfig.objects.get_or_create(
                id=slot_id,
                defaults={"label": label, "sublabel": sublabel, "is_express": express},
            )

        self.stdout.write(self.style.SUCCESS("Seed data created."))
        self.stdout.write("Customer: +919876543210 / password123")
        self.stdout.write("Vendor: +919876543211 / password123")
        self.stdout.write("Delivery: +919876543212 / password123")
        self.stdout.write("OTP dev code: 123456")
