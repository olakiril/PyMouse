
from Experiments.Calibrate import *

# define calibration parameters
session_params = {
    'duration'        : [20, 40, 100, 250],
    'probes'          : [1, 2],
    'pulsenum'        : [600, 400, 100, 30],
    'pulse_interval'  : [50, 50, 100, 100],
    'save'            : True,
}

# run experiment
exp = Calibrate(logger, session_params)
exp.run()

