import csv
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from reviews.models import Category, Comment, Genre, Review, Title, User

STATIC_DATA_PATH = 'static/data/'


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
                    user, created = User.objects.get_or_create(
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
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Создан пользователь {user.username}'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Пользователь {user.username} уже существует'
                            )
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Ошибка создания пользователя с id {row[0]}: {e}'
                        )
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
                    self.stdout.write(
                        self.style.WARNING(
                            f'Произведение с id {row[1]} не найдено.'
                        )
                    )
                    continue

                try:
                    author = User.objects.get(id=row[3])
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Автор с id {row[3]} не найден.')
                    )
                    continue

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
                    author = User.objects.get(id=row[3])
                    comment, created = Comment.objects.get_or_create(
                        id=row[0],
                        review=review,
                        text=row[2],
                        author=author,
                        pub_date=parse_datetime(row[4])
                    )
                except ObjectDoesNotExist as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Ошибка: {e}. Коммент с id {row[0]} не создан.'
                        )
                    )
