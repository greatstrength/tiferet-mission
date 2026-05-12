"""tiferet_mission Mappers Assignment"""

# *** imports

# ** app
from tiferet.mappers import Aggregate
from ..domain.assignment import DeviceAssignment

# *** mappers

# ** mapper: device_assignment_aggregate
class DeviceAssignmentAggregate(DeviceAssignment, Aggregate):
    '''
    Mutable aggregate for the DeviceAssignment domain object.
    '''

    # * method: release
    def release(self) -> None:
        '''
        Mark the assignment as released.
        '''

        # Set status to released.
        self.status = 'released'

    # * method: reject
    def reject(self) -> None:
        '''
        Mark the assignment as rejected.
        '''

        # Set status to rejected.
        self.status = 'rejected'
