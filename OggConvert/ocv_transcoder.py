#
# OggConvert -- Converts media files to Free formats
# (c) 2007 Tristan Brindle <tcbrindle at gmail dot com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import gobject
import pygst
pygst.require("0.10")
import gst
import ocv_constants

class Transcoder(gobject.GObject):

    __gsignals__ = {
            'paused' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
            'playing' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
            'eos' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
        }


    def __init__(self, inuri, outuri, vformat, vquality, aquality, fformat):
    
        gobject.GObject.__init__(self)
    
        self._infile = inuri
        self._outfile = outuri
        self._vformat = vformat
        if self._vformat == "THEORA":
            self._vquality = ocv_constants.THEORA_QUALITY_MAPPING[vquality]
        elif self._vformat == "SCHRO":
            self._vquality = ocv_constants.SCHRO_QUALITY_MAPPING[vquality]
        elif self._vformat == "VP8":
            self._vquality = ocv_constants.VP8_QUALITY_MAPPING[vquality]
        else:
            # We should never get here
            self._vquality = 0
        self._aquality = ocv_constants.VORBIS_QUALITY_MAPPING[aquality]
        self._fformat = fformat

        self._pipeline = gst.Pipeline()
        
        #self._filesrc = gst.element_factory_make("filesrc")
        #self._filesrc.set_property("location", self._infile)
        self._filesrc = gst.element_make_from_uri(gst.URI_SRC, inuri)
        
        self._decodebin = gst.element_factory_make("decodebin")
        self._decodebin.connect("new-decoded-pad", self._on_new_pad)

        if fformat == "OGG":
            self._mux = gst.element_factory_make("oggmux")
            for key in ocv_constants.OGGMUX_OPTS:
                self._mux.set_property(key, ocv_constants.OGGMUX_OPTS[key])
        else:
            self._mux = gst.element_factory_make("matroskamux")
            for key in ocv_constants.MATROSKAMUX_OPTS:
                self._mux.set_property(key, ocv_constants.MATROSKAMUX_OPTS[key])

        self._progreport = gst.element_factory_make("progressreport")
        
        #self._filesink = gst.element_factory_make("filesink")
        #self._filesink.set_property("location", outfile)
        self._filesink = gst.element_make_from_uri(gst.URI_SINK, outuri)
        
        
        self._pipeline.add(self._filesrc, 
                           self._decodebin, 
                           self._mux, 
                           self._progreport, 
                           self._filesink)

        # Link up what we've got so far
        self._filesrc.link(self._decodebin)
        self._mux.link(self._progreport)
        self._progreport.link(self._filesink)
        
        # Connect up callbacks
        self.bus = self._pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message::eos",self._on_end_of_stream)
        self.bus.connect("message::state-changed", self._on_state_changed)

    def play(self):
        self._pipeline.set_state(gst.STATE_PLAYING)
        
    def pause(self):
        self._pipeline.set_state(gst.STATE_PAUSED)
        
    def stop(self):   
        self.bus.remove_signal_watch()
        self._pipeline.set_state(gst.STATE_NULL) 
        
        
    def sync(self):
        """ 
        Wait for the pipeline to change state
        We give it a 3 second timeout: returns True if the state change was
        successful in this time, False otherwise
        """
        
        state = self._pipeline.get_state(timeout=3*gst.SECOND)[0]
        if state == gst.STATE_CHANGE_SUCCESS:
            return True
        else:
            return False
    
    
    def get_position(self):
        try:    
            return self._pipeline.query_position(gst.FORMAT_TIME)[0]
        except gst.QueryError:
            return None
        
    def get_duration(self):
        try:
            return self._pipeline.query_duration(gst.FORMAT_TIME)[0]
        except gst.QueryError:
            return None
        
    def _on_new_pad(self, element, pad, args):
        caps = pad.get_caps()
        pad_type = caps.to_string()[0:5]
        if pad_type == "video":
            encoder = VideoEncoder(self._vformat, self._vquality)
            self._pipeline.add(encoder)
            encoder.set_state(gst.STATE_PAUSED)
            pad.link(encoder.get_pad("sink"))
            encoder.link(self._mux)
        elif pad_type == "audio":
            encoder = AudioEncoder(self._aquality)
            self._pipeline.add(encoder)
            encoder.set_state(gst.STATE_PAUSED)
            pad.link(encoder.get_pad("sink"))
            encoder.link(self._mux)
        else:
            print "Unknown pad type detected, %s" %pad_type
      
    def _on_end_of_stream(self, bus, message):
        self.emit('eos')
        
    def _on_state_changed(self, bus, message):
        
        if  (message.src == self._pipeline):
            state = message.parse_state_changed()
            
            if state[1] == gst.STATE_PAUSED:
                self.emit('paused')
            elif state[1] == gst.STATE_PLAYING:
                self.emit('playing')
            
        
        
class VideoEncoder(gst.Bin):
    def __init__(self, format, quality):
        gst.Bin.__init__(self)
        self._queue1 = gst.element_factory_make("queue")
        self._queue1.set_property("max-size-buffers",500)
        self._queue2 = gst.element_factory_make("queue")
        self._queue1.set_property("max-size-buffers",500)
        self._ffmpegcsp = gst.element_factory_make("ffmpegcolorspace")
        self._videorate = gst.element_factory_make("videorate")
        
        if format == "SCHRO":
            self.encoder = gst.element_factory_make("schroenc")
            for prop in ocv_constants.SCHRO_OPTS:
                self.encoder.set_property(prop, ocv_constants.SCHRO_OPTS[prop])
                self.encoder.set_property("quality", quality)
        elif format == "VP8":
            self.encoder = gst.element_factory_make("vp8enc")
            for prop in ocv_constants.VP8_OPTS:
                self.encoder.set_property(prop, ocv_constants.VP8_OPTS[prop])
                self.encoder.set_property("quality", quality)
        else:
            self.encoder = gst.element_factory_make("theoraenc")
            for prop in ocv_constants.THEORA_OPTS:
                self.encoder.set_property(prop, ocv_constants.THEORA_OPTS[prop])            
            self.encoder.set_property("quality", quality)
        
        self.add(self._queue1, 
                     self._ffmpegcsp,
                     self._videorate,
                     self.encoder,
                     self._queue2)
        
        gst.element_link_many(self._queue1,
                              self._ffmpegcsp,
                              self._videorate,
                              self.encoder,
                              self._queue2)
        
        # Create GhostPads
        self.add_pad(gst.GhostPad('sink', self._queue1.get_pad('sink')))
        self.add_pad(gst.GhostPad('src', self._queue2.get_pad('src')))
        
        
        
        
class AudioEncoder(gst.Bin):
    def __init__(self, quality):
        gst.Bin.__init__(self)
        self._queue1 = gst.element_factory_make("queue")
        self._queue1.set_property("max-size-buffers",500)
        self._queue2 = gst.element_factory_make("queue")
        self._queue2.set_property("max-size-buffers",500)        
        self._audioconvert = gst.element_factory_make("audioconvert")
        
        # Vorbisenc can't handle packets without timestamps very well.
        # This means that certain demuxers (asfdemux and matroskademux for 
        # example, but also most of the ffdemux elements) will generate 
        # very choppy audio. 
        #
        # Fortunately GStreamer includes an audiorate element which can fix up
        # such broken streams, by putting the right timestamps on and so forth.
        # Unfortunately the audiorate element is broken in 0.10.10, to the extent
        # that the pipeline won't even preroll. Therefore we check the GStreamer
        # version (in __init__.py) to decide whether to use it or not. If you want
        # to override this checking for any reason, you can do so by editing
        # ocv_constants.py
        
        if ocv_constants.USE_AUDIORATE:
            self._audiorate = gst.element_factory_make("audiorate")
        else:
            self._audiorate = gst.element_factory_make("identity")
            
            
        self.encoder = gst.element_factory_make("vorbisenc")
        
        # Set Vorbis options
        for prop in ocv_constants.VORBIS_OPTS:
            self.encoder.set_property(prop, ocv_constants.VORBIS_OPTS[prop])
        
        self.encoder.set_property("quality", quality)
        
        self.add(self._queue1, 
                     self._audioconvert,
                     self._audiorate,
                     self.encoder,
                     self._queue2)

        gst.element_link_many(self._queue1,
                              self._audioconvert, 
                              self._audiorate, 
                              self.encoder,
                              self._queue2)
        
        # Create GhostPads
        self.add_pad(gst.GhostPad('sink', self._queue1.get_pad('sink')))
        self.add_pad(gst.GhostPad('src', self._queue2.get_pad('src')))
        


        
