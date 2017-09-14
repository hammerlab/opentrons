from .broker import emit
import functools
import inspect


def _publish(before, after, name=None, action=None, **decorator_kwargs):
    assert (name is None) != (action is None), "Either 'name' or 'action' args should be specified"  # noqa

    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            payload = _get_args(f, args, kwargs)
            payload.update(decorator_kwargs)
            action_name = name

            if action:
                action_args = dict(
                    zip(
                        reversed(inspect.getargspec(f).args),
                        reversed(inspect.getargspec(f).defaults)))

                action_args.update(decorator_kwargs)
                action_args.update({
                        key: payload[key]
                        for key in set(action_args) & payload.keys()
                    })
                action_name, payload = action(**action_args)

            if before:
                emit(action_name, {**payload, '$': 'before'})

            res = f(*args, **kwargs)

            if after:
                emit(action_name, {**payload, '$': 'after', 'return': res})

            return res
        return decorated

    return decorator


def _get_args(f, args, kwargs):
    # Create the initial dictionary with args that have defaults
    res = {}

    if inspect.getargspec(f).defaults:
        res = dict(
            zip(
                reversed(inspect.getargspec(f).args),
                reversed(inspect.getargspec(f).defaults)))

    # Update / insert values for positional args
    res.update(dict(zip(inspect.getargspec(f).args, args)))

    # Update it with values for named args
    res.update(kwargs)
    return res

before = functools.partial(_publish, before=True, after=False)
after = functools.partial(_publish, before=False, after=True)
both = functools.partial(_publish, before=True, after=True)
