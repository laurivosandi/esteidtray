
import gobject
from smartcard.CardMonitoring import CardObserver
            
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

