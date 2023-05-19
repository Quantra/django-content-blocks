from django.core.management import BaseCommand

from content_blocks.services.content_block import CacheServices


class Command(BaseCommand):
    help = "Clear content blocks cache"

    def handle(self, *args, **options):
        verbosity = int(options["verbosity"])

        CacheServices.delete_cache_all()

        if verbosity > 0:
            self.stdout.write("Content blocks cache cleared")  # pragma: no cover
