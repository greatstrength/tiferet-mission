# AGENTS.md — tiferet-mission

## Project Overview

**tiferet-mission** is a mission planning extension package for the [Tiferet](https://github.com/greatstrength/tiferet) framework. It provides a full Domain-Driven Design (DDD) layer for autonomous drone mission planning, with MAVLink-compatible domain objects, lifecycle management, device assignment validation, and dual-backend persistence (SQLite and HDF5).

- **Repository:** https://github.com/greatstrength/tiferet-mission
- **Branch:** `v0.x-proto`
- **Python:** ≥ 3.10
- **Version:** `0.1.0a1`
- **Dependencies:** `tiferet >= 2.0.0b1`; optional `tiferet-h5 >= 0.1.0`, `tables >= 3.10.0`

## Architecture

### Layer Overview

```
tiferet_mission/
├── assets/           Error code string constants
├── domain/           DomainObject subclasses (Mission, MissionItem, DeviceAssignment)
├── events/           DomainEvent subclasses (11 mission lifecycle events)
├── interfaces/       MissionService and DeviceRegistryService contracts
├── mappers/          Aggregates + SQL TransferObjects + H5 TableObjects/NodeObjects
├── repos/            SQLite-backed MissionService implementation
└── tests/            Unit and integration tests
```

### Key Concepts

**Domain Objects** (`domain/`)

- **`MissionItem`** — A single MAVLink-compatible mission command. Mirrors `MISSION_ITEM_INT`. Fields: `id`, `sequence`, `command`, `command_id`, `category`, `frame`, `param1`–`param4`, `latitude`, `longitude`, `altitude`, `autocontinue`. Uses `@model_validator` to auto-derive `command_id` and `category` from the `MAV_COMMANDS` reference table.
- **`Mission`** — An ordered collection of `MissionItem` objects with lifecycle status. Fields: `id`, `name`, `description`, `status`, `drone_type`, `device_id`, `items`, `created_at`, `updated_at`. Read-only methods: `get_item(sequence)`, `item_count`, `has_device`.
- **`DeviceAssignment`** — Audit record linking a device to a mission. Fields: `mission_id`, `device_id`, `drone_type`, `assigned_at`, `status`.

**Shared Constants** (`domain/settings.py`)

- `DroneType` — `Literal['copter', 'plane', 'rover', 'sub', 'vtol']`
- `MissionStatus` — `Literal['draft', 'validated', 'assigned', 'uploaded', 'executing', 'completed', 'aborted']`
- `VALID_STATUS_TRANSITIONS` — Dict defining allowed state machine transitions.
- `MAV_COMMANDS` — Dict mapping 20+ MAV_CMD names to `{id, category}` metadata.

**Service Interfaces** (`interfaces/`)

- **`MissionService`** — Full CRUD + assignment management (8 abstract methods). Implemented by `MissionSqliteRepository`.
- **`DeviceRegistryService`** — Read-only contract (`device_exists`, `get_device_type`). NOT implemented by this package — the consuming application provides it.

**Mappers** (`mappers/`)

- **Aggregates**: `MissionAggregate`, `MissionItemAggregate`, `DeviceAssignmentAggregate` — mutable extensions with domain-specific mutations.
- **SQL Transfer Objects**: `MissionSqlObject`, `MissionItemSqlObject`, `DeviceAssignmentSqlObject` — extend `TransferObject` with `_ROLES = {'to_data.sql': {...}}`.
- **H5 Transfer Objects** (optional): `MissionNodeObject`, `MissionItemTableObject`, `DeviceAssignmentTableObject` — extend `tiferet_h5` `NodeObject`/`TableObject`.

**Domain Events** (`events/mission.py`)

11 events extending `DomainEvent`:
- CRUD: `CreateMission`, `GetMission`, `ListMissions`, `DeleteMission`
- Items: `AddMissionItem`, `RemoveMissionItem`, `ReorderMissionItems`
- Device: `AssignDevice` (validates drone type compatibility via `DeviceRegistryService`), `UnassignDevice`
- Lifecycle: `ValidateMission` (structural flight-readiness checks), `UpdateMissionStatus` (enforces state transitions)

**Repository** (`repos/sqlite.py`)

`MissionSqliteRepository` — SQLite-backed `MissionService` implementation using `tiferet.utils.Sqlite`. Auto-creates schema on first use. Three tables: `missions`, `mission_items`, `device_assignments`.

## Structured Code Style

All code follows the Tiferet artifact comment hierarchy. **This is mandatory.**

### Comment Levels

- `# *** <section>` — Top-level: `imports`, `constants`, `models`, `events`, `interfaces`, `mappers`, `repos`
- `# ** <category>: <name>` — Mid-level: `core`, `infra`, `app` (imports); `model: <name>`, `event: <name>`, etc.
- `# * <component>` — Low-level: `attribute: <name>`, `init`, `method: <name>`, `method: <name> (static)`

### Spacing Rules

- One empty line between `# ***` and first `# **`.
- One empty line between each `# *` section.
- One empty line after docstrings and between code snippets within methods.

### Docstrings

RST format with `:param`, `:type`, `:return:`, `:rtype:` for all public methods.

## Error Handling

All errors are raised as `TiferetError` via `self.verify()` or `self.raise_error()` in domain events. Error code constants are defined in `tiferet_mission/assets/constants.py`:

- `MISSION_NOT_FOUND_ID`, `MISSION_ALREADY_EXISTS_ID`, `MISSION_ITEM_NOT_FOUND_ID`
- `MISSION_NOT_DELETABLE_ID`, `MISSION_NOT_MODIFIABLE_ID`
- `MISSION_INVALID_STATUS_TRANSITION_ID`, `MISSION_VALIDATION_FAILED_ID`
- `DEVICE_NOT_FOUND_ID`, `DEVICE_TYPE_MISMATCH_ID`, `DEVICE_ALREADY_ASSIGNED_ID`
- `INVALID_MAV_COMMAND_ID`, `SEQUENCE_GAP_ID`

## Testing

- **Framework:** `pytest` with `pytest-cov`.
- **Test location:** `tiferet_mission/tests/` (unit) and `tiferet_mission/mappers/tests/` (harness-based mapper tests).
- **Run tests:** `pytest tiferet_mission/ --verbose`
- **Test harness:** Uses `AggregateTestBase` and `TransferObjectTestBase` from `tiferet.mappers.tests.settings`.
- **Integration tests:** `test_repos.py` uses `tmp_path` fixtures with real temporary SQLite databases.
- **Event testing:** Always invoke via `DomainEvent.handle(EventClass, dependencies={...}, **kwargs)`.

## Package Exports

`tiferet_mission/__init__.py` exports:

**Domain:** `Mission`, `MissionItem`, `DeviceAssignment`
**Interfaces:** `MissionService`, `DeviceRegistryService`
**Mappers:** `MissionAggregate`, `MissionItemAggregate`, `DeviceAssignmentAggregate`
**Events:** `CreateMission`, `GetMission`, `ListMissions`, `DeleteMission`, `AddMissionItem`, `RemoveMissionItem`, `ReorderMissionItems`, `AssignDevice`, `UnassignDevice`, `ValidateMission`, `UpdateMissionStatus`

## Key Files for Orientation

- `tiferet_mission/__init__.py` — Version and public exports
- `tiferet_mission/assets/constants.py` — Error code constants
- `tiferet_mission/domain/settings.py` — Shared enums, MAV_COMMANDS table, status transitions
- `tiferet_mission/domain/mission.py` — Mission and MissionItem domain objects
- `tiferet_mission/domain/assignment.py` — DeviceAssignment domain object
- `tiferet_mission/events/mission.py` — All 11 domain events
- `tiferet_mission/interfaces/mission.py` — MissionService contract
- `tiferet_mission/interfaces/device.py` — DeviceRegistryService contract
- `tiferet_mission/mappers/mission.py` — MissionAggregate, MissionItemAggregate
- `tiferet_mission/mappers/mission_sql.py` — SQL transfer objects
- `tiferet_mission/mappers/mission_h5.py` — H5 transfer objects (optional)
- `tiferet_mission/repos/sqlite.py` — MissionSqliteRepository

## Contributing

1. Work from the `v0.x-proto` branch. Feature branches: `<issue-number>-<lowercase-hyphenated-title>`.
2. Follow the structured code style documented above.
3. All errors must use `self.verify()` or `self.raise_error()` with a constant from `assets/constants.py`.
4. Separate functional changes from documentation in distinct commits.
5. Include `Co-Authored-By: Oz <oz-agent@warp.dev>` in every commit made with AI assistance.
6. Publish a Collaboration Report on the issue upon completion.
