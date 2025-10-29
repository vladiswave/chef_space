import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    help = 'Загрузка данных из JSON-файлов в базу данных'

    def handle(self, *args, **options):
        data_dir = os.path.join(settings.BASE_DIR.parent, 'app', 'data')
        self.load_data(
            data_dir,
            'ingredients.json',
            Ingredient,
            ['name', 'measurement_unit']
        )
        self.load_data(
            data_dir,
            'tags.json',
            Tag,
            ['name', 'slug'],
            need_slug=True
        )

    def load_data(self, data_dir, file_name, model, fields, need_slug=False):
        """Загрузка данных из JSON-файла"""
        file_path = os.path.join(data_dir, file_name)
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'Файл {file_path} не найден!'))
            return
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError as e:
                self.stderr.write(self.style.ERROR(f'Ошибка чтения JSON: {e}'))
                return
            objs_to_create = []
            for item in data:
                if need_slug and 'slug' not in item and 'name' in item:
                    item['slug'] = slugify(item['name'])[:50]
                if not all(field in item for field in fields):
                    continue
                objs_to_create.append(
                    model(**{field: item[field] for field in fields})
                )

            created = model.objects.bulk_create(
                objs_to_create, ignore_conflicts=True
            )
            self.stdout.write(self.style.SUCCESS(
                f'Успешно создано {len(created)} объектов для {model.__name__}'
            ))
