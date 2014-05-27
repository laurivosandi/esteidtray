
import gobject
from smartcard.ReaderMonitoring import ReaderObserver

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
