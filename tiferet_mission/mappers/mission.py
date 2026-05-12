"""tiferet_mission Mappers Mission"""

# *** imports

# ** core
from typing import Dict, List, Optional

# ** app
from tiferet.mappers import Aggregate
from ..domain.mission import Mission, MissionItem

# *** mappers

# ** mapper: mission_item_aggregate
class MissionItemAggregate(MissionItem, Aggregate):
    '''
    Mutable aggregate for the MissionItem domain object.
    '''

    # * method: update_position
    def update_position(self, latitude: float, longitude: float, altitude: float) -> None:
        '''
        Update the positional coordinates of this mission item.

        :param latitude: Latitude in degrees.
        :type latitude: float
        :param longitude: Longitude in degrees.
        :type longitude: float
        :param altitude: Altitude in meters.
        :type altitude: float
        '''

        # Apply positional updates.
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude

    # * method: update_params
    def update_params(self,
            param1: Optional[float] = None,
            param2: Optional[float] = None,
            param3: Optional[float] = None,
            param4: Optional[float] = None,
        ) -> None:
        '''
        Update command-specific parameters.

        :param param1: Parameter 1 value, or None to leave unchanged.
        :type param1: float | None
        :param param2: Parameter 2 value, or None to leave unchanged.
        :type param2: float | None
        :param param3: Parameter 3 value, or None to leave unchanged.
        :type param3: float | None
        :param param4: Parameter 4 value, or None to leave unchanged.
        :type param4: float | None
        '''

        # Update only the parameters that were provided.
        if param1 is not None:
            self.param1 = param1
        if param2 is not None:
            self.param2 = param2
        if param3 is not None:
            self.param3 = param3
        if param4 is not None:
            self.param4 = param4


# ** mapper: mission_aggregate
class MissionAggregate(Mission, Aggregate):
    '''
    Mutable aggregate for the Mission domain object.
    '''

    # * attribute: items
    items: List[MissionItemAggregate] = []

    # * method: rename
    def rename(self, name: str) -> None:
        '''
        Rename the mission.

        :param name: The new mission name.
        :type name: str
        '''

        # Apply the name update.
        self.name = name

    # * method: set_status
    def set_status(self, status: str) -> None:
        '''
        Update the mission lifecycle status.

        :param status: The new status value.
        :type status: str
        '''

        # Apply the status update.
        self.status = status

    # * method: add_item
    def add_item(self, item: MissionItemAggregate) -> None:
        '''
        Append a mission item to the items list.

        :param item: The mission item aggregate to add.
        :type item: MissionItemAggregate
        '''

        # Append the item to the list.
        self.items.append(item)

    # * method: remove_item
    def remove_item(self, item_id: str) -> Optional[MissionItemAggregate]:
        '''
        Remove a mission item by its ID and re-sequence remaining items.

        :param item_id: The ID of the item to remove.
        :type item_id: str
        :return: The removed item, or None if not found.
        :rtype: MissionItemAggregate | None
        '''

        # Find and remove the item by ID.
        removed = None
        for i, item in enumerate(self.items):
            if item.id == item_id:
                removed = self.items.pop(i)
                break

        # Re-sequence remaining items if an item was removed.
        if removed is not None:
            for idx, item in enumerate(self.items):
                item.sequence = idx

        # Return the removed item.
        return removed

    # * method: reorder_items
    def reorder_items(self, sequence_map: Dict[str, int]) -> None:
        '''
        Reorder mission items according to a mapping of item_id -> new_sequence.

        :param sequence_map: Dict mapping item IDs to their new sequence numbers.
        :type sequence_map: Dict[str, int]
        '''

        # Apply new sequence numbers from the map.
        for item in self.items:
            if item.id in sequence_map:
                item.sequence = sequence_map[item.id]

        # Sort the items list by the new sequence numbers.
        self.items.sort(key=lambda it: it.sequence)

    # * method: assign_device
    def assign_device(self, device_id: str) -> None:
        '''
        Set the assigned device ID on this mission.

        :param device_id: The device identifier.
        :type device_id: str
        '''

        # Set the device_id field.
        self.device_id = device_id

    # * method: unassign_device
    def unassign_device(self) -> None:
        '''
        Clear the assigned device ID from this mission.
        '''

        # Reset device_id to None.
        self.device_id = None
