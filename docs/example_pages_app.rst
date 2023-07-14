Example Pages App
=================

Django Content Blocks works great with your existing models but if you need a simple app to create pages using content blocks this section will provide you with code samples to create one.

You can find a similar app in the project repository in the example project. This documentation assumes you are familiar with creating apps, models, admin, URLs, views, and templates in Django. If you are not, please complete the Django tutorial first. The samples are written as if you have run ``python3 manage.py startapp pages``, but you can call the app anything you like.

Models
------

We will need a simple model to represent our pages. We require at least a slug and to extend :py:class:`ContentBlockParentModel`.

.. code-block:: python
    :caption: pages/models.py

    from django.db import models
    from django.urls import reverse

    from content_blocks.models import ContentBlockParentModel


    class Page(ContentBlockParentModel):
        slug = models.SlugField(unique=True, blank=True)

        def __str__(self):
            return self.slug or "Home"

        def get_absolute_url(self):
            if self.slug:
                return reverse("page_detail", args=[self.slug])
            return reverse("home")

        @property
        def preview_url(self):
            if self.slug:
                return reverse("page_detail_preview", args=[self.slug])
            return reverse("home_preview")

The :py:attr:`preview_url` property is provided to enable the `Preview on Site` button in the content block editor.  You can read more about this in the :doc:`configuration` section.

Admin
-----

We need an ``admin.py`` file for our model.  As a minimum we need to show the slug field and content block editor button on the change page.  We can also show a link to the content block editor on the change list.

By inheriting from :py:class:`ContentBlockModelAdmin` we can use ``"content_blocks_button"`` in :py:attr:`fieldsets` and ``"content_blocks_link"`` in :py:attr:`list_display`.

.. code-block:: python
    :caption: pages/admin.py

    from django.contrib import admin

    from content_blocks.admin import ContentBlockModelAdmin

    from .models import Page


    @admin.register(Page)
    class PageAdmin(ContentBlockModelAdmin):
        list_display = ["__str__", "content_blocks_link"]

        fieldsets = (
            (
                "Page",
                {"fields": ["slug", "content_blocks_button"]},
            ),
        )

Views
-----

One view is enough to handle the homepage, page detail and preview views.

.. code-block:: python
    :caption: pages/views.py

    from django.shortcuts import get_object_or_404, render

    from .models import Page


    def page_detail(request, page_slug=None, preview=False):
        page_slug = page_slug or ""
        page = get_object_or_404(Page, slug=page_slug)

        content_blocks = (
            page.content_blocks.previews() if preview else page.content_blocks.visible()
        )

        return render(
            request,
            "pages/page_detail.html",
            {
                "page": page,
                "content_blocks": content_blocks,
            },
        )

Template
--------

This ``page_detail.html`` template shows an example of what is required to render the page.  You should edit it to reflect your base template name and blocks.

.. code-block:: django
    :caption: pages/templates/pages/page_detail.html

    {% extends 'base.html' %}
    {% load content_blocks %}

    {% block main %}
        {% for content_block in content_blocks %}
            {% render_content_block content_block %}
        {% endfor %}
    {% endblock %}

Urls
----

We will need a ``urls.py`` file for our app.  This will handle the homepage and page detail views as well as the preview views needed for the `Preview on Site` button in the content block editor.

.. code-block:: python
    :caption: pages/urls.py

    from django.urls import path

    from .views import page_detail

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

Then include this ``urls.py`` in your project base ``urls.py`` by adding ``path("", include("pages.urls"))`` to your ``urlpatterns``.

.. code-block:: python
    :caption: myproject/urls.py

    ...
    urlpatterns = [
        path("admin/", admin.site.urls),
        path("content-blocks/", include("content_blocks.urls")),
        ...
        path("", include("pages.urls")),
    ]
    ...
