"""tiferet_mission Domain Mission"""

# *** imports

# ** core
from typing import Any, Dict, List, Optional

# ** infra
from pydantic import Field, model_validator

# ** app
from tiferet.domain import DomainObject
from .settings import MAV_COMMANDS

# *** models

# ** model: mission_item
class MissionItem(DomainObject):
    '''
    A single MAVLink-compatible mission item (command) within a mission plan.
    '''

    # * attribute: id
    id: str = Field(..., description='Unique identifier for the mission item.')

    # * attribute: sequence
    sequence: int = Field(..., description='Zero-based order in the mission.')

    # * attribute: command
    command: str = Field(..., description='MAV_CMD name (e.g., NAV_WAYPOINT, NAV_TAKEOFF).')

    # * attribute: command_id
    command_id: int = Field(default=0, description='MAV_CMD numeric code (e.g., 16, 22, 21).')

    # * attribute: category
    category: str = Field(default='NAV', description='Command category: NAV, DO, or CONDITION.')

    # * attribute: frame
    frame: str = Field(default='GLOBAL_RELATIVE_ALT', description='Coordinate frame for positional data.')

    # * attribute: param1
    param1: float = Field(default=0.0, description='Command parameter 1 (hold time / pitch / etc.).')

    # * attribute: param2
    param2: float = Field(default=0.0, description='Command parameter 2 (acceptance radius / etc.).')

    # * attribute: param3
    param3: float = Field(default=0.0, description='Command parameter 3 (pass radius / etc.).')

    # * attribute: param4
    param4: float = Field(default=0.0, description='Command parameter 4 (yaw / etc.).')

    # * attribute: latitude
    latitude: float = Field(default=0.0, description='Latitude in degrees.')

    # * attribute: longitude
    longitude: float = Field(default=0.0, description='Longitude in degrees.')

    # * attribute: altitude
    altitude: float = Field(default=0.0, description='Altitude in meters (frame-relative).')

    # * attribute: autocontinue
    autocontinue: bool = Field(default=True, description='Whether to auto-continue to the next item.')

    # * attribute: description
    description: Optional[str] = Field(default=None, description='Optional human-readable description.')

    # * method: derive_command_fields (validator)
    @model_validator(mode='before')
    @classmethod
    def derive_command_fields(cls, data: Any) -> Any:
        '''
        Derive command_id and category from the command name using the
        MAV_COMMANDS lookup table.

        :param data: The raw input data passed to the model.
        :type data: Any
        :return: The (possibly augmented) input data.
        :rtype: Any
        '''

        # Only mutate dict-shaped inputs.
        if not isinstance(data, dict):
            return data
        data = dict(data)

        # Look up command metadata from the reference table.
        cmd_name = data.get('command')
        if cmd_name and cmd_name in MAV_COMMANDS:
            cmd_info = MAV_COMMANDS[cmd_name]
            data.setdefault('command_id', cmd_info['id'])
            data.setdefault('category', cmd_info['category'])

        # Return the augmented input data.
        return data


# ** model: mission
class Mission(DomainObject):
    '''
    A complete mission plan consisting of ordered mission items.
    '''

    # * attribute: id
    id: str = Field(..., description='Unique identifier for the mission.')

    # * attribute: name
    name: str = Field(..., description='Human-readable name of the mission.')

    # * attribute: description
    description: Optional[str] = Field(default=None, description='Optional description of the mission.')

    # * attribute: status
    status: str = Field(default='draft', description='Mission lifecycle status.')

    # * attribute: drone_type
    drone_type: str = Field(..., description='Required drone type for this mission (copter, plane, rover, etc.).')

    # * attribute: device_id
    device_id: Optional[str] = Field(default=None, description='Reference to the assigned device from the external registry.')

    # * attribute: items
    items: List[MissionItem] = Field(default_factory=list, description='Ordered sequence of mission items.')

    # * attribute: created_at
    created_at: float = Field(..., description='Unix timestamp of creation.')

    # * attribute: updated_at
    updated_at: float = Field(..., description='Unix timestamp of last update.')

    # * method: get_item
    def get_item(self, sequence: int) -> Optional[MissionItem]:
        '''
        Retrieve a mission item by sequence number.

        :param sequence: The zero-based sequence index.
        :type sequence: int
        :return: The MissionItem at the given sequence, or None.
        :rtype: Optional[MissionItem]
        '''

        # Search items by sequence number.
        return next((item for item in self.items if item.sequence == sequence), None)

    # * method: item_count
    @property
    def item_count(self) -> int:
        '''
        Return the number of mission items.

        :return: Count of items.
        :rtype: int
        '''

        # Return the length of the items list.
        return len(self.items)

    # * method: has_device
    @property
    def has_device(self) -> bool:
        '''
        Check whether a device is assigned to this mission.

        :return: True if a device_id is set.
        :rtype: bool
        '''

        # Return whether device_id is non-None.
        return self.device_id is not None
