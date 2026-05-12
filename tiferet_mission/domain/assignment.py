"""tiferet_mission Domain Assignment"""

# *** imports

# ** core
from typing import Optional

# ** infra
from pydantic import Field

# ** app
from tiferet.domain import DomainObject

# *** models

# ** model: device_assignment
class DeviceAssignment(DomainObject):
    '''
    An audit record linking a device to a mission with type validation state.
    '''

    # * attribute: mission_id
    mission_id: str = Field(..., description='The mission this assignment belongs to.')

    # * attribute: device_id
    device_id: str = Field(..., description='The device identifier from the external registry.')

    # * attribute: drone_type
    drone_type: str = Field(..., description="The device's drone type at the time of assignment.")

    # * attribute: assigned_at
    assigned_at: float = Field(..., description='Unix timestamp of when the assignment was created.')

    # * attribute: status
    status: str = Field(default='active', description="Assignment status: 'active', 'released', or 'rejected'.")
