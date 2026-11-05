from django.conf import settings


def business(request):
    return {
        "MPESA_NUMBER": settings.MPESA_NUMBER,
        "BUSINESS_PHONE": settings.BUSINESS_PHONE,
        "WHATSAPP_NUMBER": settings.WHATSAPP_NUMBER,
        "DRIVER_FEE": settings.DRIVER_FEE,
        "DEPOSIT_PERCENT": settings.DEPOSIT_PERCENT,
        "STK_ENABLED": settings.MPESA_STK_ENABLED,
        "EXTRA_KM_RATE": settings.EXTRA_KM_RATE,
    }
