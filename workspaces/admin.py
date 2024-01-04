from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import *

User = get_user_model()


class WorkSpaceViewAdmin(admin.ModelAdmin):
    list_display = ('owner', 'name', 'users', 'invited')
    list_filter = ('owner', 'name', 'users', 'invited')
    search_fields = ('owner', 'name', 'users', 'invited')


admin.site.register(WorkSpace, WorkSpaceViewAdmin)
admin.site.register(Board)
admin.site.register(Column)
admin.site.register(InvitedUsers)
admin.site.register(Task)
admin.site.register(Sticker)
