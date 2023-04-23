import csv

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из csv файла'

    def handle(self, *args, **kwargs):
        file = open('./ingredients.csv', encoding='utf-8')
        reader = csv.reader(file)
        for row in reader:
            _, created = Ingredient.objects.get_or_create(
                name=row[0],
                measurement_unit=row[1]
            )
        print('done!')
