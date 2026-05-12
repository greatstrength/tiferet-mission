"""tiferet_mission Events Mission"""

# *** imports

# ** core
import time
import uuid
from typing import Any, Dict, List, Optional

# ** app
from tiferet.events import DomainEvent
from ..assets import constants as const
from ..domain.settings import MAV_COMMANDS, VALID_STATUS_TRANSITIONS
from ..interfaces.mission import MissionService
from ..interfaces.device import DeviceRegistryService
from ..mappers.mission import MissionAggregate, MissionItemAggregate
from ..mappers.assignment import DeviceAssignmentAggregate

# *** events

# ** event: create_mission
class CreateMission(DomainEvent):
    '''
    Event to create a new mission plan in draft status.
    '''

    # * attribute: mission_service
    mission_service: MissionService

    # * init
    def __init__(self, mission_service: MissionService):
        '''
        Initialize the CreateMission event.

        :param mission_service: The mission service for persistence.
        :type mission_service: MissionService
        '''

        # Set the mission service dependency.
        self.mission_service = mission_service

    # * method: execute
    @DomainEvent.parameters_required(['name', 'drone_type'])
    def execute(self,
            name: str,
            drone_type: str,
            description: Optional[str] = None,
            id: Optional[str] = None,
            **kwargs,
        ) -> MissionAggregate:
        '''
        Create a new mission.

        :param name: The mission name.
        :type name: str
        :param drone_type: The required drone type.
        :type drone_type: str
        :param description: Optional description.
        :type description: str | None
        :param id: Optional explicit mission ID.
        :type id: str | None
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The created mission aggregate.
        :rtype: MissionAggregate
        '''

        # Generate mission ID and timestamps.
        mission_id = id or str(uuid.uuid4())
        now = time.time()

        # Verify uniqueness.
        self.verify(
            expression=not self.mission_service.exists(mission_id),
            error_code=const.MISSION_ALREADY_EXISTS_ID,
            mission_id=mission_id,
        )

        # Construct the mission aggregate.
        mission = MissionAggregate(
            id=mission_id,
            name=name,
            description=description,
            status='draft',
            drone_type=drone_type,
            items=[],
            created_at=now,
            updated_at=now,
        )

        # Persist the new mission.
        self.mission_service.save(mission)

        # Return the created mission.
        return mission


# ** event: get_mission
class GetMission(DomainEvent):
    '''
    Event to retrieve a mission by its identifier.
    '''

    # * attribute: mission_service
    mission_service: MissionService

    # * init
    def __init__(self, mission_service: MissionService):
        '''
        Initialize the GetMission event.

        :param mission_service: The mission service for retrieval.
        :type mission_service: MissionService
        '''

        # Set the mission service dependency.
        self.mission_service = mission_service

    # * method: execute
    @DomainEvent.parameters_required(['id'])
    def execute(self, id: str, **kwargs) -> MissionAggregate:
        '''
        Retrieve a mission by ID.

        :param id: The mission identifier.
        :type id: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The retrieved mission aggregate.
        :rtype: MissionAggregate
        '''

        # Retrieve the mission from the service.
        mission = self.mission_service.get(id)

        # Verify the mission exists.
        self.verify(
            expression=mission is not None,
            error_code=const.MISSION_NOT_FOUND_ID,
            mission_id=id,
        )

        # Return the retrieved mission.
        return mission


# ** event: list_missions
class ListMissions(DomainEvent):
    '''
    Event to list missions with optional filters.
    '''

    # * attribute: mission_service
    mission_service: MissionService

    # * init
    def __init__(self, mission_service: MissionService):
        '''
        Initialize the ListMissions event.

        :param mission_service: The mission service for listing.
        :type mission_service: MissionService
        '''

        # Set the mission service dependency.
        self.mission_service = mission_service

    # * method: execute
    def execute(self,
            drone_type: Optional[str] = None,
            status: Optional[str] = None,
            **kwargs,
        ) -> List[MissionAggregate]:
        '''
        List missions with optional filters.

        :param drone_type: Optional drone type filter.
        :type drone_type: str | None
        :param status: Optional status filter.
        :type status: str | None
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: A list of mission aggregates.
        :rtype: List[MissionAggregate]
        '''

        # Delegate to the mission service list method.
        return self.mission_service.list(drone_type=drone_type, status=status)


# ** event: delete_mission
class DeleteMission(DomainEvent):
    '''
    Event to delete a mission. Only draft or aborted missions may be deleted.
    '''

    # * attribute: mission_service
    mission_service: MissionService

    # * init
    def __init__(self, mission_service: MissionService):
        '''
        Initialize the DeleteMission event.

        :param mission_service: The mission service for deletion.
        :type mission_service: MissionService
        '''

        # Set the mission service dependency.
        self.mission_service = mission_service

    # * method: execute
    @DomainEvent.parameters_required(['id'])
    def execute(self, id: str, **kwargs) -> None:
        '''
        Delete a mission by ID.

        :param id: The mission identifier.
        :type id: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        '''

        # Retrieve the mission.
        mission = self.mission_service.get(id)

        # Verify the mission exists.
        self.verify(
            expression=mission is not None,
            error_code=const.MISSION_NOT_FOUND_ID,
            mission_id=id,
        )

        # Verify the mission is in a deletable status.
        self.verify(
            expression=mission.status in ('draft', 'aborted'),
            error_code=const.MISSION_NOT_DELETABLE_ID,
            mission_id=id,
            status=mission.status,
        )

        # Delete the mission and its assignment.
        self.mission_service.delete_assignment(id)
        self.mission_service.delete(id)


# ** event: add_mission_item
class AddMissionItem(DomainEvent):
    '''
    Event to add a mission item (waypoint/command) to a mission.
    '''

    # * attribute: mission_service
    mission_service: MissionService

    # * init
    def __init__(self, mission_service: MissionService):
        '''
        Initialize the AddMissionItem event.

        :param mission_service: The mission service for persistence.
        :type mission_service: MissionService
        '''

        # Set the mission service dependency.
        self.mission_service = mission_service

    # * method: execute
    @DomainEvent.parameters_required(['id', 'command'])
    def execute(self,
            id: str,
            command: str,
            frame: str = 'GLOBAL_RELATIVE_ALT',
            param1: float = 0.0,
            param2: float = 0.0,
            param3: float = 0.0,
            param4: float = 0.0,
            latitude: float = 0.0,
            longitude: float = 0.0,
            altitude: float = 0.0,
            autocontinue: bool = True,
            description: Optional[str] = None,
            item_id: Optional[str] = None,
            **kwargs,
        ) -> MissionAggregate:
        '''
        Add a mission item to a mission.

        :param id: The mission identifier.
        :type id: str
        :param command: The MAV_CMD name.
        :type command: str
        :param frame: Coordinate frame.
        :type frame: str
        :param param1: Command parameter 1.
        :type param1: float
        :param param2: Command parameter 2.
        :type param2: float
        :param param3: Command parameter 3.
        :type param3: float
        :param param4: Command parameter 4.
        :type param4: float
        :param latitude: Latitude in degrees.
        :type latitude: float
        :param longitude: Longitude in degrees.
        :type longitude: float
        :param altitude: Altitude in meters.
        :type altitude: float
        :param autocontinue: Whether to auto-continue.
        :type autocontinue: bool
        :param description: Optional item description.
        :type description: str | None
        :param item_id: Optional explicit item ID.
        :type item_id: str | None
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The updated mission aggregate.
        :rtype: MissionAggregate
        '''

        # Validate the command name.
        self.verify(
            expression=command in MAV_COMMANDS,
            error_code=const.INVALID_MAV_COMMAND_ID,
            command=command,
        )

        # Retrieve the mission.
        mission = self.mission_service.get(id)

        # Verify the mission exists.
        self.verify(
            expression=mission is not None,
            error_code=const.MISSION_NOT_FOUND_ID,
            mission_id=id,
        )

        # Verify the mission is modifiable.
        self.verify(
            expression=mission.status in ('draft', 'validated'),
            error_code=const.MISSION_NOT_MODIFIABLE_ID,
            mission_id=id,
            status=mission.status,
        )

        # Resolve command metadata.
        cmd_info = MAV_COMMANDS[command]

        # Create the mission item aggregate.
        item = MissionItemAggregate(
            id=item_id or str(uuid.uuid4()),
            sequence=mission.item_count,
            command=command,
            command_id=cmd_info['id'],
            category=cmd_info['category'],
            frame=frame,
            param1=param1,
            param2=param2,
            param3=param3,
            param4=param4,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            autocontinue=autocontinue,
            description=description,
        )

        # Add the item to the mission and update timestamp.
        mission.add_item(item)
        mission.updated_at = time.time()

        # Reset status to draft if it was validated.
        if mission.status == 'validated':
            mission.set_status('draft')

        # Persist the updated mission.
        self.mission_service.save(mission)

        # Return the updated mission.
        return mission


# ** event: remove_mission_item
class RemoveMissionItem(DomainEvent):
    '''
    Event to remove a mission item from a mission.
    '''

    # * attribute: mission_service
    mission_service: MissionService

    # * init
    def __init__(self, mission_service: MissionService):
        '''
        Initialize the RemoveMissionItem event.

        :param mission_service: The mission service for persistence.
        :type mission_service: MissionService
        '''

        # Set the mission service dependency.
        self.mission_service = mission_service

    # * method: execute
    @DomainEvent.parameters_required(['id', 'item_id'])
    def execute(self, id: str, item_id: str, **kwargs) -> MissionAggregate:
        '''
        Remove a mission item by its ID.

        :param id: The mission identifier.
        :type id: str
        :param item_id: The mission item ID to remove.
        :type item_id: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The updated mission aggregate.
        :rtype: MissionAggregate
        '''

        # Retrieve the mission.
        mission = self.mission_service.get(id)

        # Verify the mission exists.
        self.verify(
            expression=mission is not None,
            error_code=const.MISSION_NOT_FOUND_ID,
            mission_id=id,
        )

        # Verify the mission is modifiable.
        self.verify(
            expression=mission.status in ('draft', 'validated'),
            error_code=const.MISSION_NOT_MODIFIABLE_ID,
            mission_id=id,
            status=mission.status,
        )

        # Remove the item.
        removed = mission.remove_item(item_id)

        # Verify the item was found.
        self.verify(
            expression=removed is not None,
            error_code=const.MISSION_ITEM_NOT_FOUND_ID,
            mission_id=id,
            item_id=item_id,
        )

        # Update timestamp and persist.
        mission.updated_at = time.time()
        self.mission_service.save(mission)

        # Return the updated mission.
        return mission


# ** event: reorder_mission_items
class ReorderMissionItems(DomainEvent):
    '''
    Event to reorder mission items within a mission.
    '''

    # * attribute: mission_service
    mission_service: MissionService

    # * init
    def __init__(self, mission_service: MissionService):
        '''
        Initialize the ReorderMissionItems event.

        :param mission_service: The mission service for persistence.
        :type mission_service: MissionService
        '''

        # Set the mission service dependency.
        self.mission_service = mission_service

    # * method: execute
    @DomainEvent.parameters_required(['id', 'sequence_map'])
    def execute(self, id: str, sequence_map: Dict[str, int], **kwargs) -> MissionAggregate:
        '''
        Reorder mission items.

        :param id: The mission identifier.
        :type id: str
        :param sequence_map: Dict mapping item IDs to new sequence numbers.
        :type sequence_map: Dict[str, int]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The updated mission aggregate.
        :rtype: MissionAggregate
        '''

        # Retrieve the mission.
        mission = self.mission_service.get(id)

        # Verify the mission exists.
        self.verify(
            expression=mission is not None,
            error_code=const.MISSION_NOT_FOUND_ID,
            mission_id=id,
        )

        # Verify the mission is modifiable.
        self.verify(
            expression=mission.status in ('draft', 'validated'),
            error_code=const.MISSION_NOT_MODIFIABLE_ID,
            mission_id=id,
            status=mission.status,
        )

        # Validate no duplicate sequence numbers.
        new_sequences = list(sequence_map.values())
        self.verify(
            expression=len(new_sequences) == len(set(new_sequences)),
            error_code=const.SEQUENCE_GAP_ID,
            mission_id=id,
        )

        # Apply the reorder.
        mission.reorder_items(sequence_map)

        # Update timestamp and persist.
        mission.updated_at = time.time()
        self.mission_service.save(mission)

        # Return the updated mission.
        return mission


# ** event: assign_device
class AssignDevice(DomainEvent):
    '''
    Event to assign a device to a mission with drone type validation.
    '''

    # * attribute: mission_service
    mission_service: MissionService

    # * attribute: device_registry_service
    device_registry_service: DeviceRegistryService

    # * init
    def __init__(self,
            mission_service: MissionService,
            device_registry_service: DeviceRegistryService,
        ):
        '''
        Initialize the AssignDevice event.

        :param mission_service: The mission service for persistence.
        :type mission_service: MissionService
        :param device_registry_service: The device registry for type validation.
        :type device_registry_service: DeviceRegistryService
        '''

        # Set service dependencies.
        self.mission_service = mission_service
        self.device_registry_service = device_registry_service

    # * method: execute
    @DomainEvent.parameters_required(['id', 'device_id'])
    def execute(self, id: str, device_id: str, **kwargs) -> MissionAggregate:
        '''
        Assign a device to a mission after validating drone type compatibility.

        :param id: The mission identifier.
        :type id: str
        :param device_id: The device identifier from the external registry.
        :type device_id: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The updated mission aggregate.
        :rtype: MissionAggregate
        '''

        # Retrieve the mission.
        mission = self.mission_service.get(id)

        # Verify the mission exists.
        self.verify(
            expression=mission is not None,
            error_code=const.MISSION_NOT_FOUND_ID,
            mission_id=id,
        )

        # Verify the mission is in an assignable status.
        self.verify(
            expression=mission.status in ('draft', 'validated'),
            error_code=const.MISSION_NOT_MODIFIABLE_ID,
            mission_id=id,
            status=mission.status,
        )

        # Verify no device is already assigned.
        self.verify(
            expression=not mission.has_device,
            error_code=const.DEVICE_ALREADY_ASSIGNED_ID,
            mission_id=id,
            current_device_id=mission.device_id,
        )

        # Verify the device exists in the registry.
        self.verify(
            expression=self.device_registry_service.device_exists(device_id),
            error_code=const.DEVICE_NOT_FOUND_ID,
            device_id=device_id,
        )

        # Retrieve the device's drone type.
        device_type = self.device_registry_service.get_device_type(device_id)

        # Verify drone type compatibility.
        self.verify(
            expression=device_type == mission.drone_type,
            error_code=const.DEVICE_TYPE_MISMATCH_ID,
            device_id=device_id,
            device_type=device_type,
            mission_drone_type=mission.drone_type,
        )

        # Create the assignment record.
        now = time.time()
        assignment = DeviceAssignmentAggregate(
            mission_id=id,
            device_id=device_id,
            drone_type=device_type,
            assigned_at=now,
            status='active',
        )

        # Persist the assignment.
        self.mission_service.save_assignment(assignment)

        # Update the mission with the device reference and status.
        mission.assign_device(device_id)
        mission.set_status('assigned')
        mission.updated_at = now
        self.mission_service.save(mission)

        # Return the updated mission.
        return mission


# ** event: unassign_device
class UnassignDevice(DomainEvent):
    '''
    Event to release a device assignment from a mission.
    '''

    # * attribute: mission_service
    mission_service: MissionService

    # * init
    def __init__(self, mission_service: MissionService):
        '''
        Initialize the UnassignDevice event.

        :param mission_service: The mission service for persistence.
        :type mission_service: MissionService
        '''

        # Set the mission service dependency.
        self.mission_service = mission_service

    # * method: execute
    @DomainEvent.parameters_required(['id'])
    def execute(self, id: str, **kwargs) -> MissionAggregate:
        '''
        Unassign a device from a mission.

        :param id: The mission identifier.
        :type id: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The updated mission aggregate.
        :rtype: MissionAggregate
        '''

        # Retrieve the mission.
        mission = self.mission_service.get(id)

        # Verify the mission exists.
        self.verify(
            expression=mission is not None,
            error_code=const.MISSION_NOT_FOUND_ID,
            mission_id=id,
        )

        # Release the assignment record.
        assignment = self.mission_service.get_assignment(id)
        if assignment is not None:
            assignment.release()
            self.mission_service.save_assignment(assignment)

        # Remove device reference and reset status.
        mission.unassign_device()
        mission.set_status('draft')
        mission.updated_at = time.time()
        self.mission_service.save(mission)

        # Return the updated mission.
        return mission


# ** event: validate_mission
class ValidateMission(DomainEvent):
    '''
    Event to validate a mission's structural readiness for flight.
    '''

    # * attribute: mission_service
    mission_service: MissionService

    # * init
    def __init__(self, mission_service: MissionService):
        '''
        Initialize the ValidateMission event.

        :param mission_service: The mission service for persistence.
        :type mission_service: MissionService
        '''

        # Set the mission service dependency.
        self.mission_service = mission_service

    # * method: execute
    @DomainEvent.parameters_required(['id'])
    def execute(self, id: str, **kwargs) -> MissionAggregate:
        '''
        Validate a mission for flight readiness.

        :param id: The mission identifier.
        :type id: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The validated mission aggregate.
        :rtype: MissionAggregate
        '''

        # Retrieve the mission.
        mission = self.mission_service.get(id)

        # Verify the mission exists.
        self.verify(
            expression=mission is not None,
            error_code=const.MISSION_NOT_FOUND_ID,
            mission_id=id,
        )

        # Verify there is at least one NAV item.
        nav_items = [it for it in mission.items if it.category == 'NAV']
        self.verify(
            expression=len(nav_items) > 0,
            error_code=const.MISSION_VALIDATION_FAILED_ID,
            message='Mission must contain at least one NAV item.',
            mission_id=id,
        )

        # Verify first item is an appropriate start command.
        first_item = mission.items[0] if mission.items else None
        if mission.drone_type in ('copter', 'plane', 'vtol'):
            self.verify(
                expression=first_item is not None and first_item.command == 'NAV_TAKEOFF',
                error_code=const.MISSION_VALIDATION_FAILED_ID,
                message='First item must be NAV_TAKEOFF for copter/plane/vtol.',
                mission_id=id,
            )
        elif mission.drone_type == 'rover':
            self.verify(
                expression=first_item is not None and first_item.command in ('NAV_WAYPOINT', 'NAV_TAKEOFF'),
                error_code=const.MISSION_VALIDATION_FAILED_ID,
                message='First item must be NAV_WAYPOINT or NAV_TAKEOFF for rover.',
                mission_id=id,
            )

        # Verify last NAV item is a terminal command.
        last_nav = nav_items[-1] if nav_items else None
        self.verify(
            expression=last_nav is not None and last_nav.command in ('NAV_LAND', 'NAV_RETURN_TO_LAUNCH'),
            error_code=const.MISSION_VALIDATION_FAILED_ID,
            message='Last NAV item must be NAV_LAND or NAV_RETURN_TO_LAUNCH.',
            mission_id=id,
        )

        # Update status to validated.
        mission.set_status('validated')
        mission.updated_at = time.time()
        self.mission_service.save(mission)

        # Return the validated mission.
        return mission


# ** event: update_mission_status
class UpdateMissionStatus(DomainEvent):
    '''
    Event to update a mission's lifecycle status with transition validation.
    '''

    # * attribute: mission_service
    mission_service: MissionService

    # * init
    def __init__(self, mission_service: MissionService):
        '''
        Initialize the UpdateMissionStatus event.

        :param mission_service: The mission service for persistence.
        :type mission_service: MissionService
        '''

        # Set the mission service dependency.
        self.mission_service = mission_service

    # * method: execute
    @DomainEvent.parameters_required(['id', 'status'])
    def execute(self, id: str, status: str, **kwargs) -> MissionAggregate:
        '''
        Update a mission's lifecycle status.

        :param id: The mission identifier.
        :type id: str
        :param status: The target status.
        :type status: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The updated mission aggregate.
        :rtype: MissionAggregate
        '''

        # Retrieve the mission.
        mission = self.mission_service.get(id)

        # Verify the mission exists.
        self.verify(
            expression=mission is not None,
            error_code=const.MISSION_NOT_FOUND_ID,
            mission_id=id,
        )

        # Verify the status transition is valid.
        allowed = VALID_STATUS_TRANSITIONS.get(mission.status, [])
        self.verify(
            expression=status in allowed,
            error_code=const.MISSION_INVALID_STATUS_TRANSITION_ID,
            mission_id=id,
            current_status=mission.status,
            target_status=status,
        )

        # Apply the status update.
        mission.set_status(status)
        mission.updated_at = time.time()
        self.mission_service.save(mission)

        # Return the updated mission.
        return mission
