import ast
import asyncio
import logging
import sys

from asyncio import Queue
from concurrent import futures

from opentrons.robot.robot import Robot
from opentrons import robot

from opentrons.server.session import Session
from opentrons.util.trace import EventBroker

log = logging.getLogger(__name__)


class RobotContainer(object):
    def __init__(self, loop=None, filters=['add-command']):
        self.loop = loop or asyncio.get_event_loop()
        self.protocol = None
        self.session = None
        self.update_filters(filters)

        self.notifications = Queue(loop=self.loop)

        EventBroker.get_instance().add(self.on_notify)

    def update_filters(self, filters):
        self.filters = set(filters)

    def on_notify(self, event):
        if event.get('name', None) not in self.filters:
            return

        if self.session and event.get('name', '') == 'add-command':
            self.session.log_append(event['arguments']['command'])

        # Use this to turn self into it's id so we don't
        # end up serializing every object who's method
        # triggered the event
        arguments = event.get('arguments', {})
        if 'self' in arguments:
            arguments['self_id'] = arguments.pop('self')

        payload = (event, self.session)
        future = asyncio.run_coroutine_threadsafe(
                self.notifications.put(payload), self.loop)

        # TODO (artyom, 20170829): this block ensures proper sequencing
        # of notification, also covering the scenario of being called from
        # unit test where MainThread has no event loop associated with it
        if not self.thread_has_event_loop():
            futures.wait([future])

    def reset_robot(self, robot):
        # robot is essentially a singleton
        # throughout the api however we want to reset it
        # in order to do this we call a constructor
        # and then copy over the __dict__ of a newly
        # constructed robot to the one that is a singleton
        _robot = self.new_robot()
        robot.__dict__ = {**_robot.__dict__}

    def run(self, devicename=None, session=None):
        if session is None:
            session = self.session

        self.reset_robot(robot)

        if devicename is not None:
            robot.connect(devicename)

        try:
            session.set_state('running')
            exec(self.protocol, {})
            session.set_state('finished')
        except Exception as e:
            type, value, traceback = sys.exc_info()
            session.error_append((e, traceback))
            session.set_state('error')
        finally:
            robot.disconnect()

        commands = robot.commands()
        # TODO(artyom, 20170829): remove wrapping command into tuple
        # once commands contain call depth information
        commands = [(0, command) for command in commands]
        session.init_commands(commands)

        return session

    def stop(self):
        robot.stop()
        self.session.set_state('stopped')
        return self.session

    def pause(self):
        robot.pause()
        self.session.set_state('paused')
        return self.session

    def resume(self):
        robot.resume()
        self.session.set_state('running')
        return self.session

    def new_robot(self):
        return Robot()

    def load_protocol(self, text, filename):
        try:
            self.session = None
            tree = ast.parse(text)
            self.protocol = compile(tree, filename=filename, mode='exec')
            session = Session(name=filename, protocol_text=text)

            # Suppress all notifications during protocol simulation
            _filters = self.filters
            self.update_filters([])
            self.run(session=session)

            self.session = session
        finally:
            self.update_filters(_filters)
            if session.state == 'error':
                raise Exception(*session.errors.pop())
            return self.session

    def load_protocol_file(self, filename):
        with open(filename) as file:
            text = ''.join(list(file))
            return self.load_protocol(text, filename)

    def get_session(self):
        return self.session

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.notifications.get()

    def finalize(self):
        log.info('Finalizing robot_container')

        # Keep it as a loop in case there is more than one handler to remove
        for command in [self.on_notify]:
            try:
                EventBroker.get_instance().remove(command)
            except ValueError:
                log.debug(
                    "Tried removing notification handler that wasn't registered")  # NOQA

    def thread_has_event_loop(self):
        try:
            asyncio.get_event_loop()
        except RuntimeError as e:
            return False
        else:
            return True
