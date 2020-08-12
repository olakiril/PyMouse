from .RPMovies import *
from .Odors import *
from time import sleep


class SmellyMovies(RPMovies, Odors):
    """ This class handles the presentation of Visual (movies) and Olfactory (odors) stimuli"""

    def get_condition_tables(self):
        return ['Clip', 'Odor', 'Reward']
  
    def init(self):
        delivery_port = self.curr_cond['delivery_port']
        odor_id = self.curr_cond['odor_id']
        odor_dur = self.curr_cond['odor_duration']
        odor_dutycycle = self.curr_cond['dutycycle']
        self.isrunning = True
        self.vid.play()
        if self.curr_cond['static_frame']:
            sleep(0.2)
            self.vid.pause()
        self.beh.give_odor(delivery_port, odor_id, odor_dur, odor_dutycycle)
        self.timer.start()
        self.logger.log_stim()



