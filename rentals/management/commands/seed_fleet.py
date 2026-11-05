from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from rentals.models import Car

PHOTOS = Path(__file__).resolve().parents[2] / "fixtures" / "car_photos"

# (name, category, seats, transmission, fuel, daily self-drive rate KES, units, driver_only, emoji)
FLEET = [
    ("Toyota Vitz", "Economy", 5, "Auto", "Petrol", 2800, 2, False, "🚗"),
    ("Nissan Note", "Economy", 5, "Auto", "Petrol", 3000, 3, False, "🚗"),
    ("Mazda Demio", "Economy", 5, "Auto", "Petrol", 3000, 2, False, "🚗"),
    ("Toyota Axio", "Sedan", 5, "Auto", "Petrol", 3500, 3, False, "🚙"),
    ("Toyota Fielder", "Sedan", 5, "Auto", "Petrol", 3800, 2, False, "🚙"),
    ("Mazda Axela", "Sedan", 5, "Auto", "Petrol", 4500, 2, False, "🚙"),
    ("Toyota Premio", "Sedan", 5, "Auto", "Petrol", 4500, 2, False, "🚙"),
    ("Subaru Forester", "SUV", 5, "Auto", "Petrol", 6500, 2, False, "🚙"),
    ("Mazda CX-5", "SUV", 5, "Auto", "Diesel", 7500, 2, False, "🚙"),
    ("Toyota Harrier", "SUV", 5, "Auto", "Petrol", 8000, 1, False, "🚙"),
    ("Toyota Noah / Voxy", "Van", 8, "Auto", "Petrol", 6000, 2, False, "🚐"),
    ("Toyota Hiace (14 seater)", "Van", 14, "Manual", "Diesel", 12000, 2, False, "🚐"),
    ("Toyota Land Cruiser Prado", "4x4", 7, "Auto", "Diesel", 13000, 2, False, "🛻"),
    ("Toyota Land Cruiser V8", "4x4", 7, "Auto", "Diesel", 25000, 1, False, "🛻"),
    ("Mercedes-Benz E-Class", "Luxury", 5, "Auto", "Petrol", 25000, 1, True, "🏎️"),
    ("Range Rover Sport", "Luxury", 5, "Auto", "Petrol", 55000, 1, True, "🏎️"),
    ("Range Rover Vogue", "Luxury", 5, "Auto", "Petrol", 65000, 1, True, "🏎️"),
]


class Command(BaseCommand):
    help = "Load the Kenyan-market fleet and daily rates (safe to re-run)."

    def handle(self, *args, **opts):
        for name, cat, seats, tr, fuel, rate, units, drv, emoji in FLEET:
            car, _ = Car.objects.get_or_create(name=name, defaults=dict(
                category=cat, seats=seats, transmission=tr, fuel=fuel,
                daily_rate=rate, units=units, driver_only=drv, emoji=emoji))
            img = PHOTOS / f"{slugify(name)}.jpg"
            if not car.photo and img.exists():
                with img.open("rb") as f:
                    car.photo.save(img.name, File(f), save=True)
        self.stdout.write(self.style.SUCCESS(f"{Car.objects.count()} cars in fleet"))
