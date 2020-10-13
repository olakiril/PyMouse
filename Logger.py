import numpy, socket, json, os, pandas, pathlib
from utils.Timer import *
from utils.Generator import *
from queue import Queue
import time as systime
from datetime import datetime, timedelta
import threading
from DatabaseTables import *
dj.config["enable_python_native_blobs"] = True


class Logger:
    """ This class handles the database logging"""

    def __init__(self):
        self.curr_trial = 0
        self.queue = Queue()
        self.timer = Timer()
        self.trial_start = 0
        self.curr_cond = []
        self.session_key = dict
        self.setup = socket.gethostname()
        self.lock = True
        self.setup_status = 'ready'
        self.log_setup()
        path = os.path.dirname(os.path.abspath(__file__))
        fileobject = open(path + '/dj_local_conf.json')
        connect_info = json.loads(fileobject.read())
        conn2 = dj.Connection(connect_info['database.host'], connect_info['database.user'],
                              connect_info['database.password'])
        self.insert_schema = dj.create_virtual_module('beh.py', 'lab_behavior', connection=conn2)
        self.thread_end = threading.Event()
        self.thread_lock = threading.Lock()
        self.inserter_thread = threading.Thread(target=self.inserter)  # max insertion rate of 10 events/sec
        self.inserter_thread.start()
        self.getter_thread = threading.Thread(target=self.getter)  # max insertion rate of 10 events/sec
        self.getter_thread.start()

    def cleanup(self):
        self.thread_end.set()

    def inserter(self):
        while not self.thread_end.is_set():
            if self.queue.empty():  time.sleep(.5); continue
            self.thread_lock.acquire()
            item = self.queue.get()
            if 'update' in item:
                eval('(self.insert_schema.'+item['table'] + '() & item["tuple"])._update(item["field"],item["value"])')
            else:
                eval('self.insert_schema.'+item['table']+'.insert1(item["tuple"], ignore_extra_fields=True, skip_duplicates=True)')
            self.thread_lock.release()

    def getter(self):
        while not self.thread_end.is_set():
            self.setup_status = (exp.Control() & dict(setup=self.setup)).fetch1('status')
            time.sleep(1) # update once a second

    def log_setup(self):
        key = dict(setup=self.setup)
        # update values in case they exist
        if numpy.size((exp.Control() & dict(setup=self.setup)).fetch()):
            key = (exp.Control() & dict(setup=self.setup)).fetch1()
            (exp.Control() & dict(setup=self.setup)).delete_quick()

        # insert new setup
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        exp.Control().insert1(dict(key, ip=s.getsockname()[0], status='ready'))

    def log_session(self, session_params, exp_type=''):
        animal_id, protocol_idx = (exp.Control() & dict(setup=self.setup)).fetch1('animal_id', 'protocol_idx')
        self.curr_trial = 0

        # create session key
        self.session_key = dict(animal_id = animal_id,
                                session = numpy.max((Session() & self.session_key).fetch('session'),0) + 1)

        # get task parameters for session table
        key = dict(self.session_key, session_params = session_params, setup = self.setup,
                   protocol = self.get_protocol(), experiment_type = exp_type)
        self.queue.put(dict(table='Session', tuple=key))
        self.update_setup_info('current_session', self.session_key['session'])
        self.update_setup_info('curr_trial', 0)
        self.update_setup_info('total_liquid', 0)
        self.update_setup_info('start_time', session_params['start_time'])
        self.update_setup_info('stop_time', session_params['stop_time'])

        # start session time
        self.timer.start()

    def log_conditions(self, conditions, condition_tables=['Odor', 'Clip', 'Reward']):
        # iterate through all conditions and insert
        for cond in conditions:
            cond_hash = make_hash(cond)
            self.queue.put(dict(table='Condition', tuple=dict(cond_hash=cond_hash, cond_tuple=cond.copy())))
            cond.update({'cond_hash': cond_hash})
            for condtable in condition_tables:
                if condtable == 'Reward' and isinstance(cond['probe'], tuple):
                    for idx, probe in enumerate(cond['probe']):
                        key = {'cond_hash': cond['cond_hash'],
                               'probe': probe,
                               'reward_amount': cond['reward_amount']}
                        self.queue.put(dict(table=condtable, tuple=key))
                else:
                    self.queue.put(dict(table=condtable, tuple=dict(cond.items())))
                    if condtable == 'Odor':
                        for idx, port in enumerate(cond['delivery_port']):
                            key = {'cond_hash': cond['cond_hash'],
                                   'dutycycle': cond['dutycycle'][idx],
                                   'odor_id': cond['odor_id'][idx],
                                   'delivery_port': port}
                            self.queue.put(dict(table=condtable+'.Port', tuple=key))
        return conditions

    def log_condition(self, condition, condition_table='Condition'):
        # iterate through all conditions and insert
        cond_hash = make_hash(condition)
        self.queue.put(dict(table='Condition', tuple=dict(cond_hash=cond_hash, cond_tuple=condition)))


    def init_trial(self, cond_hash):
        self.curr_cond = cond_hash
        self.curr_trial += 1
        if self.lock: self.thread_lock.acquire()
        self.trial_start = self.timer.elapsed_time()
        self.trial_key = dict(self.session_key,
                         trial_idx=self.curr_trial,
                         cond_hash=self.curr_cond,
                         start_time=self.trial_start)
        return self.trial_start # return trial start time

    def init_stim(self, stim_table):
        self.stim_start[stim_table] = self.timer.elapsed_time()

    def log_trial(self, aborted=False):
        timestamp = self.timer.elapsed_time()
        self.queue.put(dict(table='exp.Trial', tuple=dict(self.trial_key, end_time=timestamp, aborted=aborted)))
        if self.lock: self.thread_lock.release()
        self.queue.put(dict(table='exp.Control', tuple=dict(setup=self.setup),
                            field='curr_trial', value=self.curr_trial, update=True))

    def log_liquid(self, probe, reward_amount):
        timestamp = self.timer.elapsed_time()
        self.queue.put(dict(table='Reward.Trial', tuple=dict(self.trial_key, time=timestamp, port=probe,
                                                               reward_amount=reward_amount)))

    def log_stim(self, stim_table):
        self.queue.put(dict(table=stim_table, tuple=dict(self.trial_key, start_time=self.stim_start[stim_table],
                                                         end_time=self.timer.elapsed_time())))

    def log_lick(self, probe):
        timestamp = self.timer.elapsed_time()
        self.queue.put(dict(table='beh.Lick', tuple=dict(self.session_key,
                                                     time=timestamp,
                                                     probe=probe)))
        return timestamp

    def log_pulse_weight(self, pulse_dur, probe, pulse_num, weight=0):
        cal_key = dict(setup=self.setup, probe=probe, date=systime.strftime("%Y-%m-%d"))
        LiquidCalibration().insert1(cal_key, skip_duplicates=True)
        (LiquidCalibration.PulseWeight() & dict(cal_key, pulse_dur=pulse_dur)).delete_quick()
        LiquidCalibration.PulseWeight().insert1(dict(cal_key, pulse_dur=pulse_dur, pulse_num=pulse_num, weight=weight))

    def log_animal_weight(self, weight):
        Mice.MouseWeight().insert1(dict(animal_id=self.get_setup_info('animal_id'), weight=weight))

    def log_position(self, in_position):
        key = dict(self.session_key, timestamp = self.timer.elapsed_time(), port=0, state=in_position)
        self.queue.put(dict(table='beh.PortState', tuple=key))

    def update_setup_info(self, field, value):
        self.queue.put(dict(table='exp.Control', tuple=dict(setup=self.setup), field=field, value=value, update=True))

    def get_setup_info(self, field):
        return (exp.Control() & dict(setup=self.setup)).fetch1(field)

    def get_clip_info(self, key):
        return (stim.Movie() * stim.Movie.Clip() & key & self.session_key).fetch1()

    def get_protocol(self):
        protocol_idx = (exp.Control() & dict(setup=self.setup)).fetch1('protocol_idx')
        protocol = (Task() & dict(protocol_idx=protocol_idx)).fetch1('protocol')
        path, filename = os.path.split(protocol)
        if not path:
            path = pathlib.Path(__file__).parent.absolute()
            protocol = str(path) + '/conf/' + filename
        return protocol

    def ping(self):
        lp = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.queue.put(dict(table='exp.Control', tuple=dict(setup=self.setup),
                            field='last_ping', value=lp, update=True))
        self.queue.put(dict(table='exp.Control', tuple=dict(setup=self.setup),
                            field='queue_size', value=self.queue.qsize(), update=True))


