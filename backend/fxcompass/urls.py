from django.contrib import admin
from django.urls import path

from alerts import views as alerts
from analytics import views as analytics
from forecasting import views as forecasting
from rates import views as rates

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/currencies", rates.currencies),
    path("api/status", rates.status),
    path("api/rates/latest", analytics.latest),
    path("api/convert", analytics.convert),
    path("api/history", analytics.history),
    path("api/gain-loss", analytics.gain_loss),
    path("api/volatility", analytics.volatility),
    path("api/heatmap", analytics.heatmap),
    path("api/forecast", forecasting.forecast),
    path("api/alerts", alerts.alert_list),
    path("api/alerts/<int:pk>", alerts.alert_detail),
]
