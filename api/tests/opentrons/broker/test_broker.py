from opentrons.broker import publish, on


@publish.both(name='command', text='{arg1} {arg2} {arg3}')
def A(arg1, arg2, arg3='foo'):
    B(0)
    return 100


@publish.both(name='command', text='{arg1} {arg2} {arg3}')
def C(arg1, arg2, arg3='bar'):
    B(0)
    return 100


@publish.both(name='command', text='{arg1}')
def B(arg1):
    return None


async def test_add_listener(loop):
    stack = []
    calls = []

    async def on_command(event):
        description = event['text'].format(**event)

        if event['$'] == 'before':
            stack.append(event)
            calls.append({'level': len(stack), 'description': description})
        else:
            stack.pop()

    unsubscribe = on('command', on_command, loop)

    A(0, 1)
    B(2)
    C(3, 4)

    await unsubscribe()

    expected = [
        {'level': 1, 'description': '0 1 foo'},
        {'level': 2, 'description': '0'},
        {'level': 1, 'description': '2'},
        {'level': 1, 'description': '3 4 bar'},
        {'level': 2, 'description': '0'}]

    assert calls == expected

    A(0, 2)

    assert calls == expected, 'No calls expected after unsubscribe()'
