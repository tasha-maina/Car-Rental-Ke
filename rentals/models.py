import uuid

from django.conf import settings
from django.db import models


class Car(models.Model):
    CATEGORIES = [
        ("Economy", "Economy"),
        ("Sedan", "Sedan"),
        ("SUV", "SUV"),
        ("Van", "Van / Group"),
        ("4x4", "4x4 / Safari"),
        ("Luxury", "Luxury"),
    ]
    name = models.CharField(max_length=80)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    seats = models.PositiveSmallIntegerField(default=5)
    transmission = models.CharField(max_length=10, default="Auto")
    fuel = models.CharField(max_length=10, default="Petrol")
    daily_rate = models.PositiveIntegerField(help_text="Self-drive rate per day (KES)")
    units = models.PositiveSmallIntegerField(default=1, help_text="How many of this car you own")
    driver_only = models.BooleanField(default=False, help_text="Chauffeur-driven only")
    emoji = models.CharField(max_length=4, default="🚗", help_text="Fallback if no photo")
    photo = models.FileField(upload_to="cars/", blank=True, help_text="Upload a real photo of your car")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["daily_rate"]

    def __str__(self):
        return self.name

    def booked_units(self, start, end):
        return self.bookings.filter(
            status__in=Booking.ACTIVE_STATUSES, start_date__lt=end, end_date__gt=start
        ).count()

    def units_left(self, start, end):
        return self.units - self.booked_units(start, end)

    def quote(self, start, end, with_driver=False):
        days = (end - start).days
        with_driver = with_driver or self.driver_only
        discount = 20 if days >= 28 else 10 if days >= 7 else 0
        per_day = round(self.daily_rate * (100 - discount) / 100) + (
            settings.DRIVER_FEE if with_driver else 0)
        total = per_day * days
        return {
            "days": days, "with_driver": with_driver, "discount": discount,
            "per_day": per_day, "total": total,
            "deposit": -(-total * settings.DEPOSIT_PERCENT // 100),
        }


class Booking(models.Model):
    PENDING = "pending"        # waiting for M-Pesa code
    VERIFYING = "verifying"    # client submitted a code, owner must check SMS
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    STATUSES = [(PENDING, "Awaiting payment"), (VERIFYING, "Payment to verify"),
                (CONFIRMED, "Confirmed"), (CANCELLED, "Cancelled")]
    ACTIVE_STATUSES = [PENDING, VERIFYING, CONFIRMED]

    ref = models.CharField(max_length=10, unique=True, editable=False)
    car = models.ForeignKey(Car, on_delete=models.PROTECT, related_name="bookings")
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    with_driver = models.BooleanField(default=False)
    total = models.PositiveIntegerField()
    deposit = models.PositiveIntegerField()
    mpesa_code = models.CharField(max_length=12, blank=True)
    checkout_request_id = models.CharField(max_length=60, blank=True, db_index=True)
    status = models.CharField(max_length=12, choices=STATUSES, default=PENDING)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = "CR" + uuid.uuid4().hex[:6].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ref} – {self.car} – {self.customer_name}"

    @property
    def days(self):
        return (self.end_date - self.start_date).days
