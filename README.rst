|coverage|
|package version|
|python versions supported|
|django versions supported|
|code style black|
|license|

=====================
Django Content Blocks
=====================

Django Content Blocks is a reusable Django app that allows users to create and manage custom content blocks for their website. Via the django admin site it provides an easy-to-use interface for creating content blocks that can be inserted into any page, as well as a powerful template system for customizing the appearance of those blocks.

Content blocks can contain any type of content, including text, images, videos, and more, and can be arranged in any order on a page. Additionally, Django Content Blocks includes support for drafts and previews, allowing users to see how their changes will look before publishing them.

.. image:: https://github.com/Quantra/django-content-blocks/raw/master/docs/images/content_block_editor_dark.png

Installation instructions and detailed documentation can be found on `ReadTheDocs <https://django-content-blocks.readthedocs.io>`_.

Supported Django & Python Versions
----------------------------------

* Python >= 3.7
* Django >= 3.2

Dependencies (and Thank You)
----------------------------

* https://github.com/jrief/django-admin-sortable2
* https://github.com/tj-django/django-clone - Additional thanks for tox.ini setup
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
   :target: https://pypi.python.org/pypi/django-content-blocks/

.. |python versions supported| image:: https://img.shields.io/pypi/pyversions/django-content-blocks
   :target: https://pypi.python.org/pypi/django-content-blocks/

.. |django versions supported| image:: https://img.shields.io/pypi/frameworkversions/django/django-content-blocks
   :target: https://pypi.python.org/pypi/django-content-blocks/

.. |coverage| image:: https://img.shields.io/badge/dynamic/xml?color=success&label=coverage&query=round%28%2F%2Fcoverage%2F%40line-rate%20%2A%20100%29&suffix=%25&url=https%3A%2F%2Fraw.githubusercontent.com%2FQuantra%2Fdjango-content-blocks%2Fmaster%2Fcoverage.xml

.. |code style black| image:: https://img.shields.io/badge/code%20style-black-black
    :target: https://github.com/psf/black

.. |license| image:: https://img.shields.io/github/license/Quantra/django-content-blocks
    :target: https://github.com/Quantra/django-content-blocks/blob/master/LICENSE
