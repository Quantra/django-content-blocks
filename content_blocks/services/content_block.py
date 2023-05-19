from django.core.cache import caches
from django.template.loader import render_to_string

from content_blocks.conf import settings
from content_blocks.services.content_block_parent import ParentServices

# Get the appropriate cache.  Any cache use should import from here.
cache = caches[settings.CONTENT_BLOCKS_CACHE]


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
    def cacheable(queryset):
        """
        Take a queryset of ContentBlock and filter to draft=False then filter by renderable.
        The resultant queryset reflects the constraints in CacheServices.can_cache().
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

        try:
            cache_key = f"{cache_key}_site_{site.id}"
        except AttributeError:
            pass

        return cache_key

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
        if not CacheServices.can_cache(content_block):
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
            content_blocks = ContentBlockFilters.cacheable(obj.content_blocks.all())

            for content_block in content_blocks:
                if CacheServices.can_cache(content_block):
                    # Early bail out if this shouldn't be cached.
                    CacheServices.get_or_set_cache_per_site(content_block, sites)

    @staticmethod
    def get_or_set_cache_published():
        """
        Get or set the cache for all published content blocks.
        Used to prepopulate the cache in app.ready()
        """
        if settings.CONTENT_BLOCKS_DISABLE_CACHE:
            return

        models = ParentServices.parent_models()

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
            content_blocks = ContentBlockFilters.cacheable(obj.content_blocks.all())

            for content_block in content_blocks:
                CacheServices.delete_cache_per_site(content_block, sites)

    @staticmethod
    def delete_cache_all():
        """
        Delete the cache for all content blocks on a per-site basis.
        Used to delete the cache via the content_blocks_clear_cache management command.
        """
        if settings.CONTENT_BLOCKS_DISABLE_CACHE:
            return  # pragma: no cover (covered by settings tests)

        models = ParentServices.parent_models()

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
            content_blocks = ContentBlockFilters.cacheable(obj.content_blocks.all())

            if queryset is not None:
                queryset = ContentBlockFilters.cacheable(queryset)
                content_blocks = ContentBlockFilters.content_blocks_in_queryset(
                    content_blocks, queryset
                )

            for content_block in content_blocks:
                CacheServices.update_cache_per_site(content_block, sites)

    @staticmethod
    def update_cache_all(queryset=None):
        """
        Update the cache for all content blocks on a per-site basis.
        Used by content_blocks_update_cache management command.
        :param queryset: ContentBlock queryset to limit the update to.
        """
        if settings.CONTENT_BLOCKS_DISABLE_CACHE:
            return

        models = ParentServices.parent_models()

        for model in models:
            CacheServices.update_cache_parent_model(model, queryset=queryset)

    @staticmethod
    def update_cache_content_block(content_block, content_block_parent):
        """
        Update the cache for a content block across all sites given its parent.
        """
        sites = ParentServices.parent_sites(content_block_parent)
        CacheServices.update_cache_per_site(content_block, sites)

    @staticmethod
    def can_cache(content_block):
        """
        :return: True if cache enabled and the content block is eligible for cacheing else False.
        """
        return (
            not settings.CONTENT_BLOCKS_DISABLE_CACHE  # Don't cache if disabled in settings
            and content_block.can_render  # Can't cache what can't be rendered
            and not content_block.draft  # Don't cache drafts
            and content_block.parent is None  # Don't cache nested content blocks
            and not content_block.content_block_template.no_cache  # Don't cache if the template is marked no_cache
        )


class RenderServices:
    @staticmethod
    def render_content_block(content_block, context=None):
        """
        Main render method.  Used by ContentBlock.render and {% render_content_block %}
        :return: Rendered html for the content block.
        """
        context = RenderServices.context(content_block, context=context)
        site = RenderServices.site(context)

        if CacheServices.can_cache(content_block):
            return CacheServices.get_or_set_cache(content_block, context, site=site)

        return RenderServices.render_html(content_block, context)

    class DummyRequest:
        """
        DummyRequest to hold a site attribute. In no other way similar to an actual request.
        """

        def __init__(self, site):
            self.site = site

    @staticmethod
    def render_html(content_block, context=None, site=None):
        """
        :context: Dictionary of context to render the template with.
        :site: If a Site is supplied and there is no request context set it in the context under request.site
        :return: Rendered html for the content block.
        """
        if not content_block.can_render:
            return ""

        context = RenderServices.context(content_block, context=context)
        request = context.get("request")
        if request is None and site is not None:
            context["request"] = RenderServices.DummyRequest(site)

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
