# Events Guide — tiferet-mission

## Overview

Domain events are the operational core of `tiferet-mission`. Each event extends `tiferet.events.DomainEvent`, receives dependencies via constructor injection, and exposes an `execute(**kwargs)` entry point.

## Available Events

### Mission CRUD

- **`CreateMission`** — Creates a new mission in `draft` status. Required: `name`, `drone_type`. Optional: `description`, `id`.
- **`GetMission`** — Retrieves a mission by ID. Raises `MISSION_NOT_FOUND` if absent.
- **`ListMissions`** — Lists missions with optional `drone_type` and `status` filters.
- **`DeleteMission`** — Deletes a mission. Only `draft` or `aborted` missions can be deleted.

### Mission Item Management

- **`AddMissionItem`** — Adds a waypoint/command to a mission. Validates command name against `MAV_COMMANDS`. Auto-assigns sequence number.
- **`RemoveMissionItem`** — Removes an item by ID and re-sequences remaining items.
- **`ReorderMissionItems`** — Reorders items using a `{item_id: new_sequence}` mapping.

### Device Assignment

- **`AssignDevice`** — Assigns a device to a mission with drone type validation:
  1. Verifies mission exists and is in `draft` or `validated` status.
  2. Verifies no device is already assigned.
  3. Queries the `DeviceRegistryService` to confirm the device exists.
  4. Validates the device's drone type matches the mission's `drone_type`.
  5. Creates a `DeviceAssignment` record and updates mission status to `assigned`.
- **`UnassignDevice`** — Releases a device assignment and resets mission to `draft`.

### Mission Lifecycle

- **`ValidateMission`** — Validates structural flight readiness:
  - At least one NAV item exists.
  - First item is `NAV_TAKEOFF` (copter/plane/vtol) or `NAV_WAYPOINT` (rover).
  - Last NAV item is `NAV_LAND` or `NAV_RETURN_TO_LAUNCH`.
- **`UpdateMissionStatus`** — Enforces valid state transitions per the `VALID_STATUS_TRANSITIONS` map.

## Testing Events

Always use `DomainEvent.handle()` in tests:

```python
from tiferet.events import DomainEvent
from tiferet_mission.events import CreateMission

result = DomainEvent.handle(
    CreateMission,
    dependencies={'mission_service': mock_service},
    name='Survey Alpha',
    drone_type='copter',
)
```

## Dependencies

All events depend on `MissionService`. The `AssignDevice` event additionally depends on `DeviceRegistryService` (a read-only interface that the consuming application must implement).
