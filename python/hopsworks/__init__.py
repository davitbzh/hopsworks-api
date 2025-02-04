#
#   Copyright 2022 Logical Clocks AB
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import warnings
import logging
import os
import sys
import getpass

from hopsworks.client.exceptions import RestAPIError, ProjectException
from hopsworks import version
from hopsworks.connection import Connection

# Needs to run before import of hsml and hsfs
warnings.filterwarnings(action="ignore", category=UserWarning, module=r".*psycopg2")

import hsml  # noqa: F401, E402
import hsfs  # noqa: F401, E402

__version__ = version.__version__

connection = Connection.connection

_saas_connection = Connection.connection


def hw_formatwarning(message, category, filename, lineno, line=None):
    return "{}: {}\n".format(category.__name__, message)


warnings.formatwarning = hw_formatwarning

__all__ = ["connection"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    stream=sys.stdout,
)


def login(
    host: str = None,
    port: int = 443,
    project: str = None,
    api_key_value: str = None,
    api_key_file: str = None,
):
    """Connect to [Serverless Hopsworks](https://app.hopsworks.ai) by calling the `hopsworks.login()` function with no arguments.

    ```python

    project = hopsworks.login()

    ```

    Alternatively, connect to your own Hopsworks installation by specifying the host, port and api key.

    ```python

    project = hopsworks.login(host="my.hopsworks.server",
                              port=8181,
                              api_key_value="DKN8DndwaAjdf98FFNSxwdVKx")

    ```

    In addition to setting function arguments directly, `hopsworks.login()` also reads the environment variables:
    HOPSWORKS_HOST, HOPSWORKS_PORT, HOPSWORKS_PROJECT and HOPSWORKS_API_KEY.

    The function arguments do however take precedence over the environment variables in case both are set.

    # Arguments
        host: The hostname of the Hopsworks instance, defaults to `None`.
        port: The port on which the Hopsworks instance can be reached,
            defaults to `443`.
        project: Name of the project to access. If used inside a Hopsworks environment it always gets the current project. If not provided you will be prompted to enter it.
        api_key_value: Value of the Api Key
        api_key_file: Path to file wih Api Key
    # Returns
        `Project`: The Project object
    # Raises
        `RestAPIError`: If unable to connect to Hopsworks
    """

    # If already logged in, should reset connection and follow login procedure as Connection may no longer be valid
    logout()

    global _saas_connection

    # If inside hopsworks, just return the current project for now
    if "REST_ENDPOINT" in os.environ:
        _saas_connection = _saas_connection()
        project_obj = _saas_connection.get_project()
        print("\nLogged in to project, explore it here " + project_obj.get_url())
        return project_obj

    # This is run for an external client

    # Function arguments takes precedence over environment variable.
    # Here we check if environment variable exists and function argument is not set, we use the environment variable.

    # If api_key_value/api_key_file not defined, get HOPSWORKS_API_KEY environment variable
    api_key = None
    if (
        api_key_value is None
        and api_key_file is None
        and "HOPSWORKS_API_KEY" in os.environ
    ):
        api_key = os.environ["HOPSWORKS_API_KEY"]

    # If project argument not defined, get HOPSWORKS_PROJECT environment variable
    if project is None and "HOPSWORKS_PROJECT" in os.environ:
        project = os.environ["HOPSWORKS_PROJECT"]

    # If host argument not defined, get HOPSWORKS_HOST environment variable
    if host is None and "HOPSWORKS_HOST" in os.environ:
        host = os.environ["HOPSWORKS_HOST"]
    elif host is None:  # Always do a fallback to Serverless Hopsworks if not defined
        host = "c.app.hopsworks.ai"

    # If port same as default, get HOPSWORKS_HOST environment variable
    if port == 443 and "HOPSWORKS_PORT" in os.environ:
        port = os.environ["HOPSWORKS_PORT"]

    # This .hw_api_key is created when a user logs into Serverless Hopsworks the first time.
    # It is then used only for future login calls to Serverless. For other Hopsworks installations it's ignored.
    api_key_path = os.getcwd() + "/.hw_api_key"

    # Conditions for getting the api_key
    # If user supplied the api key directly
    if api_key_value is not None:
        api_key = api_key_value
    # If user supplied the api key in a file
    elif api_key_file is not None:
        file = None
        if os.path.exists(api_key_file):
            try:
                file = open(api_key_file, mode="r")
                api_key = file.read()
            finally:
                file.close()
        else:
            raise IOError(
                "Could not find api key file on path: {}".format(api_key_file)
            )
    # If user connected to Serverless Hopsworks, and the cached .hw_api_key exists, then use it.
    elif os.path.exists(api_key_path) and host == "c.app.hopsworks.ai":
        try:
            _saas_connection = _saas_connection(
                host=host, port=port, api_key_file=api_key_path
            )
            project_obj = _prompt_project(_saas_connection, project)
            print("\nLogged in to project, explore it here " + project_obj.get_url())
            return project_obj
        except RestAPIError:
            logout()
            # API Key may be invalid, have the user supply it again
            os.remove(api_key_path)

    if api_key is None and host == "c.app.hopsworks.ai":
        print(
            "Copy your Api Key (first register/login): https://c.app.hopsworks.ai/account/api/generated"
        )
        api_key = getpass.getpass(prompt="\nPaste it here: ")

        # If api key was provided as input, save the API key locally on disk to avoid users having to enter it again in the same environment
        descriptor = os.open(
            path=api_key_path, flags=(os.O_WRONLY | os.O_CREAT | os.O_TRUNC), mode=0o600
        )
        with open(descriptor, "w") as fh:
            fh.write(api_key.strip())

    try:
        _saas_connection = _saas_connection(host=host, port=port, api_key_value=api_key)
        project_obj = _prompt_project(_saas_connection, project)
    except RestAPIError as e:
        logout()
        raise e

    print("\nLogged in to project, explore it here " + project_obj.get_url())
    return project_obj


def _prompt_project(valid_connection, project):
    saas_projects = valid_connection.get_projects()
    if project is None:
        if len(saas_projects) == 0:
            raise ProjectException("Could not find any project")
        elif len(saas_projects) == 1:
            return saas_projects[0]
        else:
            while True:
                print("\nMultiple projects found. \n")
                for index in range(len(saas_projects)):
                    print("\t (" + str(index + 1) + ") " + saas_projects[index].name)
                while True:
                    project_index = input("\nEnter project to access: ")
                    # Handle invalid input type
                    try:
                        project_index = int(project_index)
                        # Handle negative indexing
                        if project_index <= 0:
                            print("Invalid input, must be greater than or equal to 1")
                            continue
                        # Handle index out of range
                        try:
                            return saas_projects[project_index - 1]
                        except IndexError:
                            print(
                                "Invalid input, should be an integer from the list of projects."
                            )
                    except ValueError:
                        print(
                            "Invalid input, should be an integer from the list of projects."
                        )
    else:
        for proj in saas_projects:
            if proj.name == project:
                return proj
        raise ProjectException("Could not find project {}".format(project))


def logout():
    global _saas_connection
    if type(_saas_connection) is Connection:
        _saas_connection.close()
    _saas_connection = Connection.connection
