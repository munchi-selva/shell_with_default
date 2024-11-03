import click
import logging
from click_shell import make_click_shell, Shell

from shell_with_default import click_group_with_default, ClickShellWithDefault

@click_group_with_default(prompt="sample-shell-with-default $ ", debug=True)
@click.pass_context
def sample_shell(ctx: click.Context):
    print("No idea")

@sample_shell.command()
@click.pass_context
def non_default(ctx: click.Context):
    logging.info("Command called")

@sample_shell.command(default=True)
@click.pass_context
@click.argument("arg")
@click.option("-c", "--count", type=int, default=True)
def default(ctx: click.Context, arg: str, count: int):
    logging.info(f"Command called with argument '{arg}', count = {count}")

if __name__ == "__main__":

    # Launch a sample shell that has a default command
    # sample_shell()

    # Alternative way to create the shell, requires additional imports:
    #   from click_shell import make_click_shell, Shell
    #   from shell_with_default import ClickShellWithDefault
    ctx = click.Context(sample_shell)
    shell = make_click_shell(ctx, prompt="sample_shell-with-default $ ", shell_cls=ClickShellWithDefault)
    # shell.cmdloop()

