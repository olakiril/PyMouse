from Logger import *
import sys, utils, os

if os.uname()[4][:3] == 'arm':
    from utils.Start import PyWelcome as Welcome
else:
    from utils.Start import Welcome

global logger
logger = Logger()                                                   # setup logger,publish IP and make setup available

# # # # Waiting for instructions loop # # # # #
while not logger.setup_status == 'exit':
    if logger.setup_status == 'ready':
        interface = Welcome(logger)
        while logger.setup_status != 'running' and logger.setup_status != 'exit': # wait for remote start
            interface.eval_input()
            time.sleep(0.5)
            logger.ping()
        interface.close()
    if logger.setup_status == 'running':   # run experiment unless stopped
        protocol = logger.get_protocol()
        exec(open(protocol).read())
        if logger.setup_status == 'stop':
            logger.update_setup_info('status','ready')                            # update setup status


# # # # # Exit # # # # #
logger.cleanup()
sys.exit(0)
