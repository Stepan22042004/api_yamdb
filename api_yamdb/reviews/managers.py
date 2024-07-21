from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    '''Менеджер для кастомного пользователя'''

    def create_user(self, email, username, password=None, **extra_fields):
        '''Создание обычного пользователя'''
        if not email:
            raise ValueError('Email поле должно быть заполнено')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        extra_fields.setdefault('is_staff', False)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        '''Создание суперпользователя'''
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперюзер должен иметь is_superuser=True')

        return self.create_user(email, username, password, **extra_fields)
