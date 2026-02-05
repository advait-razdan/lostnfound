import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lost_and_found_project.settings")

application = get_asgi_application()


