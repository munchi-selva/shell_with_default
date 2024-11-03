import click
import logging

from click_shell import make_click_shell, Shell
from click_shell.core import ClickShell

from typing import Any, Callable, List, Optional, TypeVar, Tuple, Union, cast

"""
Builds on click and click_shell to construct a CLI with these behaviours:
    1. An individual sub-command can be invoked by passing its name and
       arguments/options as parameters to the Python script that invokes
       the enclosing click.Group (actually a sub-class).
    2. Sub-commands can be interactively run from a shell if the Python
       script is called with no parameters.
    3. A default command can be marked such. If the input line provided
       to the Python script or shell is not recognised, the default
       command is run with the input line as its arguments/options.
"""

class ClickShellWithDefault(ClickShell):
    """
    A custom shell that treats the input line as arguments to a default command
    if it does not parse as a known command.

    Class hierarchy:
        cmd.Cmd
        |
        |_  click_shell.ClickCmd
            |
            |_  click_shell.core.ClickShell
                |
                |_  This class
    """

    def __init__(
            self,
            ctx: Optional[click.Context] = None,
            hist_file: Optional[str] = None,
            *args,
            **kwargs,
    ):
        super().__init__(ctx, hist_file, args, kwargs)

    def precmd(self, line: str) -> str:
        logging.info(f"Running precmd over '{line}'")
        return_val = super().precmd(line)
        logging.info(f"Gives '{return_val}'")
        return return_val

    def onecmd(self, line: str) -> str:
        logging.info(f"Running onecmd over '{line}'")
        onecmd_return = super().onecmd(line)
        logging.info(f"Gives '{onecmd_return}'")
        return onecmd_return

    def default(self, line: str) -> str:
        """
        Called on an input line when the command prefix is not recognised.

        If a default command is configured, runs that command with the
        input line as its argument(s).
        Otherwise falls back on the super class' implementation."""

        default_cmd_name = self.ctx.command.default_cmd_name
        if default_cmd_name:
            alternative_cmd = f"{default_cmd_name} {line}"
            logging.info(f"The command '{line}' is unknown, trying to run '{alternative_cmd}' instead.")
            return self.onecmd(alternative_cmd)
        return super().default(str)


class ClickGroupWithDefault(Shell):
    """
    Extends click_shell.Shell to invoke a default command if the provided input
    does not map to a known command, borrows click_default_group logic.

    Class hierarchy:
        click.Group
        |
        |_  click_shell.core.Shell
            |
            |_  This class
    """

    def __init__(
            self,
            prompt: Optional[Union[str, Callable[..., str]]] = None,
            intro: Optional[str] = None,
            hist_file: Optional[str] = None,
            on_finished: Optional[Callable[[click.Context], None]] = None,
            **attrs,
    ):
        self._debug_mode = attrs.pop('debug', False)
        logging_format = format="%(pathname)s:%(lineno)d %(funcName)s(): %(message)s"
        if self._debug_mode:
            logging.basicConfig(format=logging_format, level=logging.DEBUG)
        else:
            logging.basicConfig(format=logging_format, level=logging.INFO)


        logging.debug(f"Constructing ClickGroupWithDefault, attrs = {attrs}")

        self._custom_parser = attrs.pop('custom_parser', None)

        # To resolve as the default command.
        self.ignore_unknown_options = True

        self._default_cmd: Optional[click.core.Command] = None
        self.default_if_no_args = attrs.pop('default_if_no_args', True)
        super().__init__(prompt, intro, hist_file, on_finished,
                         shell_cls=ClickShellWithDefault, **attrs)

    def command(self, *args, **kwargs):
        """Augments the command decorator with a default parameter that indicates this command will run if the CLI receives an unrecognised command."""

        is_default = kwargs.pop('default', False)
        decorator = super().command(*args, **kwargs)
        if not is_default:
            # Just apply the super class' decorator
            return decorator
        else:
            logging.debug(f"Found a command decorated as the default, args = {args}, remaining kwargs = {kwargs}")

        def _decorator_with_default(cmd_body):
            cmd = decorator(cmd_body)
            self.set_default_command(cmd)
            return cmd

        return _decorator_with_default

    def set_default_command(self, cmd: click.core.Command) -> None:
        logging.debug(f"The default command name is '{cmd.name}'")
        self._default_cmd = cmd

    @property
    def default_cmd_name(self) -> Optional[str]:
        if self._default_cmd:
            return self._default_cmd.name
        return None
    
    def invoke(self, ctx: click.Context) -> Any:
        logging.debug("Invoked")
        return super().invoke(ctx)

    def parse_args(self, ctx: click.Context, args: List[str]) -> List[str]:
        logging.debug(f"Parsing {args}")

#       if self._custom_parser is not None():
#           logging.debug(f"Calling {_custom_parser.name}")

#       if not args and self.default_if_no_args:
#           args.insert(0, self.default_cmd_name)
        parsed_args: List[str] = super().parse_args(ctx, args)
        logging.debug(f"Parsed args = {parsed_args}")
        return parsed_args

    def resolve_command(self, ctx: click.Context, args: List[str]) -> Tuple[str, click.core.Command, List[str]]:
        """
        Resolves the arguments parsed from the command line used to invoke
        the Click group script into the details of the (sub)command that
        should be run, specifically:
            - The command name
            - The actual command
            - Arguments 

        If the super class' resolution fails to identify a command,
        returns details of the configured default command with the args
        provided as input.

        e.g. If the "echo" command is the default:

             python example_click_group.py echo 1 2 3 =>
             "echo", <echo_command>, ["1", "2", "3"]

             python example_click_group.py 1 2 3 =>
             "echo", <echo_command>, ["1, "2", "3"]
        """
        logging.debug(f"Trying to resolve {args}")
        base = super(ClickGroupWithDefault, self)
        try:
            cmd_name, cmd, args = base.resolve_command(ctx, args)
        except Exception:
            cmd_name = self.default_cmd_name
            cmd = self._default_cmd

#           args.insert(0, self.default_cmd_name)
#           cmd_name, cmd, args = base.resolve_command(ctx, args)
        logging.debug(f"cmd_name = {cmd_name}, args = {args}")
        return cmd_name, cmd, args

F = TypeVar("F", bound=Callable[..., Any])
def click_group_with_default(name: Optional[str] = None, **attrs: Any) -> Callable[[F], ClickGroupWithDefault]:
    """
    Creates a new ClickGroupWithDefault with the named function (assumed to be
    a Click command) as a callback.
    """
    logging.info(f"{attrs}")
    attrs.setdefault('cls', ClickGroupWithDefault)
    return cast(ClickGroupWithDefault, click.command(name, **attrs))
