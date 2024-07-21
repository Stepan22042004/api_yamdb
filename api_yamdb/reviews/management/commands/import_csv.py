import csv
import logging
from django.core.management.base import BaseCommand
from reviews.models import Category, Genre, Title, Review, Comment, CustomUser
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ObjectDoesNotExist

STATIC_DATA_PATH = 'api_yamdb/api_yamdb/static/data/'

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s'
)

class Command(BaseCommand):
    help = 'Import data from CSV files'

    def handle(self, *args, **kwargs):
        self.import_categories()
        self.import_genres()
        self.import_titles()
        self.import_genres_titles()
        self.import_reviews()
        self.import_comments()

    def import_users(self):
        with open(
            STATIC_DATA_PATH + 'users.csv',
            'r',
            encoding='utf-8'
        ) as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                try:
                    user, created = CustomUser.objects.get_or_create(
                        id=row[0],
                        defaults={
                            'username': row[1],
                            'email': row[2],
                            'role': row[3],
                            'bio': row[4],
                            'first_name': row[5],
                            'last_name': row[6]
                        }
                    )
                    if created:
                        logger.info(f'Создан {user.username}')
                    else:
                        logger.warning(f'{user.username} уже существует')
                except Exception as e:
                    logger.error(
                        f'Ошибка создания пользователя с id {row[0]}: {e}'
                    )

    def import_categories(self):
        with open(
            STATIC_DATA_PATH + 'category.csv',
            'r',
            encoding='utf-8'
        ) as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                Category.objects.get_or_create(
                    id=row[0],
                    name=row[1],
                    slug=row[2]
                )

    def import_genres(self):
        with open(
            STATIC_DATA_PATH + 'genre.csv',
            'r',
            encoding='utf-8'
        ) as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                Genre.objects.get_or_create(
                    id=row[0],
                    name=row[1],
                    slug=row[2]
                )

    def import_titles(self):
        with open(
            STATIC_DATA_PATH + 'titles.csv',
            'r',
            encoding='utf-8'
        ) as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                category = Category.objects.get(id=row[3])
                Title.objects.get_or_create(
                    id=row[0],
                    name=row[1],
                    year=row[2],
                    category=category
                )

    def import_genres_titles(self):
        with open(
            STATIC_DATA_PATH + 'genre_title.csv',
            'r',
            encoding='utf-8'
        ) as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                title = Title.objects.get(id=row[1])
                genre = Genre.objects.get(id=row[2])
                title.genre.add(genre)

    def import_reviews(self):
        with open(
            STATIC_DATA_PATH + 'review.csv',
            'r',
            encoding='utf-8'
        ) as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                try:
                    title = Title.objects.get(id=row[1])
                except ObjectDoesNotExist:
                    logger.warning(f'Произведение с id {row[1]} не найдено.')
                    continue  # Пропускаем строки с отсутствующим заголовком

                try:
                    author = CustomUser.objects.get(id=row[3])
                except CustomUser.DoesNotExist:
                    logger.warning(f'Автор с id {row[3]} не найден.')
                    continue  # Пропускаем строки с отсутствующим автором

                Review.objects.get_or_create(
                    id=row[0],
                    defaults={
                        'title': title,
                        'text': row[2],
                        'author': author,
                        'score': row[4],
                        'pub_date': parse_datetime(row[5])
                    }
                )

    def import_comments(self):
        with open(
            STATIC_DATA_PATH + 'comments.csv',
            'r',
            encoding='utf-8'
        ) as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                try:
                    review = Review.objects.get(id=row[1])
                    author = CustomUser.objects.get(id=row[3])
                    comment, created = Comment.objects.get_or_create(
                        id=row[0],
                        review='N/A' if review is None else review,
                        text=row[2],
                        author=author,
                        pub_date=parse_datetime(row[4])
                    )
                except ObjectDoesNotExist as e:
                    logger.warning(
                        f'Ошибка: {e}. Коммент с id {row[0]} не создан.'
                    )
