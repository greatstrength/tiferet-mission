# tiferet-mission

Domain-driven mission planning for autonomous drone operations, powered by MAVLink-compatible workflows and dual-backend persistence.

## Overview

`tiferet-mission` is a [Tiferet](https://github.com/greatstrength/tiferet) extension package that provides a complete Domain-Driven Design (DDD) layer for drone mission planning. It models MAVLink-style mission plans as first-class domain objects with lifecycle management, device assignment validation, and dual-backend persistence (SQLite and HDF5).

## Installation

```bash
# Core (SQLite backend)
pip install tiferet-mission

# With HDF5 support
pip install tiferet-mission[h5]
```

## Quick Start

```python
from tiferet.events import DomainEvent
from tiferet_mission.events import CreateMission, AddMissionItem, ValidateMission
from tiferet_mission.repos.sqlite import MissionSqliteRepository

# Initialize the SQLite repository
mission_service = MissionSqliteRepository(db_path='missions.db')

# Create a mission
mission = DomainEvent.handle(
    CreateMission,
    dependencies={'mission_service': mission_service},
    name='Survey Alpha',
    drone_type='copter',
)

# Add waypoints
for cmd, kwargs in [
    ('NAV_TAKEOFF', {'altitude': 10.0}),
    ('NAV_WAYPOINT', {'latitude': 35.123, 'longitude': -120.456, 'altitude': 50.0}),
    ('NAV_RETURN_TO_LAUNCH', {}),
]:
    DomainEvent.handle(
        AddMissionItem,
        dependencies={'mission_service': mission_service},
        id=mission.id, command=cmd, **kwargs,
    )

# Validate the mission
validated = DomainEvent.handle(
    ValidateMission,
    dependencies={'mission_service': mission_service},
    id=mission.id,
)
print(f'Mission "{validated.name}" status: {validated.status}')  # validated
```

## Architecture

```
tiferet_mission/
├── assets/           Error code constants
├── domain/           DomainObject subclasses (Mission, MissionItem, DeviceAssignment)
├── events/           DomainEvent subclasses (11 mission lifecycle events)
├── interfaces/       Service contracts (MissionService, DeviceRegistryService)
├── mappers/          Aggregates + SQL TransferObjects + H5 TableObjects/NodeObjects
├── repos/            SQLite repository implementation
└── tests/            Unit + integration tests
```

## Features

### Domain Objects
- **Mission** — ordered collection of mission items with lifecycle status and device reference
- **MissionItem** — MAVLink-compatible command (NAV/DO/CONDITION) with auto-derived metadata
- **DeviceAssignment** — audit record linking a device to a mission

### Domain Events (11)
- **CRUD**: CreateMission, GetMission, ListMissions, DeleteMission
- **Items**: AddMissionItem, RemoveMissionItem, ReorderMissionItems
- **Device**: AssignDevice (with type validation), UnassignDevice
- **Lifecycle**: ValidateMission, UpdateMissionStatus

### MAVLink Compatibility
- 20+ MAV_CMD commands mapped (NAV_WAYPOINT, NAV_TAKEOFF, NAV_LAND, DO_CHANGE_SPEED, etc.)
- Mission items mirror the `MISSION_ITEM_INT` message structure
- Extensible command reference table

### Dual-Backend Persistence
- **SQLite** — relational storage via `MissionSqliteRepository`
- **HDF5** — columnar storage via H5 transfer objects (requires `[h5]` extra)
- Both implement the same `MissionService` interface — switching is a config change

### Device Type Validation
- `DeviceRegistryService` — read-only interface for querying external device registries
- `AssignDevice` event validates drone type compatibility before assignment

## Dependencies

- `tiferet >= 2.0.0b1` (core framework)
- `tiferet-h5 >= 0.1.0` + `tables >= 3.10.0` (optional, for HDF5 backend)

## Documentation

- [Domain Guide](docs/guides/domain.md)
- [Events Guide](docs/guides/events.md)
- [Mappers Guide](docs/guides/mappers.md)

## License

BSD 3-Clause. See [LICENSE](LICENSE).
