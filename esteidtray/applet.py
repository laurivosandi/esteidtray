#!/usr/bin/env python
# coding: utf-8 
 
# apt-get install python-pyscard python-dbus

import os
import dbus
from gettext import gettext as _
from smartcard.scard import *
from smartcard.pcsc.PCSCExceptions import *
import gtk
import gobject
gobject.threads_init()

PCSCD = "/usr/sbin/pcscd"
QESTEIDUTIL = "/usr/bin/qesteidutil"


def psaux():
    for pid in os.listdir("/proc"):
        try:
            pid = int(pid)
        except ValueError: # Not a pid
            continue
        s = os.stat("/proc/%d" % pid)
        try:
            exe = os.readlink("/proc/%d/exe" % pid)
        except OSError: # Permission denied
            continue
        cmdline = open("/proc/%d/cmdline" % pid).read()
        cmdline = cmdline.split("\x00")[:-1]
        environment = open("/proc/%d/environ" % pid).read()
        environment = dict([i.split("=", 1) for i in environment.split("\x00")[:-1]])
        yield pid, s.st_uid, s.st_gid, exe, cmdline, environment

from smartcard.ReaderMonitoring import ReaderMonitor, ReaderObserver
from smartcard.CardMonitoring import CardMonitor, CardObserver

class GReaderObserver(ReaderObserver, gobject.GObject):
    """
    Adapt ReadObserver for GTK
    """
    
    __gsignals__ =  { 
        "cardreader_added":    (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        "cardreader_removed":  (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
    }

    def __init__(self):
        ReaderObserver.__init__(self)
        gobject.GObject.__init__(self)
        
    def emit(self, *args):
        gobject.idle_add(gobject.GObject.emit, self, *args)
        
    def update( self, observable, (added_readers, removed_readers) ):
        for reader in added_readers:
            self.emit("cardreader_added", reader)
        for reader in removed_readers:
            self.emit("cardreader_removed", reader)
            
class GCardObserver(CardObserver, gobject.GObject):
    """
    Adapt CardObserver for GTK
    """
    __gsignals__ =  { 
        "smartcard_inserted":     (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        "smartcard_switched": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        "smartcard_removed":      (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING])
    }
    
    def __init__(self):
        CardObserver.__init__(self)
        gobject.GObject.__init__(self)
        
    def emit(self, *args):
        gobject.idle_add(gobject.GObject.emit, self, *args)
    
    def update( self, observable, (added_cards, removed_cards) ):
        for added_card in added_cards:
            for removed_card in removed_cards:
                if added_card.reader == removed_card.reader:
                    self.emit("smartcard_switched", added_card.reader) #, card.atr)
                    break
            else:
                self.emit("smartcard_inserted", added_card.reader) #, card.atr)

        for removed_card in removed_cards:
            for added_card in added_cards:
                if added_card.reader == removed_card.reader:
                    break
            else:
                self.emit("smartcard_removed", removed_card.reader) #, card.atr)

class SmartcardApplet():
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
            item.set_image(gtk.image_new_from_file("smartcard-present.png"))
            item.set_tooltip_text(_("Smartcard present"))
            self.tray_icon.set_from_file("applet.svg")
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
        self.tray_icon.set_from_file("applet-problem.svg")
        
        print "Smartcard removed:", reader_name
        try:
            item  = self.get_reader_item(reader_name)
            item.set_image(None)
            #item.set_image(gtk.image_new_from_file(IMAGE_CARD_REMOVED_SMALL))
            item.set_tooltip_text(_("Smartcard absent"))
        except ListReadersException:
            print "This should not happen"
            
        if self.lock_screen.get_active():
            for dbus_name in ("org.gnome.ScreenSaver", "org.freedesktop.ScreenSaver", "org.mate.ScreenSaver"):
                try:
                    screensaver = self.session_bus.get_object(dbus_name, "/ScreenSaver")
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
                        path="/ScreenSaver",
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
        
    def __init__(self):
        self.session_bus = dbus.SessionBus()
        self.reader_observer = GReaderObserver()
        self.card_observer = GCardObserver()
        
        
        self.tray_icon = gtk.status_icon_new_from_file("applet-problem.svg")
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
        
#        lock_screen.connect("toggled", toggle_lock_screen)

        close_item = gtk.MenuItem(_("Close"))

        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.lock_screen)
        self.menu.append(close_item)

        close_item.connect_object("activate", gtk.main_quit, "Close App")
        self.menu.show_all()

 
 

 
 
    def on_right_click(self, data, event_button, event_time):
        self.menu.popup(None, None, None, event_button, event_time)
 
    def on_left_click(self, event):
        os.system("%s &" % QESTEIDUTIL)

if __name__ == '__main__':
    print u"Smartcard monitor applet by Lauri Võsandi <lauri.vosandi@gmail.com>"
    if not os.path.exists(PCSCD):
        print "Unable to find", PCSCD, "are you sure it is installed"
#    for pid, uid, gid, exe, cmdline, environment in psaux():
#        print exe, PCSCD
#        if exe == PCSCD:
#            print "Found pcscd running (pid=%d)" % pid
#            break
#    else:
#        print "No pcscd running!"
        
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


