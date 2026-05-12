"""tiferet_mission Repository Integration Tests"""

# *** imports

# ** infra
import pytest

# ** app
from tiferet_mission.repos.sqlite import MissionSqliteRepository
from tiferet_mission.mappers.mission import MissionAggregate, MissionItemAggregate
from tiferet_mission.mappers.assignment import DeviceAssignmentAggregate

# *** fixtures

# ** fixture: repo
@pytest.fixture
def repo(tmp_path):
    '''
    MissionSqliteRepository backed by a temporary SQLite file.
    '''

    # Create a repository pointing at a temp database.
    db_path = str(tmp_path / 'test_missions.db')
    return MissionSqliteRepository(db_path=db_path)


# ** fixture: sample_mission
@pytest.fixture
def sample_mission():
    '''
    A sample MissionAggregate for testing.
    '''

    # Return a basic draft mission.
    return MissionAggregate(
        id='m-int-test',
        name='Integration Test Mission',
        description='Testing the SQLite repo',
        status='draft',
        drone_type='copter',
        items=[
            MissionItemAggregate(
                id='item-1', sequence=0, command='NAV_TAKEOFF',
                altitude=10.0,
            ),
            MissionItemAggregate(
                id='item-2', sequence=1, command='NAV_WAYPOINT',
                latitude=35.0, longitude=-120.0, altitude=50.0,
            ),
            MissionItemAggregate(
                id='item-3', sequence=2, command='NAV_RETURN_TO_LAUNCH',
            ),
        ],
        created_at=1704067200.0,
        updated_at=1704067200.0,
    )


# *** tests

# ** test: save_and_get_mission
def test_save_and_get_mission(repo, sample_mission):
    '''
    Test saving and retrieving a mission with items via the SQLite repo.
    '''

    # Save the mission.
    repo.save(sample_mission)

    # Retrieve it.
    loaded = repo.get('m-int-test')

    # Assert mission metadata.
    assert loaded is not None
    assert loaded.id == 'm-int-test'
    assert loaded.name == 'Integration Test Mission'
    assert loaded.drone_type == 'copter'
    assert loaded.status == 'draft'

    # Assert items were round-tripped.
    assert loaded.item_count == 3
    assert loaded.items[0].command == 'NAV_TAKEOFF'
    assert loaded.items[1].latitude == 35.0
    assert loaded.items[2].command == 'NAV_RETURN_TO_LAUNCH'


# ** test: exists
def test_exists(repo, sample_mission):
    '''
    Test the exists method.
    '''

    # Mission does not exist yet.
    assert repo.exists('m-int-test') is False

    # Save and check.
    repo.save(sample_mission)
    assert repo.exists('m-int-test') is True


# ** test: list_missions_no_filter
def test_list_missions_no_filter(repo, sample_mission):
    '''
    Test listing all missions without filters.
    '''

    # Save a mission.
    repo.save(sample_mission)

    # List all.
    missions = repo.list()
    assert len(missions) == 1
    assert missions[0].id == 'm-int-test'


# ** test: list_missions_with_filter
def test_list_missions_with_filter(repo, sample_mission):
    '''
    Test listing missions with drone_type filter.
    '''

    # Save a copter mission.
    repo.save(sample_mission)

    # Filter by copter.
    copter_missions = repo.list(drone_type='copter')
    assert len(copter_missions) == 1

    # Filter by plane (should be empty).
    plane_missions = repo.list(drone_type='plane')
    assert len(plane_missions) == 0


# ** test: delete_mission
def test_delete_mission(repo, sample_mission):
    '''
    Test deleting a mission removes it and its items.
    '''

    # Save then delete.
    repo.save(sample_mission)
    repo.delete('m-int-test')

    # Verify it's gone.
    assert repo.exists('m-int-test') is False
    assert repo.get('m-int-test') is None


# ** test: update_mission
def test_update_mission(repo, sample_mission):
    '''
    Test that saving an existing mission updates it (upsert behavior).
    '''

    # Save initial version.
    repo.save(sample_mission)

    # Modify and re-save.
    sample_mission.rename('Updated Name')
    sample_mission.set_status('validated')
    repo.save(sample_mission)

    # Reload and verify.
    loaded = repo.get('m-int-test')
    assert loaded.name == 'Updated Name'
    assert loaded.status == 'validated'


# ** test: save_and_get_assignment
def test_save_and_get_assignment(repo, sample_mission):
    '''
    Test saving and retrieving a device assignment.
    '''

    # Save the mission first (foreign key).
    repo.save(sample_mission)

    # Create and save an assignment.
    assignment = DeviceAssignmentAggregate(
        mission_id='m-int-test',
        device_id='drone-001',
        drone_type='copter',
        assigned_at=1704110400.0,
        status='active',
    )
    repo.save_assignment(assignment)

    # Retrieve it.
    loaded = repo.get_assignment('m-int-test')
    assert loaded is not None
    assert loaded.device_id == 'drone-001'
    assert loaded.drone_type == 'copter'
    assert loaded.status == 'active'


# ** test: delete_assignment
def test_delete_assignment(repo, sample_mission):
    '''
    Test deleting a device assignment.
    '''

    # Save mission and assignment.
    repo.save(sample_mission)
    assignment = DeviceAssignmentAggregate(
        mission_id='m-int-test',
        device_id='drone-001',
        drone_type='copter',
        assigned_at=1704110400.0,
    )
    repo.save_assignment(assignment)

    # Delete and verify.
    repo.delete_assignment('m-int-test')
    assert repo.get_assignment('m-int-test') is None


# ** test: get_nonexistent_returns_none
def test_get_nonexistent_returns_none(repo):
    '''
    Test that get returns None for a non-existent mission.
    '''

    # Retrieve a non-existent mission.
    assert repo.get('nonexistent') is None


# ** test: delete_idempotent
def test_delete_idempotent(repo):
    '''
    Test that deleting a non-existent mission does not raise.
    '''

    # Should not raise.
    repo.delete('nonexistent')
