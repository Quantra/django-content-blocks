from django.apps import apps

from content_blocks.models import ContentBlockParentModel


class ParentServices:
    """
    Services for dealing with ContentBlockParentModel subclasses.
    """

    @staticmethod
    def parent_models():
        """
        Return a list of models that use content blocks. Ie models that subclass ContentBlockParentModel.
        """
        return [
            model
            for model in apps.get_models()
            if issubclass(model, ContentBlockParentModel)
        ]

    @staticmethod
    def parent_sites(content_block_parent):
        """
        :param content_block_parent: Instance of a ContentBlockParentModel subclass.
        :return: An iterable of related Site objects if possible. If not return a list containing None.
        """
        content_blocks_sites_field = getattr(
            content_block_parent, "content_blocks_sites_field", None
        )
        if content_blocks_sites_field is None:
            return [None]

        if hasattr(content_blocks_sites_field, "all"):
            return content_blocks_sites_field.all()

        return [content_blocks_sites_field]
