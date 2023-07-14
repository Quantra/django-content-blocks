Cacheing Content Blocks
=======================

For improved performance you can cache your content blocks using template fragment cacheing.  Read more about it in the `official Django documentation. <https://docs.djangoproject.com/en/4.2/topics/cache/#template-fragment-caching>`_

.. note::
    Content blocks containing :py:class:`NestedField` can see significant performance benefits from cacheing.

When content blocks are published new content blocks are always created in the database.  This means you can vary the cache on the content block ID to automatically invalidate the cache.

You should only cache published content blocks.  Draft content blocks, which are used in previews and page previews, should not be cached.  To achieve this add a ``"cache_timeout"`` variable to the context in your view(s) which render content blocks.  Set this to your desired timeout in seconds (or  use ``None`` to cache indefinitely).  For your page previews set this to ``0`` to prevent cacheing.

With this the views from the :doc:`example pages app <example_pages_app>` become:

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

        cache_timeout = 0 if preview else 5 * 60

        return render(
            request,
            "pages/page_detail.html",
            {
                "page": page,
                "content_blocks": content_blocks,
                "cache_timeout": cache_timeout
            },
        )

.. warning::
    The ``cache_timout`` variable is used in the view for content block previews.  If you use a different variable name in your view(s) content block previews will not behave as expected.

For example to add cacheing to the content block in :doc:`getting started <getting_started>`:

.. code-block:: django
    :caption: content_blocks/content_blocks/my_first_content_block.html

    {% load cache %}

    {% cache cache_timeout "my_first_content_block" content_block_object.id %}
        <div class="content-block {{ content_block.css_class }}">
            <h1>{{ content_block.heading }}</h1>
            <img src="{{ content_block.image.url }}" />
        </div>
    {% endcache %}

.. warning::
    If your content block uses data from a :py:class:`ModelChoiceField` or related data from another object you should either not cache the content block or add another argument to the ``{% cache %}`` template tag which varies when the related object is updated.

By default content blocks are pre rendered on publish, this will populate the cache ready for your visitors.  If you are using `django-lazy-srcset <https://github.com/Quantra/django-lazy-srcset>`_ this will also pre generate responsive images. If you want to disable pre rendering you can do so in your settings:

    ``CONTENT_BLOCKS_PRE_RENDER``
        When ``True`` content blocks are rendered on publish.
