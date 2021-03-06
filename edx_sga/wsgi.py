"""
WSGI config for edx_sga_t project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

from __future__ import absolute_import

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "edx_sga.test_settings")

application = get_wsgi_application()  # pylint: disable=invalid-name
