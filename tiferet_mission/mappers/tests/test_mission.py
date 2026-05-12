"""tiferet_mission Mission Mapper Tests"""

# *** imports

# ** infra
import pytest

# ** app
from .settings import AggregateTestBase, TransferObjectTestBase
from ..mission import MissionAggregate, MissionItemAggregate
from ..mission_sql import MissionSqlObject, MissionItemSqlObject

# *** constants

# ** constant: mission_item_aggregate_sample_data
MISSION_ITEM_AGGREGATE_SAMPLE_DATA = {
    'id': 'item-001',
    'sequence': 0,
    'command': 'NAV_WAYPOINT',
    'command_id': 16,
    'category': 'NAV',
    'frame': 'GLOBAL_RELATIVE_ALT',
    'param1': 5.0,
    'param2': 0.0,
    'param3': 0.0,
    'param4': 90.0,
    'latitude': 35.123456,
    'longitude': -120.654321,
    'altitude': 50.0,
    'autocontinue': True,
    'description': 'First waypoint',
}

# ** constant: mission_item_equality_fields
MISSION_ITEM_EQUALITY_FIELDS = [
    'id', 'sequence', 'command', 'command_id', 'category',
    'frame', 'param1', 'param2', 'param3', 'param4',
    'latitude', 'longitude', 'altitude', 'autocontinue', 'description',
]

# ** constant: mission_aggregate_sample_data
MISSION_AGGREGATE_SAMPLE_DATA = {
    'id': 'mission-001',
    'name': 'Survey Alpha',
    'description': 'A survey mission',
    'status': 'draft',
    'drone_type': 'copter',
    'device_id': None,
    'items': [],
    'created_at': 1704067200.0,
    'updated_at': 1704067200.0,
}

# ** constant: mission_equality_fields
MISSION_EQUALITY_FIELDS = [
    'id', 'name', 'description', 'status', 'drone_type',
    'device_id', 'created_at', 'updated_at',
]

# ** constant: mission_item_sql_sample_data
MISSION_ITEM_SQL_SAMPLE_DATA = {
    'id': 'item-001',
    'sequence': 0,
    'command': 'NAV_WAYPOINT',
    'command_id': 16,
    'category': 'NAV',
    'frame': 'GLOBAL_RELATIVE_ALT',
    'param1': 5.0,
    'param2': 0.0,
    'param3': 0.0,
    'param4': 90.0,
    'latitude': 35.123456,
    'longitude': -120.654321,
    'altitude': 50.0,
    'autocontinue': True,
    'description': 'First waypoint',
    'mission_id': 'mission-001',
}

# ** constant: mission_sql_sample_data
MISSION_SQL_SAMPLE_DATA = {
    'id': 'mission-001',
    'name': 'Survey Alpha',
    'description': 'A survey mission',
    'status': 'draft',
    'drone_type': 'copter',
    'device_id': None,
    'items': [],
    'created_at': 1704067200.0,
    'updated_at': 1704067200.0,
}


# *** classes

# ** class: TestMissionItemAggregate
class TestMissionItemAggregate(AggregateTestBase):
    '''Tests for MissionItemAggregate.'''

    aggregate_cls = MissionItemAggregate
    sample_data = MISSION_ITEM_AGGREGATE_SAMPLE_DATA
    equality_fields = MISSION_ITEM_EQUALITY_FIELDS

    set_attribute_params = [
        ('latitude',      40.0,            None),
        ('longitude',     -110.0,          None),
        ('altitude',      100.0,           None),
        ('param1',        10.0,            None),
        ('description',   'Updated desc',  None),
        ('invalid_attr',  'value',         'INVALID_MODEL_ATTRIBUTE'),
    ]

    # *** domain-specific mutation tests

    # ** test: update_position
    def test_update_position(self, aggregate):
        '''Test update_position mutation.'''

        # Apply position update.
        aggregate.update_position(latitude=40.0, longitude=-110.0, altitude=200.0)

        # Assert updated values.
        assert aggregate.latitude == 40.0
        assert aggregate.longitude == -110.0
        assert aggregate.altitude == 200.0

    # ** test: update_params_selective
    def test_update_params_selective(self, aggregate):
        '''Test update_params only modifies provided params.'''

        # Update only param2.
        original_param1 = aggregate.param1
        aggregate.update_params(param2=15.0)

        # Assert param1 unchanged, param2 updated.
        assert aggregate.param1 == original_param1
        assert aggregate.param2 == 15.0


# ** class: TestMissionAggregate
class TestMissionAggregate(AggregateTestBase):
    '''Tests for MissionAggregate.'''

    aggregate_cls = MissionAggregate
    sample_data = MISSION_AGGREGATE_SAMPLE_DATA
    equality_fields = MISSION_EQUALITY_FIELDS

    set_attribute_params = [
        ('name',          'Renamed Mission',  None),
        ('status',        'validated',        None),
        ('device_id',     'drone-001',        None),
        ('invalid_attr',  'value',            'INVALID_MODEL_ATTRIBUTE'),
    ]

    # *** domain-specific mutation tests

    # ** test: add_and_remove_item
    def test_add_and_remove_item(self, aggregate):
        '''Test add_item and remove_item with re-sequencing.'''

        # Add three items.
        item1 = MissionItemAggregate(id='i1', sequence=0, command='NAV_TAKEOFF')
        item2 = MissionItemAggregate(id='i2', sequence=1, command='NAV_WAYPOINT')
        item3 = MissionItemAggregate(id='i3', sequence=2, command='NAV_LAND')
        aggregate.add_item(item1)
        aggregate.add_item(item2)
        aggregate.add_item(item3)
        assert aggregate.item_count == 3

        # Remove middle item and verify re-sequencing.
        removed = aggregate.remove_item('i2')
        assert removed.id == 'i2'
        assert aggregate.item_count == 2
        assert aggregate.items[0].sequence == 0
        assert aggregate.items[1].sequence == 1

    # ** test: reorder_items
    def test_reorder_items(self, aggregate):
        '''Test reorder_items sorts by new sequence numbers.'''

        # Add items.
        aggregate.add_item(MissionItemAggregate(id='i1', sequence=0, command='NAV_TAKEOFF'))
        aggregate.add_item(MissionItemAggregate(id='i2', sequence=1, command='NAV_WAYPOINT'))
        aggregate.add_item(MissionItemAggregate(id='i3', sequence=2, command='NAV_LAND'))

        # Swap first and last.
        aggregate.reorder_items({'i1': 2, 'i3': 0})

        # Assert new order.
        assert aggregate.items[0].id == 'i3'
        assert aggregate.items[2].id == 'i1'

    # ** test: assign_unassign_device
    def test_assign_unassign_device(self, aggregate):
        '''Test device assignment and unassignment.'''

        # Assign.
        aggregate.assign_device('drone-001')
        assert aggregate.has_device is True
        assert aggregate.device_id == 'drone-001'

        # Unassign.
        aggregate.unassign_device()
        assert aggregate.has_device is False

    # ** test: rename
    def test_rename(self, aggregate):
        '''Test rename mutation.'''

        # Rename the mission.
        aggregate.rename('New Name')
        assert aggregate.name == 'New Name'


# ** class: TestMissionItemSqlObject
class TestMissionItemSqlObject(TransferObjectTestBase):
    '''Tests for MissionItemSqlObject.'''

    transfer_cls = MissionItemSqlObject
    aggregate_cls = MissionItemAggregate
    sample_data = MISSION_ITEM_SQL_SAMPLE_DATA
    aggregate_sample_data = MISSION_ITEM_AGGREGATE_SAMPLE_DATA
    equality_fields = MISSION_ITEM_EQUALITY_FIELDS

    # * method: make_aggregate
    def make_aggregate(self, data=None):
        '''Override: construct from aggregate data (without mission_id).'''
        return MissionItemAggregate(**(data if data is not None else self.aggregate_sample_data))

    # * method: test_from_model
    def test_from_model(self, aggregate):
        '''Override: from_model requires mission_id override for this SQL transfer object.'''
        obj = self.transfer_cls.from_model(aggregate, mission_id='mission-001')
        assert isinstance(obj, self.transfer_cls)
        assert obj.mission_id == 'mission-001'

    # * method: test_round_trip
    def test_round_trip(self, aggregate):
        '''Override: round-trip must supply mission_id to from_model.'''
        obj = self.transfer_cls.from_model(aggregate, mission_id='mission-001')
        round_tripped = obj.map()
        assert isinstance(round_tripped, self.aggregate_cls)
        self.assert_model_matches(round_tripped, self.aggregate_sample_data)

    # *** SQL-specific tests

    # ** test: to_sql_dict
    def test_to_sql_dict(self):
        '''Test that to_sql_dict returns expected keys.'''

        # Construct and serialize.
        obj = self.transfer_cls.model_validate(self.sample_data)
        sql_dict = obj.to_sql_dict()

        # Assert mission_id is included.
        assert 'mission_id' in sql_dict
        assert sql_dict['mission_id'] == 'mission-001'

    # ** test: from_sql_row
    def test_from_sql_row(self):
        '''Test construction from SQL row dict.'''

        # Construct from row.
        obj = self.transfer_cls.from_sql_row(self.sample_data)
        assert isinstance(obj, self.transfer_cls)
        assert obj.id == 'item-001'


# ** class: TestMissionSqlObject
class TestMissionSqlObject(TransferObjectTestBase):
    '''Tests for MissionSqlObject.'''

    transfer_cls = MissionSqlObject
    aggregate_cls = MissionAggregate
    sample_data = MISSION_SQL_SAMPLE_DATA
    aggregate_sample_data = MISSION_AGGREGATE_SAMPLE_DATA
    equality_fields = MISSION_EQUALITY_FIELDS

    # *** SQL-specific tests

    # ** test: to_sql_dict_excludes_items
    def test_to_sql_dict_excludes_items(self):
        '''Test that to_sql_dict excludes nested items.'''

        # Construct and serialize.
        obj = self.transfer_cls.model_validate(self.sample_data)
        sql_dict = obj.to_sql_dict()

        # Assert items are excluded.
        assert 'items' not in sql_dict

    # ** test: from_sql_row
    def test_from_sql_row(self):
        '''Test construction from SQL row dict.'''

        # Construct from row.
        obj = self.transfer_cls.from_sql_row(self.sample_data)
        assert isinstance(obj, self.transfer_cls)
        assert obj.id == 'mission-001'
