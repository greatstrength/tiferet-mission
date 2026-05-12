"""tiferet_mission Domain Settings"""

# *** imports

# ** core
from typing import Dict, Any, Literal

# *** constants

# ** constant: drone_type
DroneType = Literal['copter', 'plane', 'rover', 'sub', 'vtol']

# ** constant: mission_status
MissionStatus = Literal[
    'draft',
    'validated',
    'assigned',
    'uploaded',
    'executing',
    'completed',
    'aborted',
]

# ** constant: mav_frame
MavFrame = Literal[
    'GLOBAL',
    'GLOBAL_RELATIVE_ALT',
    'GLOBAL_TERRAIN_ALT',
    'LOCAL_NED',
    'MISSION',
]

# ** constant: mav_command_category
MavCommandCategory = Literal['NAV', 'DO', 'CONDITION']

# ** constant: assignment_status
AssignmentStatus = Literal['active', 'released', 'rejected']

# ** constant: valid_status_transitions
VALID_STATUS_TRANSITIONS: Dict[str, list] = {
    'draft':      ['validated', 'aborted'],
    'validated':  ['assigned', 'draft', 'aborted'],
    'assigned':   ['uploaded', 'draft', 'aborted'],
    'uploaded':   ['executing', 'assigned', 'aborted'],
    'executing':  ['completed', 'aborted'],
    'completed':  [],
    'aborted':    ['draft'],
}

# ** constant: mav_commands
MAV_COMMANDS: Dict[str, Dict[str, Any]] = {
    'NAV_WAYPOINT':          {'id': 16,  'category': 'NAV'},
    'NAV_LOITER_UNLIM':      {'id': 17,  'category': 'NAV'},
    'NAV_LOITER_TURNS':      {'id': 18,  'category': 'NAV'},
    'NAV_LOITER_TIME':       {'id': 19,  'category': 'NAV'},
    'NAV_RETURN_TO_LAUNCH':  {'id': 20,  'category': 'NAV'},
    'NAV_LAND':              {'id': 21,  'category': 'NAV'},
    'NAV_TAKEOFF':           {'id': 22,  'category': 'NAV'},
    'NAV_SPLINE_WAYPOINT':   {'id': 82,  'category': 'NAV'},
    'NAV_DELAY':             {'id': 93,  'category': 'NAV'},
    'CONDITION_DELAY':       {'id': 112, 'category': 'CONDITION'},
    'CONDITION_DISTANCE':    {'id': 114, 'category': 'CONDITION'},
    'CONDITION_YAW':         {'id': 115, 'category': 'CONDITION'},
    'DO_JUMP':               {'id': 177, 'category': 'DO'},
    'DO_CHANGE_SPEED':       {'id': 178, 'category': 'DO'},
    'DO_SET_HOME':           {'id': 179, 'category': 'DO'},
    'DO_SET_RELAY':          {'id': 181, 'category': 'DO'},
    'DO_SET_SERVO':          {'id': 183, 'category': 'DO'},
    'DO_SET_ROI':            {'id': 201, 'category': 'DO'},
    'DO_SET_CAM_TRIGG_DIST': {'id': 206, 'category': 'DO'},
    'DO_FENCE_ENABLE':       {'id': 207, 'category': 'DO'},
}
