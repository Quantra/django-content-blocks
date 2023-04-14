Configuration
=============

.. _ContentBlockAvailability:

Restricting the Available Content Block Templates
-------------------------------------------------

You can restrict the available content block templates by creating :py:class:`ContentBlockAvailability` objects in the admin site.  Create a new :py:class:`ContentBlockAvailability` and choose the appropriate ``content_type``. For example if you have an app called ``pages`` with a model called ``Page`` choose ``pages | page``.  Then choose the content block templates you want to make available.

This is useful to restrict the templates which can be used for a certain content type. For example you may have several apps serving several sections of your website.  You can restrict which content block templates can be used on each section.

It is also useful when using :py:class:`NestedField` as you may not want the content block templates associated with the :py:class:`NestedField` to be available for use as a top level content block.

If you don't provide a :py:class:`ContentBlockAvailability` for any given content type then all content block templates will be available by default.

.. _ContentBlockPreviews:

Content Block Previews
----------------------

Content block previews are shown via iframes. This is such that the content block can be rendered using your base template and shown in the content block editor without conflict.

This assumes you have a base template called ``base.html`` in the root of your project templates directory. And this template contains a ``{% block body %}`` just inside the ``<body>`` tag.  It also assumes you will load all necessary static assets required to properly render the content block in the base template. See `base.html <https://github.com/Quantra/django-content-blocks/blob/master/example/templates/base.html>`_ in the repo example project for a minimal example.

If you do not have a base template or it does not define a ``{% block body %}`` you can override the template at ``content_blocks/content_block_preview.html`` to suit your needs. See the packaged `content_block_preview.html <https://github.com/Quantra/django-content-blocks/blob/master/content_blocks/templates/content_blocks/content_block_preview.html>`_ for reference.

.. _PagePreviews:

Page Previews
-------------

To enable page previews in the content block editor you need to add a :py:attr:`preview_url` property to your parent model which returns a valid url to preview the page.  You will also need to provide a view for this url.  This view is responsible for providing :py:meth:`content_blocks.previews()` instead of :py:meth:`content_blocks.visible()`.  For an example see the :doc:`example_pages_app` documentation.

Cache Settings
--------------

By default the html produced by content blocks is stored in and served from the cache.  The following settings are provided to control caching behaviour.

    ``CONTENT_BLOCKS_CACHE``
        Choose which cache to use for content blocks.  Must be set to a valid key in the ``CACHES`` `setting <https://docs.djangoproject.com/en/4.2/ref/settings/#caches>`_.  Defaults to ``"default"``.

    ``CONTENT_BLOCKS_DISABLE_CACHE``
        Disable caching of content blocks. Defaults to ``False``.

    ``CONTENT_BLOCKS_DISABLE_CACHE_ON_START``
        All content blocks are cached during the :py:meth:`AppConfig.ready()` method. This works well with a long or permanent cache as it means content blocks are always ready to be served from the cache.  You can disable this functionality by setting this to ``True``.  Defaults to ``False``.

    ``CONTENT_BLOCKS_DISABLE_UPDATE_CACHE_MODEL_CHOICE``
        A signal is used to update the cache for :py:class:`ModelChoice` fields.  This signal runs on the save of `every` model and will make some database queries. You can disable this feature by setting this to ``True``. In this case you should use the `no_cache` option for :py:class:`ContentBlockTemplate` which contain :py:class:`ModelChoice` fields.  Defaults to ``False``

Storage Backend Settings
------------------------

    ``CONTENT_BLOCKS_STORAGE``
        The storage backend to use for ``Image``, ``Video`` and ``File`` fields. Provide a dotted path as per the ``STORAGES`` `setting <https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-STORAGES>`_.

        Defaults to your ``STORAGES["default"]["BACKEND"]`` setting.

    ``CONTENT_BLOCKS_IMAGE_STORAGE``
        If provided will override the storage backend used for images.

    ``CONTENT_BLOCKS_FILE_STORAGE``
        If provided will override the storage backend used for files.

    ``CONTENT_BLOCKS_VIDEO_STORAGE``
        If provided will override the storage backend used for videos.

Font Awesome Pro Support
------------------------

Django Content Blocks was made using `Font Awesome <https://fontawesome.com/>`_ 6 pro icons.  However due to licencing it is not possible to include them in this package and Font Awesome free icons are used instead.

If you have an appropriate licence to use Fontawesome pro icons in your project you can enable them by providing the following files from your Font Awesome 6 pro kit in your project's static directory.

.. code-block:: text

    content_blocks
    └── fontawesome
        ├── css
        |   ├── fontawesome.min.css
        |   ├── light.min.css
        |   └── thin.min.css
        └── webfonts
            ├── fa-light-300.ttf
            ├── fa-light-300.woff2
            ├── fa-thin-100.ttf
            └── fa-thin-100.woff2


django-dbtemplates Support
--------------------------

`django-dbtemplates <https://github.com/jazzband/django-dbtemplates>`_ let's you create and edit Django template files in the admin site. You can use this to edit content block html template files in the admin site, as well as any other template in your project.

If you set it so that the dbtemplates loader is used before the file loader dbtemplates will be used in preference to the files.  This lets website administrators edit html templates without having any knowledge of Django.

If you are using dbtemplates a button is added to the :py:class:`ContentBlockTemplate` admin change page which links to the dbtemplates change page where the html template can be edited.

django-cleanup Support
----------------------

Django Content Blocks removes unused media files via it's own signals.  If you are using `django-cleanup <https://github.com/un1t/django-cleanup>`_ you don't need to do anything as all the relevant models are decorated with ``@cleanup_ignore`` to avoid conflicts.