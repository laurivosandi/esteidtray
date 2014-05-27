#!/usr/bin/env python
# coding: utf-8 
 
# apt-get install python-pyscard python-dbus

import os
import dbus
from gettext import gettext as _
from smartcard.scard import *
from smartcard.pcsc.PCSCExceptions import *
from smartcard.ReaderMonitoring import ReaderMonitor
from smartcard.CardMonitoring import CardMonitor
from greaderobserver import GReaderObserver
from gcardobserver import GCardObserver
import gtk
import gobject

gobject.threads_init()

DBUS_SCREENSAVERS = (
    ("org.gnome.ScreenSaver",         "/org/gnome/ScreenSaver"),
    ("org.freedesktop.ScreenSaver",   "/ScreenSaver"),
    ("org.mate.ScreenSaver",          "/ScreenSaver")
)

ICON_ROOT = os.path.join(os.path.dirname(__file__), "icons")

ICON_APPLET_OKAY = os.path.join(ICON_ROOT, "applet.svg")
ICON_APPLET_PROBLEM = os.path.join(ICON_ROOT, "applet-problem.svg")
ICON_SMARTCARD_PRESENT = os.path.join(ICON_ROOT, "smartcard-present.png")

PCSCD = "/usr/sbin/pcscd"
QESTEIDUTIL = "/usr/bin/qesteidutil"

class SmartcardApplet():
    def __init__(self):
        self.session_bus = dbus.SessionBus()
        self.reader_observer = GReaderObserver()
        self.card_observer = GCardObserver()
        
        
        self.tray_icon = gtk.status_icon_new_from_file(ICON_APPLET_PROBLEM)
        self.tray_icon.connect('popup-menu', self.on_right_click)
        self.tray_icon.connect('activate', self.on_left_click)

        self.menu = gtk.Menu()
        
        self.reader_observer.connect("cardreader_added", self.on_cardreader_added)
        self.reader_observer.connect("cardreader_removed", self.on_cardreader_removed)
        self.card_observer.connect("smartcard_inserted", self.on_smartcard_inserted)
        self.card_observer.connect("smartcard_switched", self.on_smartcard_switched)
        self.card_observer.connect("smartcard_removed", self.on_smartcard_removed)

            
        self.lock_screen = gtk.CheckMenuItem(_("Lock screen"))
        self.lock_screen.set_tooltip_text(_("Lock screen when card is removed"))
        
        close_item = gtk.MenuItem(_("Close"))

        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.lock_screen)
        self.menu.append(close_item)

        close_item.connect_object("activate", gtk.main_quit, "Close App")
        self.menu.show_all()

    def get_reader_item(self, reader_name):
        for child in self.menu.children():
            if child.get_data("fully_qualified_name") == reader_name:
                return child
        raise ListReadersException("No such smart card reader: %s" % reader_name)
    
    def on_cardreader_added(self, source, reader_name):
        print "Cardreader added:", reader_name

        title = reader_name[:-5] # Omit bus number/slot number
        if "(" in title: title, tail = title.split("(", 1)
        if "[" in title: title, tail = title.split("[", 1)

        reader_item = gtk.ImageMenuItem(title.strip())
        reader_item.set_data("fully_qualified_name", reader_name)
        reader_item.show()
        self.menu.prepend(reader_item)
        
        
    def on_cardreader_removed(self, source, reader_name):
        print "Cardreader removed:", reader_name
        try:    
            self.get_reader_item(reader_name).destroy()
        except ListReadersException:
            print "This should not happen"

        
    def on_smartcard_inserted(self, source, reader_name):
        print "Smartcard inserted:", reader_name
        try:    
            item  = self.get_reader_item(reader_name)
            item.set_image(gtk.image_new_from_file(ICON_SMARTCARD_PRESENT))
            item.set_tooltip_text(_("Smartcard present"))
            self.tray_icon.set_from_file(ICON_APPLET_OKAY)
        except ListReadersException:
            print "This should not happen"
            
    def on_smartcard_switched(self, source, reader_name):
        print "Smartcard switched:", reader_name
        try:    
            item  = self.get_reader_item(reader_name)
            item.set_tooltip_text(_("Smartcard present"))
        except ListReadersException:
            print "This should not happen"

        
    def on_smartcard_removed(self, source, reader_name):
        self.tray_icon.set_from_file(ICON_APPLET_PROBLEM)
        
        print "Smartcard removed:", reader_name
        try:
            item  = self.get_reader_item(reader_name)
            item.set_image(None)
            item.set_tooltip_text(_("Smartcard absent"))
        except ListReadersException:
            print "This should not happen"
            
        if self.lock_screen.get_active():
            for dbus_name, dbus_path in DBUS_SCREENSAVERS:
                try:
                    screensaver = self.session_bus.get_object(dbus_name, dbus_path)
                except dbus.exceptions.DBusException:
                    print "No such DBus object:", dbus_name
                    continue
                else:
                    print "Found screensaver object:", dbus_name
                    # Following is waiting for reply for some reason?!
        #            interface = dbus.Interface(screensaver, dbus_name)
        #            interface.Lock()
                    msg = dbus.lowlevel.MethodCallMessage(
                        destination=dbus_name,
                        path=dbus_path,
                        interface=dbus_name,
                        method='Lock')
                    # Don't expect for reply, at least mate-screensaver does
                    msg.set_no_reply (True)
                    self.session_bus.send_message(msg)
                    break
            else:
                print "Did not find screensaver DBus object, don't know how to lock desktop"
        else:
            print "Not going to lock screen"
        
    def on_right_click(self, data, event_button, event_time):
        self.menu.popup(None, None, None, event_button, event_time)
 
    def on_left_click(self, event):
        os.system("%s &" % QESTEIDUTIL)


def entry_point():        
    print u"Smartcard monitor applet by Lauri Võsandi <lauri.vosandi@gmail.com>"
    if not os.path.exists(PCSCD):
        print "Unable to find", PCSCD, "are you sure it is installed"
        
    applet = SmartcardApplet()
    reader_monitor = ReaderMonitor()
    reader_monitor.addObserver(applet.reader_observer)
    card_monitor = CardMonitor()
    card_monitor.addObserver(applet.card_observer)
    try:
        gtk.main()
    except KeyboardInterrupt:
        pass
    card_monitor.deleteObserver(applet.card_observer)
    reader_monitor.deleteObserver(applet.reader_observer)


if __name__ == '__main__':
    entry_point()

