# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import List

from ufo.module.basic import BaseSession

import time
import os
class UFOClientManager:
    """
    The manager for the UFO clients.
    """

    def __init__(self, session_list: List[BaseSession]) -> None:
        """
        Initialize a batch UFO client.
        """

        self._session_list = session_list

    def run_all(self) -> None:
        """
        Run the batch UFO client.
        """
        # add timer for session
        for session in self.session_list:
            start_time = time.time()
            session.run()
            end_time = time.time()
            print(end_time-start_time)
            time_log_file = os.path.join(session.log_path, "time.txt")
            with open(time_log_file, "w") as f:
                f.write(str(end_time-start_time))

    @property
    def session_list(self) -> List[BaseSession]:
        """
        Get the session list.
        :return: The session list.
        """
        return self._session_list

    def add_session(self, session: BaseSession) -> None:
        """
        Add a session to the session list.
        :param session: The session to add.
        """
        self._session_list.append(session)

    def next_session(self) -> BaseSession:
        """
        Get the next session.
        :return: The next session.
        """
        return self._session_list.pop(0)
