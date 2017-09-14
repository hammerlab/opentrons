from opentrons.actions import types


def make_action(name, payload):
    return (name, payload)


def aspirate(volume, location, rate, text):
    return make_action(
        name=types.ASPIRATE,
        payload={
            'volume': volume,
            'location': location,
            'rate': rate,
            'text': text
        }
    )


def dispense(volume, location, rate, text):
    return make_action(
        name=types.DISPENSE,
        payload={
            'volume': volume,
            'location': location,
            'rate': rate,
            'text': text
        }
    )
