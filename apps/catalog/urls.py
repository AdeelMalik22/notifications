from django.urls import path

from apps.catalog.views import CategoryView, EventTypeView, TemplateVersionView, TemplateView

urlpatterns = [
    path("categories/", CategoryView.as_view(), name="categories"),
    path("event-types/", EventTypeView.as_view(), name="event-types"),
    path("templates/", TemplateView.as_view(), name="templates"),
    path("template-versions/", TemplateVersionView.as_view(), name="template-versions"),
]
