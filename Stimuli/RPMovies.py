from .RPScreen import *
import os
from time import sleep

class RPMovies(RPScreen):
    """ This class handles the presentation of Movies with an optimized library for Raspberry pi"""


    def log_conditions(self, conds):
        params = ['clip_number',
                  'movie_duration',
                  'skip_time',
                  'static_frame']
        for key in conds:
            res = dict((k, key[k]) for k in params if k in key)
            self.logger.log

    def setup(self):
        # setup parameters
        super(RPScreen,self).setup()

        # setup movies
        self.path = 'stimuli/'     # default path to copy local stimuli
        from omxplayer import OMXPlayer
        self.player = OMXPlayer
        # store local copy of files
        if not os.path.isdir(self.path):  # create path if necessary
            os.makedirs(self.path)
        for cond in self.conditions:
            clip_info = self.logger.get_clip_info(cond)
            filename = self.path + clip_info['file_name']
            if not os.path.isfile(filename):
                print('Saving %s ...' % filename)
                clip_info['clip'].tofile(filename)
        # initialize player
        self.vid = self.player(filename, args=['--aspect-mode', 'stretch', '--no-osd'],
                    dbus_name='org.mpris.MediaPlayer2.omxplayer1')
        self.vid.stop()

    def prepare(self):
        self._get_new_cond()
        self._init_player()

    def init(self):
        self.isrunning = True
        try:
            self.vid.play()
        except:
            self._init_player()
            self.vid.play()
        if self.curr_cond['static_frame']:
            sleep(0.2)
            self.vid.pause()
        self.timer.start()
        self.logger.init_stim('Clip.Trial')

    def present(self):
        if self.timer.elapsed_time() > self.curr_cond['movie_duration']:
            self.isrunning = False
            self.vid.quit()

    def stop(self, color=False):
        try:
            self.vid.stop()
        except:
            self._init_player()
            self.vid.stop(color)
        self.logger.log_stim()
        self.set_background()
        self.isrunning = False

    def _init_player(self):
        clip_info = self.logger.get_clip_info(self.curr_cond)
        self.filename = self.path + clip_info['file_name']
        try:
            self.vid.load(self.filename)
        except:
            self.vid = self.player(self.filename, args=['--aspect-mode', 'stretch', '--no-osd'],
                        dbus_name='org.mpris.MediaPlayer2.omxplayer1')
        self.vid.pause()
        self.vid.set_position(self.curr_cond['skip_time'])

    def close(self):
        """Close stuff"""
        pygame.mouse.set_visible(1)
        pygame.display.quit()
        pygame.quit()

