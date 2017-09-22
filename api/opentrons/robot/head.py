# I think that all GCODE sending should be buffered, like stdout,
# and be triggered to send gcodes regularly. This buffer could also
# be `flushed()`.

class InstrumentMotor(object):
    """
    Provides access to Robot's head motor.
    """
    def __init__(self, this_robot, axis):
        self.robot = this_robot
        self.axis = axis

    def move(self, value, mode='absolute'):
        """
        Move plunger motor.

        Parameters
        ----------
        value : int
            A one-dimensional coordinate to move to.
        mode : {'absolute', 'relative'}
        """
        kwargs = {self.axis: value}
        self.robot._driver.move_plunger(
            mode=mode, **kwargs
        )

    def home(self):
        """
        Home plunger motor.
        """
        self.robot._driver.home(self.axis)

    def wait(self, seconds):
        """
        Wait.

        Parameters
        ----------
        seconds : int
            Number of seconds to pause for.
        """
        self.robot._driver.wait(seconds)

    def speed(self, rate):
        """
        Set motor speed.

        Parameters
        ----------
        rate : int
        """
        self.robot._driver.set_plunger_speed(rate, self.axis)
        return self


class Gantry:
    def __init__(self):
        setup_driver()
        self.instrument_a = None
        self.instrument_b = None

    def _move(self, x, y, z, a, b):
        '''atomic gantry movement'''
        pass

    def add_instrument(self, instrument, instrumet_slot):
        '''Initializes instrument passed with instrument motor'''
        pass

    def home(self):
        '''home x,y,z axes'''
        pass

    def setup_driver(self):
        '''
        This should initialize the driver. The Gantry
        is responsible for the driver since it is basically
        a class that allows driver position to be tracked and
        splits provides driver capabilities to the relavent
        system components (i.e. it gives the plunger motor to the pipette)
        '''
        pass


