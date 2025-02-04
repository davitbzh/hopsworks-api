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


class RestAPIError(Exception):
    """REST Exception encapsulating the response object and url."""

    def __init__(self, url, response):
        try:
            error_object = response.json()
        except Exception:
            error_object = {}
        message = (
            "Metadata operation error: (url: {}). Server response: \n"
            "HTTP code: {}, HTTP reason: {}, body: {}, error code: {}, error msg: {}, user "
            "msg: {}".format(
                url,
                response.status_code,
                response.reason,
                response.content,
                error_object.get("errorCode", ""),
                error_object.get("errorMsg", ""),
                error_object.get("usrMsg", ""),
            )
        )
        super().__init__(message)
        self.url = url
        self.response = response


class UnknownSecretStorageError(Exception):
    """This exception will be raised if an unused secrets storage is passed as a parameter."""


class GitException(Exception):
    """Generic git exception"""


class JobException(Exception):
    """Generic job exception"""


class KafkaException(Exception):
    """Generic kafka exception"""


class DatasetException(Exception):
    """Generic dataset exception"""


class ProjectException(Exception):
    """Generic project exception"""


class OpenSearchException(Exception):
    """Generic opensearch exception"""


class ExternalClientError(TypeError):
    """Raised when external client cannot be initialized due to missing arguments."""

    def __init__(self, message):
        super().__init__(message)
