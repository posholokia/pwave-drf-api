from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


class UserViewsAdmin(admin.ModelAdmin):
    list_display = ('email', 'name')
    list_filter = ('email', 'name')
    search_fields = ('email', 'name')


admin.site.register(User, UserViewsAdmin)
