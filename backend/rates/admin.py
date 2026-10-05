from django.contrib import admin

from .models import Currency, FetchLog, Rate

admin.site.register(Currency)
admin.site.register(FetchLog)


@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ("date", "currency", "per_eur", "source")
    list_filter = ("currency", "source")
