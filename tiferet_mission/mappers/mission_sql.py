"""tiferet_mission Mappers Mission SQL"""

# *** imports

# ** core
from typing import Any, ClassVar, Dict, Optional

# ** infra
from pydantic import Field

# ** app
from tiferet.mappers import TransferObject
from ..domain.mission import Mission, MissionItem
from ..domain.assignment import DeviceAssignment
from .mission import MissionAggregate, MissionItemAggregate
from .assignment import DeviceAssignmentAggregate

# *** mappers

# ** mapper: mission_sql_object
class MissionSqlObject(Mission, TransferObject):
    '''
    SQLite transfer object for the Mission domain object.
    Serializes mission metadata for SQL storage (excludes nested items).
    '''

    # * attribute: _ROLES
    _ROLES: ClassVar[Dict[str, Dict[str, Any]]] = {
        'to_data.sql': {
            'exclude': {'items'},
        },
    }

    # * method: to_sql_dict
    def to_sql_dict(self) -> Dict[str, Any]:
        '''
        Serialize to a flat dict suitable for SQL parameterized insert/update.

        :return: A dict of column name -> value pairs.
        :rtype: Dict[str, Any]
        '''

        # Delegate to to_primitive with the SQL role.
        return self.to_primitive(role='to_data.sql')

    # * method: from_sql_row (static)
    @classmethod
    def from_sql_row(cls, row: Dict[str, Any]) -> 'MissionSqlObject':
        '''
        Construct a MissionSqlObject from a SQL row dict.

        :param row: Dict of column name -> value pairs from a SQL query.
        :type row: Dict[str, Any]
        :return: A new MissionSqlObject instance.
        :rtype: MissionSqlObject
        '''

        # Validate and construct from the row dict.
        return cls.model_validate(row)

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
        data = self.to_primitive(role='to_data.sql')
        data.update(overrides)
        if items is not None:
            data['items'] = items
        else:
            data['items'] = []

        # Construct and return the aggregate.
        return MissionAggregate(**data)


# ** mapper: mission_item_sql_object
class MissionItemSqlObject(MissionItem, TransferObject):
    '''
    SQLite transfer object for the MissionItem domain object.
    Adds mission_id foreign key for relational storage.
    '''

    # * attribute: mission_id
    mission_id: str = Field(..., description='Foreign key to the parent mission.')

    # * attribute: _ROLES
    _ROLES: ClassVar[Dict[str, Dict[str, Any]]] = {
        'to_data.sql': {},
    }

    # * method: to_sql_dict
    def to_sql_dict(self) -> Dict[str, Any]:
        '''
        Serialize to a flat dict suitable for SQL parameterized insert/update.

        :return: A dict of column name -> value pairs.
        :rtype: Dict[str, Any]
        '''

        # Delegate to to_primitive with the SQL role.
        return self.to_primitive(role='to_data.sql')

    # * method: from_sql_row (static)
    @classmethod
    def from_sql_row(cls, row: Dict[str, Any]) -> 'MissionItemSqlObject':
        '''
        Construct a MissionItemSqlObject from a SQL row dict.

        :param row: Dict of column name -> value pairs from a SQL query.
        :type row: Dict[str, Any]
        :return: A new MissionItemSqlObject instance.
        :rtype: MissionItemSqlObject
        '''

        # Validate and construct from the row dict.
        return cls.model_validate(row)

    # * method: map
    def map(self, **overrides) -> MissionItemAggregate:
        '''
        Map to a MissionItemAggregate.

        :param overrides: Additional keyword arguments.
        :type overrides: dict
        :return: A MissionItemAggregate instance.
        :rtype: MissionItemAggregate
        '''

        # Serialize excluding mission_id (not part of domain object).
        data = self.to_primitive(role='to_data.sql')
        data.pop('mission_id', None)
        data.update(overrides)

        # Construct and return the aggregate.
        return MissionItemAggregate(**data)


# ** mapper: device_assignment_sql_object
class DeviceAssignmentSqlObject(DeviceAssignment, TransferObject):
    '''
    SQLite transfer object for the DeviceAssignment domain object.
    '''

    # * attribute: _ROLES
    _ROLES: ClassVar[Dict[str, Dict[str, Any]]] = {
        'to_data.sql': {},
    }

    # * method: to_sql_dict
    def to_sql_dict(self) -> Dict[str, Any]:
        '''
        Serialize to a flat dict suitable for SQL parameterized insert/update.

        :return: A dict of column name -> value pairs.
        :rtype: Dict[str, Any]
        '''

        # Delegate to to_primitive with the SQL role.
        return self.to_primitive(role='to_data.sql')

    # * method: from_sql_row (static)
    @classmethod
    def from_sql_row(cls, row: Dict[str, Any]) -> 'DeviceAssignmentSqlObject':
        '''
        Construct a DeviceAssignmentSqlObject from a SQL row dict.

        :param row: Dict of column name -> value pairs from a SQL query.
        :type row: Dict[str, Any]
        :return: A new DeviceAssignmentSqlObject instance.
        :rtype: DeviceAssignmentSqlObject
        '''

        # Validate and construct from the row dict.
        return cls.model_validate(row)

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
        data = self.to_primitive(role='to_data.sql')
        data.update(overrides)

        # Construct and return the aggregate.
        return DeviceAssignmentAggregate(**data)
