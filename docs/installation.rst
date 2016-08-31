.. highlight:: shell

============
Installation
============


Stable release
--------------

To install Wagtail Social Feed, run this command in your terminal:

.. code-block:: console

    $ pip install wagtailsocialfeed

This is the preferred method to install Wagtail Social Feed, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for Wagtail Social Feed can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/LUKKIEN/wagtailsocialfeed

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/LUKKIEN/wagtailsocialfeed/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install

Configure Django
----------------

Add ``wagtailsocialfeed`` to your ``INSTALLED_APPS`` in settings:

.. code-block:: python

    INSTALLED_APPS += [
        'wagtailsocialfeed',
    ]


.. _Github repo: https://github.com/LUKKIEN/wagtailsocialfeed
.. _tarball: https://github.com/LUKKIEN/wagtailsocialfeed/tarball/master
