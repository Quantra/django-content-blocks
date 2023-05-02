from django.core.files.storage import FileSystemStorage


class SettingsTestStorage(FileSystemStorage):
    """
    Test storage for testing that we can change the storage via settings.
    """

    pass
