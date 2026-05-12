"""tiferet_mission Mappers Mission H5"""

# *** imports

# ** core
from typing import Any, ClassVar, Dict, Optional

# ** infra
import tables
from pydantic import AliasChoices, Field

# ** app
from tiferet_h5.mappers import TableObject, NodeObject
from ..domain.mission import Mission, MissionItem
from ..domain.assignment import DeviceAssignment
from .mission import MissionAggregate, MissionItemAggregate
from .assignment import DeviceAssignmentAggregate

# *** mappers

# ** mapper: mission_node_object
class MissionNodeObject(Mission, NodeObject):
    '''
    HDF5 node-attribute transfer object for Mission metadata.
    Serializes mission-level scalar fields as group attributes.
    '''

    # * attribute: _ROLES
    _ROLES: ClassVar[Dict[str, Dict[str, Any]]] = {
        'to_h5.attrs': {
            'by_alias': True,
            'exclude': {'items'},
        },
    }

    # * method: map
    def map(self, items=None, **overrides) -> MissionAggregate:
        '''
        Map to a MissionAggregate, optionally injecting items.

        :param items: Optional list of MissionItemAggregate instances.
        :type items: list | None
        :param overrides: Additional keyword arguments.
        :type overrides: dict
        :return: A MissionAggregate instance.
        :rtype: MissionAggregate
        '''

        # Serialize to dict excluding items, then merge overrides.
        data = self.to_primitive(role='to_h5.attrs')
        data.update(overrides)
        if items is not None:
            data['items'] = items
        else:
            data['items'] = []

        # Construct and return the aggregate.
        return MissionAggregate(**data)


# ** mapper: mission_item_table_object
class MissionItemTableObject(MissionItem, TableObject):
    '''
    HDF5 table-row transfer object for MissionItem.
    '''

    # * attribute: _H5_TYPES
    _H5_TYPES: ClassVar[Dict[str, Any]] = {
        'id':           tables.StringCol(64),
        'seq':          tables.Int32Col(),
        'cmd':          tables.StringCol(64),
        'cmd_id':       tables.Int32Col(),
        'cat':          tables.StringCol(16),
        'frame':        tables.StringCol(32),
        'p1':           tables.Float64Col(),
        'p2':           tables.Float64Col(),
        'p3':           tables.Float64Col(),
        'p4':           tables.Float64Col(),
        'lat':          tables.Float64Col(),
        'lon':          tables.Float64Col(),
        'alt':          tables.Float64Col(),
        'autocont':     tables.BoolCol(),
        'desc':         tables.StringCol(256),
    }

    # * attribute: sequence (alias)
    sequence: int = Field(
        ...,
        serialization_alias='seq',
        validation_alias=AliasChoices('seq', 'sequence'),
        description='Zero-based order in the mission.',
    )

    # * attribute: command (alias)
    command: str = Field(
        ...,
        serialization_alias='cmd',
        validation_alias=AliasChoices('cmd', 'command'),
        description='MAV_CMD name.',
    )

    # * attribute: command_id (alias)
    command_id: int = Field(
        default=0,
        serialization_alias='cmd_id',
        validation_alias=AliasChoices('cmd_id', 'command_id'),
        description='MAV_CMD numeric code.',
    )

    # * attribute: category (alias)
    category: str = Field(
        default='NAV',
        serialization_alias='cat',
        validation_alias=AliasChoices('cat', 'category'),
        description='Command category.',
    )

    # * attribute: param1 (alias)
    param1: float = Field(
        default=0.0,
        serialization_alias='p1',
        validation_alias=AliasChoices('p1', 'param1'),
    )

    # * attribute: param2 (alias)
    param2: float = Field(
        default=0.0,
        serialization_alias='p2',
        validation_alias=AliasChoices('p2', 'param2'),
    )

    # * attribute: param3 (alias)
    param3: float = Field(
        default=0.0,
        serialization_alias='p3',
        validation_alias=AliasChoices('p3', 'param3'),
    )

    # * attribute: param4 (alias)
    param4: float = Field(
        default=0.0,
        serialization_alias='p4',
        validation_alias=AliasChoices('p4', 'param4'),
    )

    # * attribute: latitude (alias)
    latitude: float = Field(
        default=0.0,
        serialization_alias='lat',
        validation_alias=AliasChoices('lat', 'latitude'),
    )

    # * attribute: longitude (alias)
    longitude: float = Field(
        default=0.0,
        serialization_alias='lon',
        validation_alias=AliasChoices('lon', 'longitude'),
    )

    # * attribute: altitude (alias)
    altitude: float = Field(
        default=0.0,
        serialization_alias='alt',
        validation_alias=AliasChoices('alt', 'altitude'),
    )

    # * attribute: autocontinue (alias)
    autocontinue: bool = Field(
        default=True,
        serialization_alias='autocont',
        validation_alias=AliasChoices('autocont', 'autocontinue'),
    )

    # * attribute: description (alias)
    description: Optional[str] = Field(
        default=None,
        serialization_alias='desc',
        validation_alias=AliasChoices('desc', 'description'),
    )

    # * method: map
    def map(self, **overrides) -> MissionItemAggregate:
        '''
        Map to a MissionItemAggregate.

        :param overrides: Additional keyword arguments.
        :type overrides: dict
        :return: A MissionItemAggregate instance.
        :rtype: MissionItemAggregate
        '''

        # Serialize to dict using canonical names and merge overrides.
        data = self.to_primitive()
        data.update(overrides)

        # Construct and return the aggregate.
        return MissionItemAggregate(**data)


# ** mapper: device_assignment_table_object
class DeviceAssignmentTableObject(DeviceAssignment, TableObject):
    '''
    HDF5 table-row transfer object for DeviceAssignment.
    '''

    # * attribute: _H5_TYPES
    _H5_TYPES: ClassVar[Dict[str, Any]] = {
        'mission_id':   tables.StringCol(64),
        'device_id':    tables.StringCol(64),
        'drone_type':   tables.StringCol(16),
        'assigned_at':  tables.StringCol(32),
        'status':       tables.StringCol(16),
    }

    # * method: map
    def map(self, **overrides) -> DeviceAssignmentAggregate:
        '''
        Map to a DeviceAssignmentAggregate.

        :param overrides: Additional keyword arguments.
        :type overrides: dict
        :return: A DeviceAssignmentAggregate instance.
        :rtype: DeviceAssignmentAggregate
        '''

        # Serialize and merge overrides.
        data = self.to_primitive()
        data.update(overrides)

        # Construct and return the aggregate.
        return DeviceAssignmentAggregate(**data)
