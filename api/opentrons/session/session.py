import ast
import asyncio
import functools


from asyncio import Queue
from opentrons import robot
from opentrons.robot.robot import Robot
from datetime import datetime
from contextlib import contextmanager
from opentrons.broker import emit, on


VALID_STATES = set(
    ['loaded', 'running', 'finished', 'stopped', 'paused'])

STATE_CHANGE_EVENT = 'session.state.change'


class SessionManager(object):
    def __init__(self, loop=None):
        loop = loop or asyncio.get_event_loop()
        self.unsubscribe = on(
            STATE_CHANGE_EVENT,
            handler=self.on_change,
            loop=loop)
        self.robot = Robot()
        self.loop = loop
        self.snoozed = False
        self.sessions = []
        self.queue = Queue(loop=loop)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.loop.run_until_complete(self.unsubscribe())

    @contextmanager
    def snooze(self):
        self.snoozed = True
        try:
            yield
        finally:
            self.snoozed = False

    async def on_change(self, payload):
        if not self.snoozed:
            await self.queue.put((STATE_CHANGE_EVENT, payload))

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.queue.get()

    async def create(self, name, text):
        with self.snooze():
            self.session = Session(name=name, loop=self.loop)
            await self.session.load(text)
            self.sessions.append(self.session)
        self.session.set_state('loaded')
        return self.session

    def get_session(self):
        return self.session


class Session(object):
    def __init__(self, name, loop=None):
        loop = loop or asyncio.get_event_loop()
        self.loop = loop
        self.name = name

        self.command_log = {}
        self.errors = []
        self.commands = []
        self.state = None
        self.protocol_text = ""

        self.listen_to_commands = functools.partial(
            on,
            loop=loop,
            prefix='robot.command'
        )

    async def _simulate(self):
        stack = []
        commands = []

        async def on_command(payload):
            description = payload.get('text', '').format(
                **payload
            )

            if payload['$'] == 'before':
                commands.append(
                    {
                        'level': len(stack),
                        'description': description,
                        'id': len(commands)})
                stack.append(payload)
            else:
                stack.pop()

        unsubscribe = self.listen_to_commands(handler=on_command)

        try:
            await self._execute_protocol()
        finally:
            await unsubscribe()

        return commands

    async def load(self, text):
        try:
            self.protocol_text = text
            tree = ast.parse(self.protocol_text)
            self.protocol = compile(tree, filename=self.name, mode='exec')
            commands = await self._simulate()
            self.load_commands(commands)
        finally:
            if self.errors:
                raise Exception(*self.errors)
            self.set_state('loaded')

    def _execute_protocol(self):
        # HACK: hard reset singleton by replacing all of it's attributes
        # with the one from a newly constructed robot
        robot.__dict__ = {**Robot().__dict__}

        try:
            return self.loop.run_in_executor(None, exec, self.protocol, {})
        except:
            self.error_append(e)
            raise e

    async def run(self, devicename):
        async def on_command(payload):
            if payload['$'] == 'before':
                self.log_append()

        self.command_log.clear()
        self.errors.clear()

        unsubscribe = self.listen_to_commands(handler=on_command)
        self.set_state('running')
        robot.connect(devicename)

        try:
            await self._execute_protocol()
        finally:
            robot.disconnect()
            await unsubscribe()
            self.set_state('finished')

    def stop(self):
        robot.stop()
        self.set_state('stopped')
        return self

    def pause(self):
        robot.pause()
        self.set_state('paused')
        return self

    def resume(self):
        robot.resume()
        self.set_state('running')
        return self

    def set_state(self, state):
        if state not in VALID_STATES:
            raise ValueError('Invalid state: {0}. Valid states are: {1}'
                             .format(state, VALID_STATES))
        self.state = state
        self.on_state_changed()

    def load_commands(self, commands):
        """
        Given a list of tuples of form (depth, command_text)
        that represents a DFS traversal of a command tree,
        updates self.commands with a dictionary that holds
        a command tree.
        """
        def subtrees(commands, level):
            if not commands:
                return

            acc = []
            parent, *commands = commands

            for command in commands:
                if command['level'] > level:
                    acc.append(command)
                else:
                    yield (parent, acc)
                    parent = command
                    acc.clear()
            yield (parent, acc)

        def walk(commands, level=0):
            return [
                {
                    'description': key['description'],
                    'children': walk(subtree, level+1),
                    'id': key['id']
                }
                for key, subtree in subtrees(commands, level)
            ]

        self.commands.clear()
        self.commands.extend(walk(commands))

    def log_append(self):
        self.command_log.update({
            len(self.command_log): {
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        self.on_state_changed()

    def error_append(self, error):
        self.errors.append(
            {
                'timestamp': datetime.utcnow().isoformat(),
                'error': error
            }
        )
        self.on_state_changed()

    def _snapshot(self):
        return {
            'name': self.name,
            'state': self.state,
            'protocol_text': self.protocol_text,
            'commands': self.commands.copy(),
            'command_log': self.command_log.copy(),
            'errors': self.errors.copy()
        }

    def on_state_changed(self):
        snapshot = self._snapshot()
        emit(STATE_CHANGE_EVENT, snapshot)
