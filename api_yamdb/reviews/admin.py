from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from reviews.models import Category, Comment, Genre, Review, Title, User


class GenreInline(admin.TabularInline):
    """Отображение связанных объектов в админке в виде табличной формы."""

    model = Title.genre.through
    extra = 1


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'display_genre')
    list_editable = ('category',)
    inlines = [GenreInline]

    def display_genre(self, obj):
        return ", ".join([genre.name for genre in obj.genre.all()])
    display_genre.short_description = 'Genres'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Настройка админки для модели Category."""

    list_display = ('name',)
    list_display_links = ('name',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Формы для изменения и добавления пользователя."""

    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'username', 'first_name',
                    'last_name', 'is_active', 'is_staff', 'role')
    list_editable = ('role', 'is_active', 'is_staff')

    # Настройка доп. полей в форме изменения пользователя
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )

    # Настройка доп. полей в форме добавления пользователя
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )


admin.site.register(Genre)
admin.site.register(Review)
admin.site.register(Comment)
