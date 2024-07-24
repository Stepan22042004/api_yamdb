from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from reviews.models import User


class UserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


class UserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'is_active', 'is_staff')
