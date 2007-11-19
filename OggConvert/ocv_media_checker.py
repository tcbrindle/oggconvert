
import gobject
import gst
from gst.extend import discoverer


class MediaChecker(gobject.GObject):
    __gsignals__= {
		'finished': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
	}
    
    def __init__(self, path):
    
        gobject.GObject.__init__(self)
    
        self.is_media = False
        self.is_video = False
        self.mimetype = None
    
        self.disc = discoverer.Discoverer(path)
        self.disc.connect("discovered", self.discovered)
    
    def run(self):
        self.disc.discover()
        self.main_loop = gobject.MainLoop()
        self.main_loop.run()
    
    def discovered(self, disc, is_media):
        if is_media:
            self.is_media = True
            self.has_video = disc.is_video
            self.has_audio = disc.is_audio
            disc.print_info()
            self.main_loop.quit()
            self.emit("finished")
        else:
            self.is_media = False
            self.mimetype = disc.mimetype
            self.main_loop.quit()
            self.emit("finished")

        
        
