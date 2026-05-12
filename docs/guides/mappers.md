# Mappers Guide — tiferet-mission

## Overview

The mappers layer bridges domain objects and persistent storage. It provides:
- **Aggregates** — mutable extensions of domain objects for mutation logic.
- **SQL Transfer Objects** — serialization layer for SQLite storage using `tiferet.mappers.TransferObject`.
- **H5 Transfer Objects** — serialization layer for HDF5 storage using `tiferet_h5.mappers.TableObject` / `NodeObject` (optional dependency).

## Aggregates

### MissionItemAggregate

Extends `MissionItem` with mutation methods:

```python
from tiferet_mission.mappers import MissionItemAggregate

item = MissionItemAggregate(id='i1', sequence=0, command='NAV_WAYPOINT')
item.update_position(latitude=35.0, longitude=-120.0, altitude=50.0)
item.update_params(param1=5.0, param4=90.0)
```

### MissionAggregate

Extends `Mission` with full mission management:

```python
from tiferet_mission.mappers import MissionAggregate, MissionItemAggregate

mission = MissionAggregate(
    id='m1', name='Survey', drone_type='copter',
    created_at='2026-01-01T00:00:00Z', updated_at='2026-01-01T00:00:00Z',
)

# Add items
mission.add_item(MissionItemAggregate(id='i1', sequence=0, command='NAV_TAKEOFF'))
mission.add_item(MissionItemAggregate(id='i2', sequence=1, command='NAV_WAYPOINT'))

# Remove and re-sequence
mission.remove_item('i1')  # i2 becomes sequence 0

# Reorder
mission.reorder_items({'i2': 0, 'i3': 1})

# Device management
mission.assign_device('drone-001')
mission.unassign_device()
```

### DeviceAssignmentAggregate

```python
from tiferet_mission.mappers import DeviceAssignmentAggregate

assignment = DeviceAssignmentAggregate(
    mission_id='m1', device_id='d1', drone_type='copter',
    assigned_at='2026-01-01T00:00:00Z',
)
assignment.release()   # status -> 'released'
assignment.reject()    # status -> 'rejected'
```

## SQL Transfer Objects

Located in `mappers/mission_sql.py`. Each uses a `_ROLES` ClassVar with a `to_data.sql` role:

- `MissionSqlObject` — excludes `items` from serialization (stored in a separate table).
- `MissionItemSqlObject` — adds `mission_id` foreign key field.
- `DeviceAssignmentSqlObject` — direct field mapping.

All provide `to_sql_dict()` and `from_sql_row()` convenience methods.

## H5 Transfer Objects (Optional)

Located in `mappers/mission_h5.py`. Requires the `[h5]` extra (`pip install tiferet-mission[h5]`).

### HDF5 Data Layout

```
/missions/
    {mission_id}/                  ← group, attrs via MissionNodeObject
        items                      ← table, rows via MissionItemTableObject
/assignments/                      ← table, rows via DeviceAssignmentTableObject
```

- `MissionNodeObject(Mission, NodeObject)` — mission metadata as HDF5 group attributes.
- `MissionItemTableObject(MissionItem, TableObject)` — uses aliased columns (`seq`, `cmd`, `p1`-`p4`, `lat`, `lon`, `alt`, etc.) for compact storage.
- `DeviceAssignmentTableObject(DeviceAssignment, TableObject)` — flat table for assignment records.

## Testing

Mapper tests use the Tiferet framework's `AggregateTestBase` and `TransferObjectTestBase` harnesses:

```python
from tiferet.mappers.tests.settings import AggregateTestBase

class TestMissionAggregate(AggregateTestBase):
    aggregate_cls = MissionAggregate
    sample_data = {...}
    equality_fields = [...]
    set_attribute_params = [
        ('name', 'New Name', None),
        ('invalid_attr', 'value', 'INVALID_MODEL_ATTRIBUTE'),
    ]
```

H5 mapper tests will use `TableObjectTestBase` and `NodeObjectTestBase` from tiferet-h5 once [greatstrength/tiferet-h5#17](https://github.com/greatstrength/tiferet-h5/issues/17) is resolved.
