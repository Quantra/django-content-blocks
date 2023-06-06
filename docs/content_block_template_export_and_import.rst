Content Block Template Export and Import
========================================

Exporting and importing :py:class:`ContentBlockTemplate` allows reuse of your :py:class:`ContentBlockTemplate` in other projects.

.. note::
    When moving :py:class:`ContentBlockTemplate` to a project you will also need to provide any required html templates and static files.

Natural Keys
------------

Natural keys are used when serializing and deserializing. :py:class:`ContentBlockTemplate` are referenced by their name and :py:class:`ContentBlockTemplateField` are additionally referenced by their key.

This becomes important when importing when there are existing :py:class:`ContentBlockTemplate`.  Any :py:class:`ContentBlockTemplate` with the same name will be updated as will child :py:class:`ContentBlockTemplateField` with the same key.

.. note::
    If the key changes for any :py:class:`ContentBlockTemplateField` then it will be deleted and a new :py:class:`ContentBlockTemplateField` with the new key will be created.

.. warning::
    Any :py:class:`ContentBlockTemplateField` which has been added or removed from the parent :py:class:`ContentBlockTemplate` will be added or removed from :py:class:`ContentBlock`. Due to this data can be lost in published :py:class:`ContentBlock` and care must be taken when working with production data.

You can read more about natural keys in the `official Django documentation. <https://docs.djangoproject.com/en/4.2/topics/serialization/#natural-keys>`_

Exporting
---------

The ``export_content_block_templates`` management command will serialize all :py:class:`ContentBlockTemplate` to JSON and output to stdout.  Output can be directed to a file:

.. code-block:: bash

    $ python3 manage.py export_content_block_templates > content_block_templates.json

A button is provided on the :py:class:`ContentBlockTemplate` admin changelist page which will serialize all :py:class:`ContentBlockTemplate` and provide a JSON file for download.

An admin action is available such that you can choose which :py:class:`ContentBlockTemplate` to export.

Importing
---------

The ``import_content_block_templates`` management command takes a single argument for the JSON file location.

.. code-block:: bash

    $ python3 manage.py import_content_block_templates content_block_templates.json

A button is provided on the :py:class:`ContentBlockTemplate` admin changelist page which provides a form where a JSON file can be uploaded.
