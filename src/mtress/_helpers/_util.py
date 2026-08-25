"""Utility functions."""

import dataclasses
import inspect


def enable_templating(template_class):
    """Decorate a function to accept a dataclass as a template."""

    def _decorator(func):
        param_names = [
            field.name for field in dataclasses.fields(template_class)
        ]
        func_signature = inspect.signature(func)
        func_params = func_signature.parameters
        # check if kw arguments have been provided
        kwargs_present = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param_str, param in func_params.items()
        )

        def _wrapper(*args, template=None, **kwargs):
            if template is not None:
                if not isinstance(template, template_class):
                    raise TypeError(
                        f"template should be of type {template_class}"
                    )

                for param in param_names:
                    if param not in kwargs and (
                        param in func_params or kwargs_present
                    ):
                        # Take the value from the template if it is not
                        # provided as keyword argument
                        kwargs[param] = getattr(template, param)

            return func(*args, **kwargs)

        return _wrapper

    return _decorator
