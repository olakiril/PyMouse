import datajoint as dj

experiment = dj.create_virtual_module('experiment.py', 'test_experiment', create_tables=True)
behavior = dj.create_virtual_module('behavior.py', 'test_behavior', create_tables=True)
stimulus = dj.create_virtual_module('stimulus.py', 'test_stimuli', create_tables=True)
mice = dj.create_virtual_module('mice.py', 'lab_mice')
common = dj.create_virtual_module('common.py', 'lab_common')

@experiment.schema
class Protocol(dj.Lookup):
    definition = """
    # Behavioral experiment parameters
    protocol_idx         : int                          # task identification number
    ---
    protocol_file        : varchar(4095)                # stimuli to be presented (array of dictionaries)
    description=""       : varchar(2048)                # task description
    timestamp            : timestamp    
    """

@experiment.schema
class Control(dj.Lookup):
    definition = """
    #
    setup                : varchar(64)                 # Setup name
    ---
    ->Protocol
    ip                   : varchar(16)                  # setup IP address
    status="exit"        : enum('ready','running','stop','sleeping','exit','offtime','wakeup') 
    animal_id=null       : int                          # animal id
    last_ping            : timestamp                    
    notes=null           : varchar(256)                 
    current_session=null : smallint                          
    last_trial=null      : smallint                          
    total_liquid=null    : float     
    state=null           : varchar(256)  
    difficulty=null      : smallint                     
    start_time=null      : time                         
    stop_time=null       : time 
    """

@experiment.schema
class Condition(dj.Manual):
    definition = """
    # unique stimulus conditions
    cond_hash             : char(24)                    # unique condition hash
    ---
    cond_tuple=null       : blob      
    """

@experiment.schema
class Session(dj.Manual):
    definition = """
    # Behavior session infod
    -> mice.Mice
    session              : smallint                     # session number
    ---
    setup                : varchar(64)                  # Setup name
    notes=null           : varchar(2048)                # session notes
    session_tmst         : timestamp                    # session timestamp     
    """
    class Params(dj.Part):
        definition = """
        # Session parameters
        -> Session
        ---
        -> Protocol              
        protocol=null        : blob                     # protocol file
        session_params=null  : blob                     # parameters for the session
        experiment_type=null : varchar(256)             
        git_version=null     : varchar(7)               # git short hash     
        """

@experiment.schema
class Trial(dj.Manual):
    definition = """
    # Trial information
    -> Session
    trial_idx            : smallint                     # unique condition index
    ---
    -> Condition
    start_time           : int                          # start time from session start (ms)
    end_time             : int                          # end time from session start (ms)
    aborted=0            : tinyint                      # aborted flag
    """



@behavior.schema
class PortState(dj.Manual):
    definition = """
    # Center port information
    -> Session
    time	     	     : int                      	# time from session start (ms)
    port=0               : tinyint                      # port number
    ---
    state=1              : tinyint
    """

@behavior.schema
class Lick(dj.Manual):
    definition = """
    # Lick timestamps
    -> Session
    time	             : int           	            # time from session start (ms)
    port                 : tinyint                      # port number
    """


@stimulus.schema
class MovieClass(dj.Lookup):
    definition = """
    # types of movies
    movie_class          : varchar(16)      
    """

@stimulus.schema
class Movie(dj.Lookup):
    definition = """
    # movies used for generating clips
    movie_name                              : char(8)       # short movie title
    ---
    -> MovieClass
    path                                    : varchar(255)
    original_file                           : varchar(255)
    file_template                           : varchar(255)  # filename template with full path
    file_duration                           : float         # (s) duration of each file (must be equal)
    codec="-c:v libx264 -preset slow -crf 5": varchar(255)
    movie_description                       : varchar(255)  # full movie title
    frame_rate=30                           : float         # frames per second
    frame_width=256                         : smallint      # pixels
    frame_height=144                        : smallint      # pixels
    """
    class Clip(dj.Part):
        definition = """
        # clips from movies
        -> Movie
        clip_number                        : smallint       # clip index
        ---
        file_name                          : varchar(255)   # full file name
        clip                               : longblob       # stored clip
        parent_file_name=null              : varchar(255)
        duration=null                      : smallint       # duration in seconds
        """

@stimulus.schema
class Clip(dj.Manual):
    definition = """
    # movie clip conditions
    mov_hash             : char(24)                     # unique condition hash
    ---
    -> Movie.Clip
    movie_duration       : smallint                     # movie duration
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

@stimulus.schema
class OdorIdentity(dj.Lookup):
    definition = """
    # Odor identity information
    odorant_id           : smallint                     # odor identity
    ---
    odorant_name=null    : varchar(128)                 # odor name
    concentration=100    : int                          # odor concentration in prc
    solvent=null         : varchar(255)                 
    description=null     : varchar(256)       
    """

@stimulus.schema
class Odor(dj.Manual):
    definition = """
    # odor conditions
    odor_hash                : char(24)                 # unique condition hash
    """
    class Channel(dj.Part):
        definition = """
        # odor conditions
        -> Odor
        -> OdorIdentity
        ---
        duration             : smallint                 # odor duration (ms)
        delivery_channel     : smallint                 # delivery idx for channel mapping
        mix                  : tinyint                  # odorant prc in the mixture
        """
    class Trial(dj.Part):
        definition = """
        # Stimulus onset timestamps
        -> Trials
        ---
        -> Odor
        start_time          : int                        # start time from session start (ms)
        end_time            : int                        # end time from session start (ms)
        """

@stimulus.schema
class Reward(dj.Manual):
    definition = """
    # reward probe conditions
    rew_hash               : char(24)                     # unique reward hash
    ---
    port=0                 : smallint                     # delivery port
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

@stimulus.schema
class LiquidCalibration(dj.Manual):
    definition = """
    # Liquid delivery calibration sessions for each probe
    setup                        : varchar(64)          # Setup name
    port                         : tinyint              # port number
    date                         : date                 # session date (only one per day is allowed)
    """
    class PulseWeight(dj.Part):
        definition = """
        # Data for volume per pulse duty cycle estimation
        -> LiquidCalibration
        pulse_dur                : smallint             # duration of pulse in ms
        ---
        pulse_num                : smallint             # number of pulses
        weight                   : float                # weight of total liquid released in gr
        timestamp                : timestamp            # timestamp
        """

@stimulus.schema
class Scene(dj.Manual):
    definition = """
    # scene conditions
    scene_hash                : char(24)                 # unique condition hash
    environment               : tinyblob
    """
    class Object(dj.Part):
        definition = """
        # odor conditions
        -> Odor
        -> ObjectIdentity
        ---
        params                 : tinyblob                 # object parameters
        """

    class Trial(dj.Part):
        definition = """
        # Stimulus onset timestamps
        -> Trials
        ---
        -> Scene
        start_time          : int                        # start time from session start (ms)
        end_time            : int                        # end time from session start (ms)
        """