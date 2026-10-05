from django.contrib import admin

from .models import Forecast, ModelMetric

admin.site.register(Forecast)
admin.site.register(ModelMetric)
