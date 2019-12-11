#!/usr/bin/env python3
"""The Dreaded Rear Admiral.

A configuarable Celery application.

Usage:
  admiral [options]
  admiral (-h | --help)
  admiral --version

Options:
  -c <file>, --config <file>     Read configuration from file.
  -s <section>, --section <section> Configuration file section to use.
  -i --interactive               Create app and enter IPython
"""

import os

from celery import Celery
import yaml

CONFIG_FILE_ENV_KEY = "ADMIRAL_CONFIG_FILE"
CONFIG_SECTION_ENV_KEY = "ADMIRAL_CONFIG_SECTION"
WORKER_NAME_ENV_KEY = "ADMIRAL_WORKER_NAME"
DEFAULT_CONFIG_FILE = "/run/secrets/admiral.yml"
DEFAULT_CONFIG_SECTION = "default-section"


class CustomCelery(Celery):
    """Customized Celery instance."""

    def gen_task_name(self, name, module):
        """Make generated tasks names nicer."""
        if module.endswith(".tasks"):
            module = module[:-6]
        return super(CustomCelery, self).gen_task_name(name, module)


def load_config(filename):
    """Load a configuration from a file."""
    print("Reading configuration from %s" % filename)
    with open(filename, "r") as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
    return config


def determine_input(description, cli_arg, env_key, default):
    """Determine origin of a setting and tell the user.

    The order of precedence is:
    - cli argument
    - environment variable
    - a default value passed as an argument
    """
    if cli_arg:
        print(f"{description} specified on command line: {cli_arg}")
        return cli_arg

    if env_key in os.environ.keys():
        env_value = os.environ.get(env_key)
        print(
            f"{description} specified in environment variable {env_key}:" f"{env_value}"
        )
        return env_value

    print(
        f"{description} not specified on commandline or environment.  "
        f"Using default: {default}"
    )
    return default


def configure_app(config_file=None, config_sction=None):
    """Create, configure, and return the Celery app.

    We want to handle running as a stand-alone application and also being
    invoked from the celery command.  If the called_via_celery_cmd is set to
    True then we just read our configs, setup the app, and return the app
    instance so it can be pointed to by the `celery` attribute.  This is what
    celery expects.  Otherwise, we do our own magic.
    """
    # get a configration filename
    yml_filename = determine_input(
        "Config file", config_file, CONFIG_FILE_ENV_KEY, DEFAULT_CONFIG_FILE
    )

    # load the entire configuration
    entire_config = load_config(yml_filename)

    # get the name of a configuration section for this worker
    config_section = determine_input(
        "Config section", config_sction, CONFIG_SECTION_ENV_KEY, DEFAULT_CONFIG_SECTION
    )

    # get the configuration for this worker
    active_config = entire_config[config_section]

    # create the app instance
    app = CustomCelery("admiral")

    # apply the configuration
    # See: http://docs.celeryproject.org/en/latest/userguide/configuration.html
    celery_config = active_config.get("celery", {})
    app.conf.update(celery_config)

    # print out the changes applied to the default celery config
    print("-" * 40)
    print(app.conf.humanize())
    print("-" * 40)

    # register any tasks that are listed for auto-discovery in the config
    autodiscover_tasks = active_config.get("autodiscover_tasks", [])
    print("Auto discovering tasks from", autodiscover_tasks)
    app.autodiscover_tasks(autodiscover_tasks)

    return app


def main():
    """Start of program when invoked as a stand-alone."""
    from docopt import docopt

    args = docopt(__doc__, version="v0.0.1")
    # TODO set environment vars for config and config_section or
    # https://celery.readthedocs.io/en/latest/userguide/extending.html#adding-new-command-line-options

    if args["--interactive"]:
        celery.start(argv=["celery", "-A", "admiral", "shell"])
    else:
        worker_name = os.environ.get(WORKER_NAME_ENV_KEY, "unnamed")
        celery.start(
            argv=[
                "celery",
                "-A",
                "admiral",
                "worker",
                "-l",
                "info",
                "-n",
                f"{worker_name}@%h",
            ]
        )


if __name__ == "__main__":
    # running as a stand-alone application
    main()
else:  # __name__ == 'admiral.celery':
    # this module was loaded via the celery command line
    # setup the app and return it in the attribute below
    celery = configure_app()
