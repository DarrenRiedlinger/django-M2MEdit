#!/usr/bin/env python
# Adapted from https://github.com/carljm/django-model-utils/blob/master/runtests.py

import os, sys

from django.conf import settings


if not settings.configured:
    settings_dict = dict(
        INSTALLED_APPS=(
            'django.contrib.sessions',
            'upload',
            'upload.tests',
            'demoapp',
            ),
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3"
                }
            },
        )

    settings.configure(**settings_dict)


def runtests(*test_args):
    if not test_args:
        test_args = ['tests']

    parent = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, parent)

    from django.test.simple import DjangoTestSuiteRunner
    failures = DjangoTestSuiteRunner(
        verbosity=1, interactive=True, failfast=False).run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    runtests()
