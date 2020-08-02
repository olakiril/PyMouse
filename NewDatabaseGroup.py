import datajoint as dj

ExpSchema = dj.schema('test_experiment')
BehSchema = dj.schema('test_behavior')
StimSchema = dj.schema('test_stimuli')
Mice = dj.create_virtual_module('mice.py', 'lab_mice')


def erd():
    """for convenience"""
    dj.ERD(schema).draw()


@ExpSchema
class Protocol(dj.Lookup):
    definition = """
    # Behavioral experiment parameters
    protocol_idx         : int                          # task identification number
    ---
    protocol_file        : varchar(4095)                # stimuli to be presented (array of dictionaries)
    description=""       : varchar(2048)                # task description
    timestamp            : timestamp    
    """

@ExpSchema
class SetupControl(dj.Lookup):
    definition = """
    #
    setup                : varchar(256)                 # Setup name
    ---
    ->Protocol
    ip                   : varchar(16)                  # setup IP address
    status="ready"       : enum('ready','running','stop','sleeping','offtime','exit') 
    animal_id=null       : int                          # animal id
    last_ping            : timestamp                    
    notes=null           : varchar(256)                 
    current_session=null : int                          
    last_trial=null      : int                          
    total_liquid=null    : float     
    state=null           : varchar(256)  
    """

@ExpSchema
class Session(dj.Manual):
    definition = """
    # Behavior session infod
    animal_id            : int                          # animal id
    session              : smallint                     # session number
    ---
    setup=null           : varchar(256)                 # computer id
    notes=null           : varchar(2048)                # session notes
    session_params=null  : mediumblob                   
    protocol=null        : varchar(256)                 # protocol file
    experiment_type=null : varchar(256)            
    session_tmst         : timestamp                    # session timestamp     
    """

@ExpSchema
class Condition(dj.Manual):
    definition = """
    # unique stimulus conditions
    cond_hash             : char(24)                    # unique condition hash
    ---
    cond_tuple=null       : blob      
    """

@ExpSchema
class Trial(dj.Manual):
    definition = """
    # Trial information
    -> Session
    trial_idx            : smallint                     # unique condition index
    ---
    -> Condition
    start_time           : int                          # start time from session start (ms)
    end_time             : int                          # end time from session start (ms)
    """



@BehSchema
class CenterPort(dj.Manual):
    definition = """
    # Center port information
    -> Session
    time	     	     : int                      	# time from session start (ms)
    ---
    in_position          : boolean
    """

@BehSchema
class Lick(dj.Manual):
    definition = """
    # Lick timestamps
    -> Session
    time	          	: int           	            # time from session start (ms)
    port                : int                           # port number
    """



@StimSchema
class Clip(dj.Manual):
    definition = """
    # movie clip conditions
    mov_hash             : char(24)                     # unique condition hash
    ---
    movie_name           : char(8)                      # short movie title
    clip_number          : int                          # clip index
    movie_duration       : int                          # movie duration
    skip_time            : smallint                     # start time in clip
    static_frame         : smallint                     # static frame presentation
    """

    class Trial(dj.Part):
        definition = """
        # Stimulus onset timestamps
        -> Trial
        ---
        -> Clip
        start_time          : int                       # start time from session start (ms)
        end_time            : int                       # end time from session start (ms)
        """

@StimSchema
class Odor(dj.Manual):
    definition = """
    # odor conditions
    odor_hash                : char(24)                 # unique condition hash
    """

    class Channel(dj.Part):
        definition = """
        # odor conditions
        -> Odor
        odorant_id           : int                      # index for odorant identity
        ---
        duration             : int                      # odor duration (ms)
        delivery_channel     : int                      # delivery idx for channel mapping
        mix            : int                      # odorant ratio in the mixture(0-100)
        """

    class Trial(dj.Part):
        definition = """
        # Stimulus onset timestamps
        -> Trial
        ---
        -> Odor
        start_time          : int                        # start time from session start (ms)
        end_time            : int                        # end time from session start (ms)
        """

@StimSchema
class Reward(dj.Manual):
    definition = """
    # reward probe conditions
    rew_hash               : char(24)                     # unique reward hash
    ---
    port=0                 : int                          # delivery port
    reward_amount=0        : float                        # reward amount
    reward_type='water'    : enum('water','juice','food') # reward type
    """

    class Trial(dj.Part):
        definition = """
        # movie clip conditions
        -> Trial
        ---
        -> Reward
        time			      : int 	                # time from session start (ms)
        """

@StimSchema
class LiquidCalibration(dj.Manual):
    definition = """
    # Liquid delivery calibration sessions for each probe
    setup                        : varchar(256)         # Setup name
    port                         : int                   # port number
    date                         : date                 # session date (only one per day is allowed)
    """

    class PulseWeight(dj.Part):
        definition = """
        # Data for volume per pulse duty cycle estimation
        -> LiquidCalibration
        pulse_dur                : int                  # duration of pulse in ms
        ---
        pulse_num                : int                  # number of pulses
        weight                   : float                # weight of total liquid released in gr
        timestamp                : timestamp            # timestamp
        """
