=============
Configuration
=============

The following configuration options are available:

``WAGTAIL_SOCIALFEED_CONFIG``
-----------------------------
The configuration for the social media accounts. ::

    WAGTAIL_SOCIALFEED_CONFIG = {
        'twitter': {
            'CONSUMER_KEY': 'SOME_KEY',
            'CONSUMER_SECRET': 'SOME_SECRET',
            'ACCESS_TOKEN_KEY': 'SOME_KEY',
            'ACCESS_TOKEN_SECRET': 'SOME_SECRET'
        },
        'facebook': {
            'CLIENT_ID': 'SOME_ID',
            'CLIENT_SECRET': 'SOME_SECRET',
        }
    }

No credentials are needed for Instagram.

Defaults to ``{}``


``WAGTAIL_SOCIALFEED_CACHE_DURATION``
-------------------------------------

The cache timeout (in seconds) for the social feed items

Defaults to ``900``


``WAGTAIL_SOCIALFEED_SEARCH_MAX_HISTORY``
-----------------------------------------

The amount of time the module is allowed to search through the history of the social feed.
This is only used for the moderator view. In the moderator view it is possible to enter
a search query. For the search to return a usable data-set, multiple result-pages are requested
from the social feed source. But it does need to have a limit.

Defaults to ``timedelta(weeks=26)``
