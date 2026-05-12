"""tiferet_mission Assignment Mapper Tests"""

# *** imports

# ** infra
import pytest

# ** app
from tiferet.mappers.tests.settings import AggregateTestBase, TransferObjectTestBase
from ..assignment import DeviceAssignmentAggregate
from ..mission_sql import DeviceAssignmentSqlObject

# *** constants

# ** constant: assignment_sample_data
ASSIGNMENT_SAMPLE_DATA = {
    'mission_id': 'mission-001',
    'device_id': 'drone-001',
    'drone_type': 'copter',
    'assigned_at': 1704110400.0,
    'status': 'active',
}

# ** constant: assignment_equality_fields
ASSIGNMENT_EQUALITY_FIELDS = [
    'mission_id', 'device_id', 'drone_type', 'assigned_at', 'status',
]


# *** classes

# ** class: TestDeviceAssignmentAggregate
class TestDeviceAssignmentAggregate(AggregateTestBase):
    '''Tests for DeviceAssignmentAggregate.'''

    aggregate_cls = DeviceAssignmentAggregate
    sample_data = ASSIGNMENT_SAMPLE_DATA
    equality_fields = ASSIGNMENT_EQUALITY_FIELDS

    set_attribute_params = [
        ('status',        'released',   None),
        ('invalid_attr',  'value',      'INVALID_MODEL_ATTRIBUTE'),
    ]

    # *** domain-specific mutation tests

    # ** test: release
    def test_release(self, aggregate):
        '''Test release mutation.'''

        # Release the assignment.
        aggregate.release()
        assert aggregate.status == 'released'

    # ** test: reject
    def test_reject(self, aggregate):
        '''Test reject mutation.'''

        # Reject the assignment.
        aggregate.reject()
        assert aggregate.status == 'rejected'


# ** class: TestDeviceAssignmentSqlObject
class TestDeviceAssignmentSqlObject(TransferObjectTestBase):
    '''Tests for DeviceAssignmentSqlObject.'''

    transfer_cls = DeviceAssignmentSqlObject
    aggregate_cls = DeviceAssignmentAggregate
    sample_data = ASSIGNMENT_SAMPLE_DATA
    aggregate_sample_data = ASSIGNMENT_SAMPLE_DATA
    equality_fields = ASSIGNMENT_EQUALITY_FIELDS

    # *** SQL-specific tests

    # ** test: to_sql_dict
    def test_to_sql_dict(self):
        '''Test that to_sql_dict returns all expected keys.'''

        # Construct and serialize.
        obj = self.transfer_cls.model_validate(self.sample_data)
        sql_dict = obj.to_sql_dict()

        # Assert key fields present.
        assert sql_dict['mission_id'] == 'mission-001'
        assert sql_dict['device_id'] == 'drone-001'
        assert sql_dict['status'] == 'active'

    # ** test: from_sql_row
    def test_from_sql_row(self):
        '''Test construction from SQL row dict.'''

        # Construct from row.
        obj = self.transfer_cls.from_sql_row(self.sample_data)
        assert isinstance(obj, self.transfer_cls)
        assert obj.mission_id == 'mission-001'
