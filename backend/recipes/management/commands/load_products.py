import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Product


class Command(BaseCommand):
    help = 'Load products data from JSON file into the Product model'

    def handle(self, *args, **options):
        file_path = os.path.join(
            settings.BASE_DIR,
            'data',
            'ingredients.json'
        )

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        products = [
            Product(
                name=item['name'],
                measurement_unit=item['measurement_unit']
            )
            for item in data
            if isinstance(item, dict) and 'name' in item and 'measurement_unit' in item
        ]

        if products:
            Product.objects.bulk_create(products, ignore_conflicts=True)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully loaded {len(products)} new products"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "No valid products found in the JSON file"
                )
            )
