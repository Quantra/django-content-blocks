from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template, render_to_string

from content_blocks.cache import cache
from content_blocks.conf import settings
from content_blocks.services.content_block_parent import ParentServices


class ContentBlockFilters:
    @staticmethod
    def renderable(queryset):
        """
        Take a queryset of ContentBlock and filter to top level with a template file.
        """
        return queryset.filter(parent__isnull=True).exclude(
            content_block_template__template_filename=""
        )

    @staticmethod
    def published_renderable(queryset):
        """
        Take a queryset of ContentBlock and filter to draft=False then filter by renderable.
        """
        content_blocks = queryset.filter(draft=False)
        return ContentBlockFilters.renderable(content_blocks)

    @staticmethod
    def content_blocks_in_queryset(content_blocks, queryset):
        """
        :param content_blocks: ContentBlock queryset to limit.
        :param queryset: ContentBlock queryset to limit by.
        :return: queryset of ContentBlock that are in both content_blocks and queryset
        """
        queryset_ids = queryset.values_list("id", flat=True)
        content_blocks = content_blocks.filter(id__in=queryset_ids)
        return content_blocks


class CacheServices:
    @staticmethod
    def cache_key(content_block, site=None):
        """
        :return: cache key for the provided content block and optional site.
        """
        cache_key = f"{settings.CONTENT_BLOCKS_CACHE_PREFIX}_{content_block.id}"

        site_id = getattr(site, "id", None)
        if site_id is None:
            return cache_key

        return f"{cache_key}_site_{site_id}"

    @staticmethod
    def get_cache(content_block, site=None):
        """
        Get html from the cache for the given ContentBlock.
        """
        cache_key = CacheServices.cache_key(content_block, site=site)
        return cache.get(cache_key)

    @staticmethod
    def set_cache(content_block, html, site=None):
        """
        Set the cache for the given ContentBlock.
        """
        if not RenderServices.can_cache(content_block):
            return

        cache_key = CacheServices.cache_key(content_block, site=site)
        cache.set(cache_key, html)

    @staticmethod
    def get_or_set_cache(content_block, context=None, site=None):
        """
        Get the html from the cache for the given content. If it isn't in the cache set it.
        :return: The html for the given content block.
        """
        context = context or RenderServices.context(content_block)
        html = CacheServices.get_cache(content_block, site=site)

        if html is None:
            html = RenderServices.render_html(content_block, context, site=site)
            CacheServices.set_cache(content_block, html, site=site)

        return html

    @staticmethod
    def get_or_set_cache_per_site(content_block, sites):
        """
        Get or set the cache for the given content block for each site in sites.
        """
        for site in sites:
            CacheServices.get_or_set_cache(content_block, site=site)

    @staticmethod
    def get_or_set_cache_parent_model(content_block_parent_model):
        """
        Get or set the cache for all content blocks in the given parent model objects.
        :param content_block_parent_model: ContentBlockParent() (subclass) instance.
        """
        for obj in content_block_parent_model.objects.all():
            sites = ParentServices.parent_sites(obj)
            content_blocks = ContentBlockFilters.published_renderable(
                obj.content_blocks.all()
            )

            for content_block in content_blocks:
                if RenderServices.can_cache(content_block):
                    # Early bail out if this shouldn't be cached.
                    CacheServices.get_or_set_cache_per_site(content_block, sites)

    @staticmethod
    def get_or_set_cache_published(content_block_parent_model):
        """
        Get or set the cache for all published content blocks.
        Used to prepopulate the cache in app.ready()
        :param content_block_parent_model: ContentBlockParent abstract class.
        """
        if settings.CONTENT_BLOCKS_DISABLE_CACHE:
            return

        models = ParentServices.parent_models(content_block_parent_model)

        for model in models:
            CacheServices.get_or_set_cache_parent_model(model)

    @staticmethod
    def delete_cache(content_block, site=None, cache_key=None):
        """
        Clear the html from the cache for the given content_block and any parent recursively.
        """
        cache_key = cache_key or CacheServices.cache_key(content_block, site=site)
        cache.delete(cache_key)

        if content_block.parent:
            CacheServices.delete_cache(content_block.parent.content_block, site=site)

    @staticmethod
    def delete_cache_per_site(content_block, sites):
        """
        Delete the cache for the given content block for each site in sites.
        """
        for site in sites:
            CacheServices.delete_cache(content_block, site=site)

    @staticmethod
    def delete_cache_parent_model(content_block_parent_model):
        """
        Delete the cache for all content blocks in the given parent model objects.
        :param content_block_parent_model: ContentBlockParent() (subclass) instance.
        """
        for obj in content_block_parent_model.objects.all():
            sites = ParentServices.parent_sites(obj)
            content_blocks = ContentBlockFilters.renderable(obj.content_blocks.all())

            for content_block in content_blocks:
                CacheServices.delete_cache_per_site(content_block, sites)

    @staticmethod
    def delete_cache_all(content_block_parent_model):
        """
        Delete the cache for all content blocks on a per-site basis.
        Used to delete the cache via the content_blocks_clear_cache management command.
        :param content_block_parent_model: ContentBlockParent abstract class.
        """
        if settings.CONTENT_BLOCKS_DISABLE_CACHE:
            return  # pragma: no cover (covered by settings tests)

        models = ParentServices.parent_models(content_block_parent_model)

        for model in models:
            CacheServices.delete_cache_parent_model(model)

    @staticmethod
    def update_cache(content_block, context=None, site=None):
        """
        Update the html stored in the cache for the given content block and any parent recursively.
        """
        if "context" in content_block.__dict__.keys():
            # Clear the context cached property if present
            del content_block.__dict__["context"]

        html = RenderServices.render_html(content_block, context=context, site=site)
        CacheServices.set_cache(content_block, html, site=site)

        if content_block.parent:
            CacheServices.update_cache(
                content_block.parent.content_block, context=context, site=site
            )

    @staticmethod
    def update_cache_per_site(content_block, sites, context=None):
        """
        Update the cache for the given content block for each site in sites.
        """
        for site in sites:
            CacheServices.update_cache(content_block, context=context, site=site)

    @staticmethod
    def update_cache_parent_model(content_block_parent_model, queryset=None):
        """
        Update the cache for all content blocks in the parent model objects.
        :param content_block_parent_model: ContentBlockParentModel subclass.
        :param queryset: ContentBlock queryset to limit the update to.
        """
        for obj in content_block_parent_model.objects.all():
            sites = ParentServices.parent_sites(obj)
            content_blocks = ContentBlockFilters.renderable(obj.content_blocks.all())

            if queryset is not None:
                content_blocks = ContentBlockFilters.content_blocks_in_queryset(
                    content_blocks, queryset
                )

            for content_block in content_blocks:
                CacheServices.update_cache_per_site(content_block, sites)

    @staticmethod
    def update_cache_all(content_block_parent_model, queryset=None):
        """
        Update the cache for all content blocks on a per-site basis.
        Used by content_blocks_update_cache management command.
        :param content_block_parent_model: ContentBlockParentModel class.
        :param queryset: ContentBlock queryset to limit the update to.
        """
        if settings.CONTENT_BLOCKS_DISABLE_CACHE:
            return

        models = ParentServices.parent_models(content_block_parent_model)

        for model in models:
            CacheServices.update_cache_parent_model(model, queryset=queryset)

    @staticmethod
    def update_cache_content_block(content_block, content_block_parent):
        """
        Update the cache for a content block across all sites given its parent.
        """
        sites = ParentServices.parent_sites(content_block_parent)
        CacheServices.update_cache_per_site(content_block, sites)


class RenderServices:
    @staticmethod
    def render_content_block(content_block, context=None):
        """
        Main public render method.  Used by ContentBlock.render and {% render_content_block %}
        :return: Rendered html for the content block.
        """
        context = RenderServices.context(content_block, context=context)
        site = RenderServices.site(context)

        if RenderServices.can_cache(content_block):
            return CacheServices.get_or_set_cache(content_block, context, site=site)

        return RenderServices.render_html(content_block, context)

    class FakeRequest:
        site = None

        def __init__(self, site):
            self.site = site

    @staticmethod
    def render_html(content_block, context=None, site=None):
        """
        :context: Dictionary of context to render the template with.
        :site: If a Site is supplied and there is no request context set it in the context under request.site
        :return: Rendered html for the content block.
        """
        if not RenderServices.can_render(content_block):
            return ""

        context = RenderServices.context(content_block, context=context)
        request = context.get("request")
        if request is None and site is not None:
            context["request"] = RenderServices.FakeRequest(site)

        html = render_to_string(content_block.template, context, request=request)
        return html

    @staticmethod
    def context(content_block, context=None):
        """
        :return: Context dictionary to be used when rendering html.
        """
        context = context or {}
        context[content_block.context_name] = content_block.context
        context[f"{content_block.context_name}_object"] = content_block
        return context

    @staticmethod
    def site(context):
        """
        :return: The site from the given context if possible.
        """
        request = context.get("request")
        site = getattr(request, "site", None)
        return site

    @staticmethod
    def can_cache(content_block):
        """
        :return: True if cache enabled else False.
        """
        return (
            not settings.CONTENT_BLOCKS_DISABLE_CACHE  # Don't cache if disabled in settings
            and not content_block.content_block_template.no_cache  # Don't cache if the template is marked no_cache
            and not content_block.draft  # Don't cache drafts
            and content_block.parent is None  # Don't cache nested content blocks
        )

    @staticmethod
    def can_render(content_block):
        """
        :return: True if the template exists.
        """
        if not content_block.template:
            return False
        try:
            get_template(content_block.template)
            return True
        except TemplateDoesNotExist:
            return False
