"""
Pages app urls.py
"""
from django.urls import path

from example.pages.views import page_detail

app = "pages"

urlpatterns = [
    path("homepage-preview/", page_detail, {"preview": True}, name="home_preview"),
    path(
        "<slug:page_slug>/page-preview/",
        page_detail,
        {"preview": True},
        name="page_detail_preview",
    ),
    path("<slug:page_slug>/", page_detail, name="page_detail"),
    path("", page_detail, name="home"),
]
