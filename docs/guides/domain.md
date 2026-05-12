# Domain Guide — tiferet-mission

## Overview

The domain layer defines the structural core of mission planning: missions, mission items (waypoints/commands), and device assignments. All domain objects extend `tiferet.domain.DomainObject` (Pydantic v2, read-only).

## Mission Item

`MissionItem` represents a single MAVLink-compatible command within a mission. It mirrors the `MISSION_ITEM_INT` message structure:

```python
from tiferet_mission.domain import MissionItem

item = MissionItem(
    id='wp-001',
    sequence=0,
    command='NAV_WAYPOINT',
    latitude=35.123,
    longitude=-120.456,
    altitude=50.0,
)
# command_id and category are auto-derived from the MAV_COMMANDS table
assert item.command_id == 16
assert item.category == 'NAV'
```

### Auto-Derivation

When constructing a `MissionItem`, the `command_id` and `category` fields are automatically derived from the `MAV_COMMANDS` lookup table in `domain/settings.py`. If the command name is not recognized, the defaults (`command_id=0`, `category='NAV'`) are preserved.

## Mission

`Mission` is the top-level domain object representing a complete mission plan:

```python
from tiferet_mission.domain import Mission, MissionItem

mission = Mission(
    id='mission-001',
    name='Survey Alpha',
    drone_type='copter',
    items=[
        MissionItem(id='i1', sequence=0, command='NAV_TAKEOFF', altitude=10.0),
        MissionItem(id='i2', sequence=1, command='NAV_WAYPOINT', latitude=35.0, longitude=-120.0, altitude=50.0),
        MissionItem(id='i3', sequence=2, command='NAV_RETURN_TO_LAUNCH'),
    ],
    created_at='2026-01-01T00:00:00Z',
    updated_at='2026-01-01T00:00:00Z',
)

assert mission.item_count == 3
assert mission.get_item(1).command == 'NAV_WAYPOINT'
assert mission.has_device is False
```

### Lifecycle Status

Missions follow a defined lifecycle: `draft → validated → assigned → uploaded → executing → completed`. The `aborted` status can be reached from most active states. Transitions are enforced by the `UpdateMissionStatus` domain event.

## Device Assignment

`DeviceAssignment` is a lightweight audit record linking a device to a mission:

```python
from tiferet_mission.domain import DeviceAssignment

assignment = DeviceAssignment(
    mission_id='mission-001',
    device_id='drone-001',
    drone_type='copter',
    assigned_at='2026-01-01T12:00:00Z',
)
assert assignment.status == 'active'
```

## MAV_COMMANDS Reference

The `MAV_COMMANDS` dict in `domain/settings.py` maps command names to numeric IDs and categories. This table is extensible — applications can add custom commands at startup.

Supported categories:
- **NAV** — Navigation commands (waypoint, takeoff, land, loiter, RTL)
- **DO** — Auxiliary commands (speed, servo, relay, ROI, camera)
- **CONDITION** — Conditional commands (delay, distance, yaw)
