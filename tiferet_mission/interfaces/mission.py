"""tiferet_mission Interfaces Mission"""

# *** imports

# ** core
from abc import abstractmethod
from typing import List, Optional

# ** app
from tiferet.interfaces import Service

# *** interfaces

# ** interface: mission_service
class MissionService(Service):
    '''
    Service interface for managing mission plans and device assignments.
    '''

    # * method: exists
    @abstractmethod
    def exists(self, id: str) -> bool:
        '''
        Check if a mission exists by ID.

        :param id: The mission identifier.
        :type id: str
        :return: True if the mission exists, otherwise False.
        :rtype: bool
        '''
        raise NotImplementedError()

    # * method: get
    @abstractmethod
    def get(self, id: str):
        '''
        Retrieve a mission by ID.

        :param id: The mission identifier.
        :type id: str
        :return: The mission aggregate.
        '''
        raise NotImplementedError()

    # * method: list
    @abstractmethod
    def list(self, drone_type: Optional[str] = None, status: Optional[str] = None) -> List:
        '''
        List missions with optional filters.

        :param drone_type: Optional drone type filter.
        :type drone_type: str | None
        :param status: Optional status filter.
        :type status: str | None
        :return: A list of mission aggregates.
        :rtype: List
        '''
        raise NotImplementedError()

    # * method: save
    @abstractmethod
    def save(self, mission) -> None:
        '''
        Save or update a mission.

        :param mission: The mission aggregate to persist.
        :return: None
        '''
        raise NotImplementedError()

    # * method: delete
    @abstractmethod
    def delete(self, id: str) -> None:
        '''
        Delete a mission by ID. This operation should be idempotent.

        :param id: The mission identifier.
        :type id: str
        :return: None
        '''
        raise NotImplementedError()

    # * method: save_assignment
    @abstractmethod
    def save_assignment(self, assignment) -> None:
        '''
        Persist a device assignment record.

        :param assignment: The device assignment aggregate.
        :return: None
        '''
        raise NotImplementedError()

    # * method: get_assignment
    @abstractmethod
    def get_assignment(self, mission_id: str):
        '''
        Retrieve the active device assignment for a mission.

        :param mission_id: The mission identifier.
        :type mission_id: str
        :return: The device assignment aggregate, or None.
        '''
        raise NotImplementedError()

    # * method: delete_assignment
    @abstractmethod
    def delete_assignment(self, mission_id: str) -> None:
        '''
        Delete the device assignment for a mission. Idempotent.

        :param mission_id: The mission identifier.
        :type mission_id: str
        :return: None
        '''
        raise NotImplementedError()
