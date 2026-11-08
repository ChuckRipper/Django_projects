"""Test runner: quiet logs and fast password hashing.

Many tests trigger errors on purpose (400, 403, 404, 405, CSRF...) to check how the
application reacts. Django logs each of them, which floods the console with warnings and
tracebacks although every test passes. During tests these loggers only report CRITICAL
problems; tests that check logging use assertLogs, which still works (it lowers the level
for its own block). MD5 hashing makes creating test users ~100x faster - test only!
"""

import logging

from django.conf import settings
from django.test.runner import DiscoverRunner

QUIET_LOGGERS = ("django.request", "django.security")


class QuietTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
        self._levels = {}
        for name in QUIET_LOGGERS:
            logger = logging.getLogger(name)
            self._levels[name] = logger.level
            logger.setLevel(logging.CRITICAL)

    def teardown_test_environment(self, **kwargs):
        for name, level in self._levels.items():
            logging.getLogger(name).setLevel(level)
        super().teardown_test_environment(**kwargs)
