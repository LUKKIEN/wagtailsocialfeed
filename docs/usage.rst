=====
Usage
=====

Setting up social feeds
=======================

From the Wagtail CMS settings menu you can access the 'Social feeds' section.
Add social media sources by defining the social media platform, the user to track and define if it's has to be moderated or not

Moderated feeds
===============

When a social feed is marked as 'moderated' by default the latest posts of that feed are not visible to the visitors of your website.
All posts have to be explicitally allowed before it will show up in a feed.

All moderated social feeds will show up as a new item in your CMS admin menu.
From there you will have an overview of all the latest posts, search through the posts and add/remove posts from the moderated list.

.. image:: http://i.imgur.com/REcJPFw.png
   :width: 728 px

Social feed page
================

It's easy to add a page to your tree which shows the latest posts of a specific feed.
When adding a page just choose 'Social Feed Page' and select your feedconfig.

Styling the page
----------------

You can override the default template by creating a ``wagtailsocialfeed/social_feed_page.html`` in your templates directory.
All items are available in the ``{{ feed }}`` variable.

Social feed blocks
==================

You can also render the latest feed posts by using a ``SocialFeedBlock`` in your ``StreamField``.
Make sure you define the ``SocialFeedBlock`` as allowed block-type in the ``StreamField``:

.. code-block:: python
    from wagtailsocialfeed.blocks import SocialFeedBlock

    class YourBlocksPage(Page):
        body = StreamField([
            ...
            ('socialfeed', SocialFeedBlock()),
            ...
        ], null=True, blank=True)

Styling the blocks
------------------

You can override the default template by creating a ``wagtailsocialfeed/social_feed_block.html`` in your templates directory.
All items are available in the ``{{ feed }}`` variable.
