Introduction
------------

This is a simple smartcard applet that sits in the system tray and shows
whether a smartcard has been plugged in or not.
Right click on the icon reveals the list of smart card readers attached to
the machine and you can optionally have your screen locked when you remove
the smart card.
Main purpose of the applet is to simplify smartcard application debugging 
under Ubuntu, Debian and other Linux distributions.


Features
--------

* Event driven architecture, no naive polling
* Card reader add and remove
* Smartcard insertion, removing and hot reset
* Lock screen via DBus
* The applet is automatically launched via /etc/xdg/autostart


Install
-------

Simply issue following:

.. code::

    sudo pip install esteidtray


TODO
----

* Ubuntu hides tray icons, some sort of new API has to be used there
* Unlock screen, possibly not required because of already existing PAM modules
* Better debuggin capabilities, eg. is pcscd running?
* Use pykcs11 to read certificate and warn user if the certificate is about to expire
* Debianize the package and set it as dependency for estonianidcard at http://packages.koodur.com


Author
------

`Lauri Võsandi <mailto:lauri.vosandi@gmail.com>`_ created this nifty piece of code.


License
-------

Copyright (c) 2014 `Lauri Võsandi <lauri.vosandi@gmail.com>`_
This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.
