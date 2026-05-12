"""tiferet_mission Domain Tests"""

# *** imports

# ** infra
import pytest

# ** app
from tiferet_mission.domain.mission import Mission, MissionItem
from tiferet_mission.domain.assignment import DeviceAssignment

# *** tests

# ** test: mission_item_basic_construction
def test_mission_item_basic_construction():
    '''
    Test that a MissionItem can be constructed with required fields.
    '''

    # Construct a basic waypoint item.
    item = MissionItem(id='item-1', sequence=0, command='NAV_WAYPOINT')

    # Assert the command metadata was derived.
    assert item.command_id == 16
    assert item.category == 'NAV'
    assert item.frame == 'GLOBAL_RELATIVE_ALT'
    assert item.autocontinue is True


# ** test: mission_item_derives_command_fields
def test_mission_item_derives_command_fields():
    '''
    Test that command_id and category are auto-derived from command name.
    '''

    # Construct a takeoff item.
    item = MissionItem(id='item-2', sequence=0, command='NAV_TAKEOFF')

    # Assert derived fields.
    assert item.command_id == 22
    assert item.category == 'NAV'


# ** test: mission_item_unknown_command_preserves_defaults
def test_mission_item_unknown_command_preserves_defaults():
    '''
    Test that an unknown command name preserves default command_id and category.
    '''

    # Construct an item with an unknown command.
    item = MissionItem(id='item-3', sequence=0, command='CUSTOM_CMD')

    # Assert defaults are preserved.
    assert item.command_id == 0
    assert item.category == 'NAV'


# ** test: mission_item_do_command
def test_mission_item_do_command():
    '''
    Test that a DO command derives category correctly.
    '''

    # Construct a DO command item.
    item = MissionItem(id='item-4', sequence=1, command='DO_CHANGE_SPEED')

    # Assert the category is DO.
    assert item.command_id == 178
    assert item.category == 'DO'


# ** test: mission_construction
def test_mission_construction():
    '''
    Test that a Mission can be constructed with required fields.
    '''

    # Construct a mission.
    mission = Mission(
        id='mission-1',
        name='Test Flight',
        drone_type='copter',
        created_at=1704067200.0,
        updated_at=1704067200.0,
    )

    # Assert basic attributes.
    assert mission.id == 'mission-1'
    assert mission.status == 'draft'
    assert mission.item_count == 0
    assert mission.has_device is False


# ** test: mission_with_items
def test_mission_with_items():
    '''
    Test that a Mission can be constructed with items.
    '''

    # Construct items.
    items = [
        MissionItem(id='i1', sequence=0, command='NAV_TAKEOFF'),
        MissionItem(id='i2', sequence=1, command='NAV_WAYPOINT', latitude=35.0, longitude=-120.0, altitude=50.0),
        MissionItem(id='i3', sequence=2, command='NAV_LAND'),
    ]

    # Construct the mission with items.
    mission = Mission(
        id='mission-2',
        name='Full Flight',
        drone_type='copter',
        items=items,
        created_at=1704067200.0,
        updated_at=1704067200.0,
    )

    # Assert item access.
    assert mission.item_count == 3
    assert mission.get_item(1).command == 'NAV_WAYPOINT'
    assert mission.get_item(5) is None


# ** test: device_assignment_construction
def test_device_assignment_construction():
    '''
    Test that a DeviceAssignment can be constructed.
    '''

    # Construct an assignment.
    assignment = DeviceAssignment(
        mission_id='mission-1',
        device_id='drone-001',
        drone_type='copter',
        assigned_at=1704067200.0,
    )

    # Assert attributes.
    assert assignment.status == 'active'
    assert assignment.drone_type == 'copter'
