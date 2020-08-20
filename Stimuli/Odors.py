from Stimulus import *


class Odors(Stimulus):
    """ This class handles the presentation of Odors"""

    def log_conditios(self):
        return ['Odor', 'Reward']
        for idx, port in enumerate(cond['delivery_port']):
            key = {'cond_hash': cond['cond_hash'],
                   'dutycycle': cond['dutycycle'][idx],
                   'odor_id': cond['odor_id'][idx],
                   'delivery_port': port}
            self.queue.put(dict(table=condtable + '.Port', tuple=key))

    def setup(self):
        # setup parameters
        self.size = (800, 480)     # window size
        self.color = [10, 10, 10]  # default background color

        # setup pygame
        pygame.init()
        self.screen = pygame.display.set_mode(self.size)
        self.unshow()
        pygame.display.toggle_fullscreen()

    def init(self):
        delivery_port = self.curr_cond['delivery_port']
        odor_id = self.curr_cond['odor_id']
        odor_dur = self.curr_cond['odor_duration']
        odor_dutycycle = self.curr_cond['dutycycle']
        self.beh.give_odor(delivery_port, odor_id, odor_dur, odor_dutycycle)
        self.isrunning = True
        self.timer.start()

    def prepare(self):
        self._get_new_cond()

    def unshow(self, color=False):
        """update background color"""
        if not color:
            color = self.color
        self.screen.fill(color)
        
    def stop(self):
        self.logger.log_stim()
        self.isrunning = False

    def close(self):
        """Close stuff"""
        pygame.mouse.set_visible(1)
        pygame.display.quit()
        pygame.quit()
