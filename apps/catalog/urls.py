from django.urls import path

from apps.catalog.views import (
    CategoryView,
    EventTypeView,
    TemplateVersionPreviewView,
    TemplateVersionPublishView,
    TemplateVersionView,
    TemplateView,
)

urlpatterns = [
    path("categories/", CategoryView.as_view(), name="categories"),
    path("event-types/", EventTypeView.as_view(), name="event-types"),
    path("templates/", TemplateView.as_view(), name="templates"),
    path("template-versions/", TemplateVersionView.as_view(), name="template-versions"),
    path(
        "template-versions/<uuid:version_id>/publish/",
        TemplateVersionPublishView.as_view(),
        name="template-version-publish",
    ),
    path(
        "template-versions/<uuid:version_id>/preview/",
        TemplateVersionPreviewView.as_view(),
        name="template-version-preview",
    ),
]
