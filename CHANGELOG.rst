=========
CHANGELOG
=========

0.2.0 (xxxx.xx.xx)
==================
+ Added Facebook support
+ Added ability to mix all the feeds; just leave feedconfig empty in `SocialFeedPage` or `SocialFeedBlock`.

0.1.0 (2016.09.27)
==================
+ Fixed PyPI long_description format error
+ Fixed value_for_form error in FeedChooserBlock

0.1.dev4 (2016.09.27)
=====================
+ Made looping over multiple result pages more DRY
+ Improved moderate page title
+ Fixed AttributeError in FeedChooserBlock.value_for_form

0.1.dev3 (2016.09.11)
=====================
+ Updated license model to BSD

0.1.dev2 (2016.09.04)
=====================
+ Added block type 'SocialFeedBlock'
+ Added SocialFeedModerateMenu which live detects configuration changes
+ Added FeedItem to consolidate the item/post structure
+ Added search functionality to the Feed objects
+ Dropped Wagtail 1.5 support in favour of using the IntegerBlock

0.1.dev1 (2016.09.01)
=====================
+ First implementation
