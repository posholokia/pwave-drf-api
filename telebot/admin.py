from django.contrib import admin
from .models import TeleBotID


class TelebotAdmin(admin.ModelAdmin):
    list_display = ('user', 'telegram_id', 'name')
    list_filter = ('user', 'telegram_id', 'name')
    search_fields = ('user', 'telegram_id', 'name')


admin.site.register(TeleBotID, TelebotAdmin)
