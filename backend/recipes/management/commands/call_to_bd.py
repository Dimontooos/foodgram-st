import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient
from django.db.utils import ProgrammingError


class Command(BaseCommand):
    help = 'Load ingredients data from JSON file into the Ingredient model'

    def handle(self, *args, **options):
        verbosity = options.get('verbosity', 1)
        file_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.json')

        try:
            try:
                before_count = Ingredient.objects.count()
            except ProgrammingError as e:
                if 'relation "recipes_ingredient" does not exist' in str(e):
                    self.stdout.write(
                        self.style.ERROR(
                            'Table "recipes_ingredient" does not exist. '
                            'Please run migrations first: '
                            'python manage.py migrate'
                        )
                    )
                    return
                raise e

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File {file_path} does not exist")

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError(
                    "JSON data must be a list of ingredient objects")

            ingredients = []
            for item in data:
                if not isinstance(item, dict):
                    if verbosity > 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Skipping invalid item: {item} "
                                "(must be a dictionary)"
                            )
                        )
                    continue
                if 'name' not in item or 'measurement_unit' not in item:
                    if verbosity > 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Skipping item {item} "
                                "(missing 'name' or 'measurement_unit')"
                            )
                        )
                    continue
                ingredients.append(Ingredient(**item))

            if not ingredients:
                if verbosity > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            "No valid ingredients found in the JSON file"
                        )
                    )
                return

            Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)
            after_count = Ingredient.objects.count()
            created_count = after_count - before_count

            if verbosity > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully loaded {created_count} new ingredients"
                    )
                )
                if created_count < len(ingredients):
                    self.stdout.write(
                        self.style.WARNING(
                            f"{len(ingredients) - created_count} ingredients "
                            "were skipped due to conflicts"
                        )
                    )

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f"File error: {e}"))
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"JSON decode error: {e}"))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"Data validation error: {e}"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Unexpected error loading data from {file_path}: {e}"
                )
            )
