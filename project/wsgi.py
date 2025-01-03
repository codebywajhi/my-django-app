import os
import sys

# Add the virtual environment to the sys.path
# Update this path to your virtual environment location
activate_this = '/var/www/projects/django/my-django-app/venv/bin/activate_this.py'
exec(open(activate_this).read(), dict(__file__=activate_this))

# Add your project to the sys.path
sys.path.append('/var/www/projects/django/my-django-app')

# Set the Django settings module environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
