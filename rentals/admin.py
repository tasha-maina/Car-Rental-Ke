from django.contrib import admin, messages
from django.utils import timezone

from .models import Booking, Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "daily_rate", "units", "driver_only", "active")
    list_editable = ("daily_rate", "units", "active")
    list_filter = ("category", "active")


@admin.action(description="CONFIRM selected (I checked the M-Pesa SMS: code, amount and sender match)")
def confirm(modeladmin, request, queryset):
    ok = 0
    for b in queryset:
        if not b.mpesa_code:
            modeladmin.message_user(request, f"{b.ref}: no M-Pesa code submitted, not confirmed.", messages.ERROR)
        elif b.status == Booking.CANCELLED:
            modeladmin.message_user(request, f"{b.ref}: cancelled, not confirmed.", messages.ERROR)
        else:
            b.status = Booking.CONFIRMED
            b.save(update_fields=["status"])
            ok += 1
    if ok:
        modeladmin.message_user(request, f"{ok} booking(s) confirmed. Customers see the thank-you message.")


@admin.action(description="REJECT selected (fake / wrong payment) and free the car")
def reject(modeladmin, request, queryset):
    queryset.exclude(status=Booking.CONFIRMED).update(status=Booking.CANCELLED)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("ref", "status", "car", "customer_name", "phone", "start_date", "end_date",
                    "deposit", "total", "mpesa_code", "created")
    list_filter = ("status", "car")
    search_fields = ("ref", "customer_name", "phone", "mpesa_code")
    readonly_fields = ("ref", "created", "checkout_request_id")
    actions = [confirm, reject]
    ordering = ("status", "-created")
    date_hierarchy = "start_date"
