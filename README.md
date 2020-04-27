# django-sharding
Simple horizontal scaling utilities for django framework


# Use guide:
- clone folder sharding and add it to settings.py in INSTALED_APPS
- add your databases and make sure the key of user database is user_1
- add the following settings to settings.py:

DATABASE_MAX_ROWS = 100

DATABASE_ROUTERS = ['sharding.router.ShardingRouter', ]

USER_INIT_DATABASE = 'user_1' # must be the same user database key in DATABASES

SHARDING_USER_MODEL = True

FIXTURE_DIRS = ['sharding.fixtures',]

