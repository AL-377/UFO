# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import List

from ufo.module.basic import BaseSession
import time
import os
from ufo.config.config import Config
configs = Config.get_instance().config_data

class UFOClientManager:
    """
    The manager for the UFO clients.
    """

    def __init__(self, session_list: List[BaseSession]) -> None:
        """
        Initialize a batch UFO client.
        """

        self._session_list = session_list

    def run_all(self) -> bool:
        """
        Run the batch UFO client.
        """
        time_out = configs["TIME_OUT"]

        for session in self.session_list:
            start_time = time.time()
            session.run()
            end_time = time.time()
            task_time = end_time-start_time
            open(os.path.join(session.log_path,"time.log"),'w').write(str(task_time))
            open(os.path.join(session.log_path,"cost.log"),'w').write(str(session.cost))
            if task_time > time_out:
                return False
        return True

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
