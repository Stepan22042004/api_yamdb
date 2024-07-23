from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import Category, Comment, User, Genre, Review, Title


# Отображение связанных объектов в админке в виде табличной формы
class GenreInline(admin.TabularInline):
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

# Настройка админки для модели Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    # Устанавливаем ссылку для редактирования
    list_display_links = ('name',)


class UserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'

class UserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'is_active', 'is_staff')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Формы для изменения и добавления пользователя
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'username', 'first_name', 'last_name', 'is_active', 'is_staff', 'role')
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