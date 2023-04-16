from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    list_filter = ('email', 'username')
    search_fields = ('email', 'username')
    empty_value_display = '-пусто-'


admin.site.register(User, CustomUserAdmin)
