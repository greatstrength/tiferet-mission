"""tiferet_mission — Domain-Driven Mission Planning for Autonomous Drone Operations"""

# *** exports

# ** app
# Wrap runtime imports in a try/except so that build tools can import
# __version__ without requiring the full dependency tree to be installed.
try:
    from .domain import (
        Mission,
        MissionItem,
        DeviceAssignment,
    )
    from .interfaces import (
        MissionService,
        DeviceRegistryService,
    )
    from .mappers import (
        MissionAggregate,
        MissionItemAggregate,
        DeviceAssignmentAggregate,
    )
    from .events import (
        CreateMission,
        GetMission,
        ListMissions,
        DeleteMission,
        AddMissionItem,
        RemoveMissionItem,
        ReorderMissionItems,
        AssignDevice,
        UnassignDevice,
        ValidateMission,
        UpdateMissionStatus,
    )
except Exception as e:
    import os, sys
    if not os.getenv('TIFERET_MISSION_SILENT_IMPORTS'):
        print(f'Warning: Failed to import tiferet_mission modules: {e}', file=sys.stderr)

# *** version

__version__ = '0.1.0a1'
