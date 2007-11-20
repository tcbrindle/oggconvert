
import gobject
import gst
from gst.extend import discoverer


class MediaChecker(gobject.GObject):
    __gsignals__= {
		'finished': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
	}
    
    def __init__(self, path):
    
        gobject.GObject.__init__(self)
   
        self.done = False
        self.is_media = False
        self.has_audio = False
        self.has_video = False
        self.mimetype = ""
   
        # Set up Gst elements
        self.pipeline = gst.Pipeline("pipeline")
        self.src = gst.element_make_from_uri(gst.URI_SRC, path, "src")
#        self.src.set_property("location",path)
       
        self.decodebin = gst.element_factory_make("decodebin","dbin")
        
        self.pipeline.add(self.src, self.decodebin)
        self.src.link(self.decodebin)
        
        # Grab the bus
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        
        # Grab the decodebin's typefind element
        self.typefind = self.decodebin.get_by_name("typefind")
        
        # Connect signals
        self.typefind.connect("have-type",self._on_have_type)
        self.decodebin.connect("new-decoded-pad",self._on_new_decoded_pad)
        self.decodebin.connect("unknown-type",self._on_unknown_type)
        self.decodebin.connect("no-more-pads",self._on_no_more_pads)
        self.bus.connect("message::eos",self._on_eos)
        self.bus.connect("message::error",self._on_error)
    
    def __del__(self):
        self.bus.remove_signal_watch()
    
    def _on_have_type(self, typefind, notused, caps):
        self.mimetype = caps.to_string()
    
    def _on_new_decoded_pad(self, dbin, pad, notused):
        
        caps = pad.get_caps()
        pad_type = caps.to_string()[0:5]
        
        if pad_type == "video":
            self.is_media = True
            self.has_video = True
        elif pad_type == "audio":
            self.is_media = True
            self.has_audio = True
        else:
            print "Unknown pad type detected"
        
        # Connect the pad to a fakesink because we get errors otherwise...
        fsink = gst.element_factory_make("fakesink")
        self.pipeline.add(fsink)
        pad.link(fsink.get_pad("sink"))
        
        
    def _on_unknown_type(self, dbin, pad, caps):
        print "Unknown type discovered."
        
    def _on_no_more_pads(self, dbin):
        gobject.idle_add(self._finished)
        
    def _on_eos(self, bus, message):
        print "End of stream message received. This shouldn't happen."
        gobject.idle_add(self._finished)
        
    def _on_error(self, bus, message):
        print "Error message received:"
        error = message.parse_error()
        print error[1]
          
    def _finished(self):
        print "All done!"
        gobject.source_remove(self.timeoutid)
        self.pipeline.set_state(gst.STATE_NULL)
        if not self.done:
            self.emit('finished')
            self.done = True       
        return False
    
    def run(self):
        self.pipeline.set_state(gst.STATE_PAUSED)
        self.timeoutid = gobject.timeout_add(5000, self._finished)
    

        
        
