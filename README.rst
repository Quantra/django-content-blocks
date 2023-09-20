|package version|
|license|
|pypi status|

|python versions supported|
|django versions supported|

|coverage|
|docs build|

|code style black|
|pypi downloads|
|github stars|

Django Content Blocks
=====================

Django Content Blocks is a reusable Django app that allows users to create and manage custom content blocks for their website. It aims to provide content management and page building features from within the admin site without being a full CMS app or reinventing the admin site.

The content block editor is a simple page builder that integrates seamlessly into the admin site, it provides an easy-to-use interface for creating content blocks.

.. figure:: https://github.com/Quantra/django-content-blocks/raw/master/docs/images/content_block_editor_dark.png
    :alt: The content block editor in the Django admin site.

    The content block editor in the Django admin site.

Content blocks can be related to any other object. This allows you to provide rich, dynamic, editable content for your existing models such as pages, products, projects or whatever models you have.

The templates used to render content blocks are made in the same way as any other template in your project, giving you access to the full power of your chosen template engine. You define the fields that are available to edit your content blocks in the content block editor. This means you can build a content block template once and reuse it over and over again.

Content blocks can contain any type of content, including text, images, videos, and more, and can be arranged in any order. Additionally, Django Content Blocks includes support for drafts and previews, allowing users to see how their changes will look before publishing them.

Installation instructions and detailed documentation can be found on `ReadTheDocs <https://django-content-blocks.readthedocs.io>`_.

Development Status & Roadmap
----------------------------

Django content blocks is already in use in a number of production websites however it is still considered to be in beta as active development continues.

Major development plans/ideas include:

* Content block editor HTML, CSS and JS rework.
    * This all needs updating to use modern HTML and CSS (flex, grid etc) and vanilla JS.
    * Currently using jQuery which isn't the end of the world as it comes with django.contrib.admin so not an extra dependency.
* Option for vertical layout for nested forms in the content block editor
    * Sometimes nested blocks can represent columns within a content block. It would be nice to give the option to have these shown side by side in the content block editor.
* django-content-blocks 2.0
    * This will be a major rewrite which will move the representation of content blocks out of the database and into a ``JSONField``. This will greatly improve performance as the whole representation of an object's content blocks can be returned at once and any subsequent queries required can be made in a prefetch fashion.
    * The ``ContentBlockField`` will become pluggable allowing developers to add/remove available fields from within their project.
* Django content blocks suite of apps providing additional functionality and basic apps powered by content blocks:
    * CMS
    * Blog
    * Contact forms

Dependencies (and Thank You)
----------------------------

* https://github.com/jrief/django-admin-sortable2
* https://github.com/tj-django/django-clone
* https://github.com/python-pillow/Pillow

Thank You
---------

* https://shystudios.co.uk - For the monies I need to eat
* https://opalstack.com/?lmref=A2GlhA - For great value hosting and superb support over the years (affiliate link)
* https://chat.openai.com/ - For documentation rewrites
* https://github.com/django-hijack/django-hijack - For conf.py LazySettings idea
* https://github.com/cookiecutter/cookiecutter-django - For many things including docker
* Dmitry Sobolev for so graciously transferring the django-content-blocks name on pypi
* Margo Yaguda for linguistic assistance in contacting Dmitry

Contributing
------------

Contributions, advice and guidance are welcome. Please make contact **before** writing any code!


.. shields.io badges

.. |package version| image:: https://img.shields.io/pypi/v/django-content-blocks
    :alt: PyPI Package Version
    :target: https://pypi.python.org/pypi/django-content-blocks/

.. |python versions supported| image:: https://img.shields.io/pypi/pyversions/django-content-blocks
    :alt: Python Versions Supported
    :target: https://pypi.python.org/pypi/django-content-blocks/

.. |django versions supported| image:: https://img.shields.io/pypi/frameworkversions/django/django-content-blocks
    :alt: Django Versions Supported
    :target: https://pypi.python.org/pypi/django-content-blocks/

.. |coverage| image:: https://img.shields.io/badge/dynamic/xml?color=success&label=coverage&query=round%28%2F%2Fcoverage%2F%40line-rate%20%2A%20100%29&suffix=%25&url=https%3A%2F%2Fraw.githubusercontent.com%2FQuantra%2Fdjango-content-blocks%2Fmaster%2Fcoverage.xml
    :alt: Test Coverage
    :target: https://github.com/Quantra/django-content-blocks/blob/master/coverage.xml

.. |code style black| image:: https://img.shields.io/badge/code%20style-black-black
    :alt: Code Style Black
    :target: https://github.com/psf/black

.. |license| image:: https://img.shields.io/github/license/Quantra/django-content-blocks
    :alt: MIT License
    :target: https://github.com/Quantra/django-content-blocks/blob/master/LICENSE

.. |docs build| image:: https://img.shields.io/readthedocs/django-content-blocks
    :alt: Read the Docs
    :target: https://django-content-blocks.readthedocs.io/

.. |github stars| image:: https://img.shields.io/github/stars/Quantra/django-content-blocks?style=social
    :alt: GitHub Repo Stars
    :target: https://github.com/Quantra/django-content-blocks/stargazers

.. |pypi downloads| image:: https://img.shields.io/pypi/dm/django-content-blocks
    :alt: PyPI Downloads
    :target: https://pypi.python.org/pypi/django-content-blocks/

.. |pypi status| image:: https://img.shields.io/pypi/status/django-content-blocks
    :alt: PyPI Status
    :target: https://pypi.python.org/pypi/django-content-blocks/
