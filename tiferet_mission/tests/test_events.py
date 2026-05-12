"""tiferet_mission Event Tests"""

# *** imports

# ** infra
import pytest
from unittest import mock

# ** app
from tiferet.events import DomainEvent
from tiferet.assets.exceptions import TiferetError
from tiferet_mission.events.mission import (
    CreateMission,
    GetMission,
    DeleteMission,
    AddMissionItem,
    AssignDevice,
    ValidateMission,
    UpdateMissionStatus,
)
from tiferet_mission.interfaces.mission import MissionService
from tiferet_mission.interfaces.device import DeviceRegistryService
from tiferet_mission.mappers.mission import MissionAggregate, MissionItemAggregate

# *** fixtures

# ** fixture: mock_mission_service
@pytest.fixture
def mock_mission_service():
    '''
    Mock MissionService for testing.
    '''
    return mock.Mock(spec=MissionService)


# ** fixture: mock_device_registry
@pytest.fixture
def mock_device_registry():
    '''
    Mock DeviceRegistryService for testing.
    '''
    return mock.Mock(spec=DeviceRegistryService)


# ** fixture: sample_mission
@pytest.fixture
def sample_mission():
    '''
    Sample MissionAggregate for testing.
    '''
    return MissionAggregate(
        id='m-test',
        name='Test Mission',
        drone_type='copter',
        status='draft',
        items=[],
        created_at=1704067200.0,
        updated_at=1704067200.0,
    )

# *** tests

# ** test: create_mission_success
def test_create_mission_success(mock_mission_service):
    '''
    Test successful mission creation.
    '''

    # Arrange: no existing mission.
    mock_mission_service.exists.return_value = False

    # Execute.
    result = DomainEvent.handle(
        CreateMission,
        dependencies={'mission_service': mock_mission_service},
        name='Survey Alpha',
        drone_type='copter',
        id='m-001',
    )

    # Assert the mission was created and saved.
    assert result.id == 'm-001'
    assert result.name == 'Survey Alpha'
    assert result.drone_type == 'copter'
    assert result.status == 'draft'
    mock_mission_service.save.assert_called_once()


# ** test: create_mission_duplicate_fails
def test_create_mission_duplicate_fails(mock_mission_service):
    '''
    Test that creating a duplicate mission raises an error.
    '''

    # Arrange: mission already exists.
    mock_mission_service.exists.return_value = True

    # Execute and expect failure.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            CreateMission,
            dependencies={'mission_service': mock_mission_service},
            name='Dupe',
            drone_type='copter',
            id='m-existing',
        )


# ** test: get_mission_success
def test_get_mission_success(mock_mission_service, sample_mission):
    '''
    Test successful mission retrieval.
    '''

    # Arrange.
    mock_mission_service.get.return_value = sample_mission

    # Execute.
    result = DomainEvent.handle(
        GetMission,
        dependencies={'mission_service': mock_mission_service},
        id='m-test',
    )

    # Assert.
    assert result is sample_mission


# ** test: get_mission_not_found
def test_get_mission_not_found(mock_mission_service):
    '''
    Test that getting a non-existent mission raises an error.
    '''

    # Arrange.
    mock_mission_service.get.return_value = None

    # Execute and expect failure.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            GetMission,
            dependencies={'mission_service': mock_mission_service},
            id='m-nonexistent',
        )


# ** test: delete_mission_success
def test_delete_mission_success(mock_mission_service, sample_mission):
    '''
    Test successful mission deletion (draft status).
    '''

    # Arrange.
    mock_mission_service.get.return_value = sample_mission

    # Execute.
    DomainEvent.handle(
        DeleteMission,
        dependencies={'mission_service': mock_mission_service},
        id='m-test',
    )

    # Assert deletion was called.
    mock_mission_service.delete.assert_called_once_with('m-test')


# ** test: delete_mission_non_deletable_fails
def test_delete_mission_non_deletable_fails(mock_mission_service, sample_mission):
    '''
    Test that deleting a non-draft mission raises an error.
    '''

    # Arrange: mission is executing.
    sample_mission.set_status('executing')
    mock_mission_service.get.return_value = sample_mission

    # Execute and expect failure.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            DeleteMission,
            dependencies={'mission_service': mock_mission_service},
            id='m-test',
        )


# ** test: add_mission_item_success
def test_add_mission_item_success(mock_mission_service, sample_mission):
    '''
    Test adding a mission item to a draft mission.
    '''

    # Arrange.
    mock_mission_service.get.return_value = sample_mission

    # Execute.
    result = DomainEvent.handle(
        AddMissionItem,
        dependencies={'mission_service': mock_mission_service},
        id='m-test',
        command='NAV_WAYPOINT',
        latitude=35.0,
        longitude=-120.0,
        altitude=50.0,
    )

    # Assert item was added.
    assert result.item_count == 1
    assert result.items[0].command == 'NAV_WAYPOINT'
    assert result.items[0].latitude == 35.0


# ** test: add_mission_item_invalid_command_fails
def test_add_mission_item_invalid_command_fails(mock_mission_service, sample_mission):
    '''
    Test that adding an item with an invalid command raises an error.
    '''

    # Arrange.
    mock_mission_service.get.return_value = sample_mission

    # Execute and expect failure.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            AddMissionItem,
            dependencies={'mission_service': mock_mission_service},
            id='m-test',
            command='INVALID_CMD',
        )


# ** test: assign_device_success
def test_assign_device_success(mock_mission_service, mock_device_registry, sample_mission):
    '''
    Test successful device assignment with matching drone type.
    '''

    # Arrange.
    mock_mission_service.get.return_value = sample_mission
    mock_device_registry.device_exists.return_value = True
    mock_device_registry.get_device_type.return_value = 'copter'

    # Execute.
    result = DomainEvent.handle(
        AssignDevice,
        dependencies={
            'mission_service': mock_mission_service,
            'device_registry_service': mock_device_registry,
        },
        id='m-test',
        device_id='drone-001',
    )

    # Assert device was assigned and status updated.
    assert result.device_id == 'drone-001'
    assert result.status == 'assigned'
    mock_mission_service.save_assignment.assert_called_once()


# ** test: assign_device_type_mismatch_fails
def test_assign_device_type_mismatch_fails(mock_mission_service, mock_device_registry, sample_mission):
    '''
    Test that assigning a device with wrong drone type raises an error.
    '''

    # Arrange: mission needs copter, device is plane.
    mock_mission_service.get.return_value = sample_mission
    mock_device_registry.device_exists.return_value = True
    mock_device_registry.get_device_type.return_value = 'plane'

    # Execute and expect failure.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            AssignDevice,
            dependencies={
                'mission_service': mock_mission_service,
                'device_registry_service': mock_device_registry,
            },
            id='m-test',
            device_id='plane-001',
        )


# ** test: validate_mission_success
def test_validate_mission_success(mock_mission_service):
    '''
    Test successful mission validation for a copter mission.
    '''

    # Arrange: a structurally valid copter mission.
    mission = MissionAggregate(
        id='m-valid', name='Valid Flight', drone_type='copter',
        status='draft',
        items=[
            MissionItemAggregate(id='i1', sequence=0, command='NAV_TAKEOFF', altitude=10.0),
            MissionItemAggregate(id='i2', sequence=1, command='NAV_WAYPOINT', latitude=35.0, longitude=-120.0, altitude=50.0),
            MissionItemAggregate(id='i3', sequence=2, command='NAV_RETURN_TO_LAUNCH'),
        ],
        created_at=1704067200.0,
        updated_at=1704067200.0,
    )
    mock_mission_service.get.return_value = mission

    # Execute.
    result = DomainEvent.handle(
        ValidateMission,
        dependencies={'mission_service': mock_mission_service},
        id='m-valid',
    )

    # Assert status updated to validated.
    assert result.status == 'validated'


# ** test: validate_mission_empty_fails
def test_validate_mission_empty_fails(mock_mission_service, sample_mission):
    '''
    Test that validating an empty mission raises an error.
    '''

    # Arrange: mission has no items.
    mock_mission_service.get.return_value = sample_mission

    # Execute and expect failure.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            ValidateMission,
            dependencies={'mission_service': mock_mission_service},
            id='m-test',
        )


# ** test: update_mission_status_valid_transition
def test_update_mission_status_valid_transition(mock_mission_service, sample_mission):
    '''
    Test a valid status transition from draft to aborted.
    '''

    # Arrange.
    mock_mission_service.get.return_value = sample_mission

    # Execute.
    result = DomainEvent.handle(
        UpdateMissionStatus,
        dependencies={'mission_service': mock_mission_service},
        id='m-test',
        status='aborted',
    )

    # Assert status was updated.
    assert result.status == 'aborted'


# ** test: update_mission_status_invalid_transition_fails
def test_update_mission_status_invalid_transition_fails(mock_mission_service, sample_mission):
    '''
    Test that an invalid status transition raises an error.
    '''

    # Arrange: draft -> executing is not allowed.
    mock_mission_service.get.return_value = sample_mission

    # Execute and expect failure.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            UpdateMissionStatus,
            dependencies={'mission_service': mock_mission_service},
            id='m-test',
            status='executing',
        )
