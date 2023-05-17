from django.apps import apps


class ParentServices:
    @staticmethod
    def parent_models(content_block_parent_model):
        """
        Return a list of models that use content blocks.
        :param content_block_parent_model: ContentBlockParent abstract class.
        """
        return [
            model
            for model in apps.get_models()
            if issubclass(model, content_block_parent_model)
        ]

    @staticmethod
    def parent_sites(content_block_parent):
        """
        :return: An iterable of related Site objects if possible. If not return a list containing None.
        """
        content_blocks_sites_field = getattr(
            content_block_parent, "content_blocks_sites_field", None
        )
        if content_blocks_sites_field is None:
            return [None]

        try:
            iter(content_block_parent.content_blocks_sites_field)
            return content_block_parent.content_blocks_sites_field
        except TypeError:
            return [content_block_parent.content_blocks_sites_field]
