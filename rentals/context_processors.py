from urllib.parse import quote

from django.conf import settings

WA_GREETING = ("Hello Car Rental KE! I'm interested in hiring a car. "
               "Could you help me with availability and rates?")


def business(request):
    return {
        "MPESA_NUMBER": settings.MPESA_NUMBER,
        "BUSINESS_PHONE": settings.BUSINESS_PHONE,
        "WHATSAPP_NUMBER": settings.WHATSAPP_NUMBER,
        "WHATSAPP_URL": f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(WA_GREETING)}",
        "DRIVER_FEE": settings.DRIVER_FEE,
        "DEPOSIT_PERCENT": settings.DEPOSIT_PERCENT,
        "STK_ENABLED": settings.MPESA_STK_ENABLED,
        "EXTRA_KM_RATE": settings.EXTRA_KM_RATE,
    }
