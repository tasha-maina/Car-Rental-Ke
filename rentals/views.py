import json
import re
from datetime import date, timedelta
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render

from . import mpesa
from .models import Booking, Car


def _parse(value, default):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return default


def _dates(data):
    start = _parse(data.get("start"), date.today())
    end = _parse(data.get("end"), start + timedelta(days=1))
    return start, end


def home(request):
    start, end = _dates(request.GET)
    category = request.GET.get("category", "")
    driver = request.GET.get("driver") == "1"
    valid = end > start and start >= date.today()
    cars = Car.objects.filter(active=True)
    if category:
        cars = cars.filter(category=category)
    rows = []
    for car in cars:
        left = car.units_left(start, end) if valid else 0
        rows.append({"car": car, "left": left, "available": left > 0,
                     "quote": car.quote(start, end, driver) if valid else None})
    return render(request, "rentals/home.html", {
        "rows": rows, "start": start, "end": end, "category": category, "driver": driver,
        "valid": valid, "categories": Car.CATEGORIES, "today": date.today(),
    })


def book(request, car_id):
    car = get_object_or_404(Car, pk=car_id, active=True)
    data = request.GET if request.method == "GET" else request.POST
    start, end = _dates(data)
    driver = data.get("driver") == "1"
    if end <= start or start < date.today():
        messages.error(request, "Please choose valid dates.")
        return redirect("home")
    if car.units_left(start, end) <= 0:
        messages.error(request, f"Sorry, {car.name} is not available for those dates.")
        return redirect("home")
    q = car.quote(start, end, driver)
    if request.method == "POST":
        name = data.get("name", "").strip()
        phone = re.sub(r"[ \-]", "", data.get("phone", ""))
        if not name or not re.fullmatch(r"(\+?254|0)[17]\d{8}", phone):
            messages.error(request, "Enter your name and a valid Kenyan phone number (e.g. 0712345678).")
        else:
            b = Booking.objects.create(
                car=car, customer_name=name, phone=phone, start_date=start, end_date=end,
                with_driver=q["with_driver"], total=q["total"], deposit=q["deposit"])
            return redirect("pay", ref=b.ref)
    return render(request, "rentals/book.html", {
        "car": car, "start": start, "end": end, "driver": driver, "q": q})


def pay(request, ref):
    b = get_object_or_404(Booking, ref=ref)
    if request.method == "POST" and b.status in (Booking.PENDING, Booking.VERIFYING):
        code = request.POST.get("mpesa_code", "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9]{10}", code):
            messages.error(request, "Enter the 10-character M-Pesa code from your confirmation SMS.")
        elif Booking.objects.exclude(pk=b.pk).filter(mpesa_code=code).exists():
            messages.error(request, "That M-Pesa code has already been used.")
        else:
            b.mpesa_code, b.status = code, Booking.VERIFYING
            b.save()
            messages.success(request, "Payment received. We will verify it and confirm shortly.")
            return redirect("pay", ref=b.ref)
    wa = (f"Hello, I booked {b.car} ({b.ref}) {b.start_date} to {b.end_date}. "
          f"M-Pesa code: {b.mpesa_code or 'pending'}. Name: {b.customer_name}")
    return render(request, "rentals/pay.html", {"b": b, "wa_text": quote(wa)})


def contact(request):
    return render(request, "rentals/contact.html")


@require_POST
def stk(request, ref):
    """Send an M-Pesa STK push prompt to the customer's phone."""
    b = get_object_or_404(Booking, ref=ref)
    if not settings.MPESA_STK_ENABLED:
        messages.error(request, "Instant M-Pesa prompt is not set up. Please use Send Money below.")
    elif b.status not in (Booking.PENDING, Booking.VERIFYING):
        messages.error(request, "This booking can no longer be paid.")
    else:
        amount = b.total if request.POST.get("amount") == "full" else b.deposit
        try:
            b.checkout_request_id = mpesa.stk_push(b.phone, amount, b.ref)
            b.save(update_fields=["checkout_request_id"])
            messages.success(request, "Check your phone and enter your M-Pesa PIN. This page updates once paid.")
        except mpesa.MpesaError as e:
            messages.error(request, f"Could not start M-Pesa prompt: {e}. Use Send Money below.")
    return redirect("pay", ref=b.ref)


@csrf_exempt
@require_POST
def mpesa_callback(request):
    """Safaricom posts the STK result here."""
    try:
        cb = json.loads(request.body)["Body"]["stkCallback"]
        b = Booking.objects.filter(checkout_request_id=cb["CheckoutRequestID"]).first()
        if b and cb["ResultCode"] == 0:
            items = {i["Name"]: i.get("Value") for i in cb["CallbackMetadata"]["Item"]}
            paid = int(items.get("Amount", 0))
            if paid >= b.deposit and b.status != Booking.CANCELLED:
                b.mpesa_code = str(items.get("MpesaReceiptNumber", ""))[:12]
                b.status = Booking.CONFIRMED
                b.save()
    except (KeyError, ValueError, TypeError):
        pass
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})


def pay_status(request, ref):
    b = get_object_or_404(Booking, ref=ref)
    return JsonResponse({"status": b.status})
