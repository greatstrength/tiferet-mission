"""tiferet_mission Repos H5"""

# *** imports

# ** core
from typing import List, Optional

# ** app
from tiferet_h5.repos import H5Repository
from ..interfaces.mission import MissionService
from ..mappers.mission import MissionAggregate, MissionItemAggregate
from ..mappers.assignment import DeviceAssignmentAggregate
from ..mappers.mission_h5 import (
    MissionNodeObject,
    MissionItemTableObject,
    DeviceAssignmentTableObject,
)

# *** constants

# ** constant: missions_root
MISSIONS_ROOT = '/missions'

# ** constant: assignments_path
ASSIGNMENTS_PATH = '/assignments'

# *** repos

# ** repo: mission_h5_repository
class MissionH5Repository(H5Repository, MissionService):
    '''
    HDF5-backed implementation of MissionService.

    Data layout::

        /missions/
            {mission_id}/              ← group, attrs via MissionNodeObject
                items                  ← table, rows via MissionItemTableObject
        /assignments/                  ← table, rows via DeviceAssignmentTableObject
    '''

    # * init
    def __init__(self, h5_file: str, mode: str = 'a'):
        '''
        Initialize the MissionH5Repository.

        :param h5_file: Path to the HDF5 file.
        :type h5_file: str
        :param mode: Default PyTables open mode.
        :type mode: str
        '''

        # Initialize the H5Repository base.
        super().__init__(h5_file=h5_file, mode=mode)

    # * method: _mission_group_path
    def _mission_group_path(self, id: str) -> str:
        '''
        Return the HDF5 group path for a mission.

        :param id: The mission identifier.
        :type id: str
        :return: The group path string.
        :rtype: str
        '''

        # Build the path from the missions root.
        return f'{MISSIONS_ROOT}/{id}'

    # * method: _items_table_path
    def _items_table_path(self, id: str) -> str:
        '''
        Return the HDF5 table path for a mission's items.

        :param id: The mission identifier.
        :type id: str
        :return: The table path string.
        :rtype: str
        '''

        # Build the path from the mission group.
        return f'{MISSIONS_ROOT}/{id}/items'

    # * method: exists
    def exists(self, id: str) -> bool:
        '''
        Check if a mission exists by ID.

        :param id: The mission identifier.
        :type id: str
        :return: True if the mission group exists.
        :rtype: bool
        '''

        # Check for the mission group node.
        with self.client(mode='r') as h5:
            return h5.node_exists(self._mission_group_path(id))

    # * method: get
    def get(self, id: str) -> Optional[MissionAggregate]:
        '''
        Retrieve a mission by ID with its items.

        :param id: The mission identifier.
        :type id: str
        :return: The mission aggregate, or None.
        :rtype: MissionAggregate | None
        '''

        group_path = self._mission_group_path(id)
        items_path = self._items_table_path(id)

        with self.client(mode='r') as h5:

            # Check if the mission group exists.
            if not h5.node_exists(group_path):
                return None

            # Read mission metadata from group attributes.
            attrs = h5.get_node_attrs(group_path)
            mission_obj = MissionNodeObject.from_attrs(attrs)

            # Read items from the items table if it exists.
            items = []
            if h5.node_exists(items_path):
                table = h5.get_table(items_path)
                for row in table.iterrows():
                    item_obj = MissionItemTableObject.from_row(row)
                    items.append(item_obj.map())

        # Map to aggregate with items.
        return mission_obj.map(items=items)

    # * method: list
    def list(self,
            drone_type: Optional[str] = None,
            status: Optional[str] = None,
        ) -> List[MissionAggregate]:
        '''
        List missions with optional filters.

        :param drone_type: Optional drone type filter.
        :type drone_type: str | None
        :param status: Optional status filter.
        :type status: str | None
        :return: A list of mission aggregates.
        :rtype: List[MissionAggregate]
        '''

        results = []

        with self.client(mode='r') as h5:

            # Check if the missions root exists.
            if not h5.node_exists(MISSIONS_ROOT):
                return results

            # Iterate over mission groups.
            group = h5.get_group(MISSIONS_ROOT)
            for node in group._f_iter_nodes('Group'):
                attrs = h5.get_node_attrs(node._v_pathname)
                mission_obj = MissionNodeObject.from_attrs(attrs)

                # Apply filters.
                if drone_type is not None and mission_obj.drone_type != drone_type:
                    continue
                if status is not None and mission_obj.status != status:
                    continue

                results.append(mission_obj.id)

        # Load full missions by ID.
        return [self.get(mid) for mid in results if self.get(mid) is not None]

    # * method: save
    def save(self, mission: MissionAggregate) -> None:
        '''
        Save or update a mission and its items.

        :param mission: The mission aggregate to persist.
        :type mission: MissionAggregate
        '''

        group_path = self._mission_group_path(mission.id)
        items_path = self._items_table_path(mission.id)

        # Serialize mission metadata.
        mission_obj = MissionNodeObject.from_model(mission)
        attrs = mission_obj.to_attrs()

        with self.client() as h5:

            # Create or get the mission group.
            if not h5.node_exists(group_path):
                h5.create_group(MISSIONS_ROOT, mission.id)

            # Write mission metadata as group attributes.
            for key, value in attrs.items():
                h5.set_node_attr(group_path, key, value)

            # Remove existing items table if present, then recreate.
            if h5.node_exists(items_path):
                h5.h5file.remove_node(items_path)

            # Create items table and write rows.
            if mission.items:
                description = MissionItemTableObject.get_description()
                table = h5.create_table(group_path, 'items', description, title='Mission Items')
                for item in mission.items:
                    item_obj = MissionItemTableObject.from_model(item)
                    item_obj.to_row(table)
                table.flush()

            # Flush all changes.
            h5.flush()

    # * method: delete
    def delete(self, id: str) -> None:
        '''
        Delete a mission by ID. Idempotent.

        :param id: The mission identifier.
        :type id: str
        '''

        group_path = self._mission_group_path(id)

        with self.client() as h5:

            # Remove the mission group if it exists.
            if h5.node_exists(group_path):
                h5.h5file.remove_node(group_path, recursive=True)
                h5.flush()

        # Also delete associated assignment.
        self.delete_assignment(id)

    # * method: save_assignment
    def save_assignment(self, assignment: DeviceAssignmentAggregate) -> None:
        '''
        Persist a device assignment record.

        :param assignment: The device assignment aggregate.
        :type assignment: DeviceAssignmentAggregate
        '''

        with self.client() as h5:

            # Get or create the assignments table.
            description = DeviceAssignmentTableObject.get_description()
            table = h5.get_or_create_table(ASSIGNMENTS_PATH, description, title='Device Assignments')

            # Remove any existing assignment for this mission.
            for row in table.where(f'mission_id == b"{assignment.mission_id}"'):
                row.delete()

            # Append the new assignment.
            obj = DeviceAssignmentTableObject.from_model(assignment)
            obj.to_row(table)

            # Flush changes.
            table.flush()
            h5.flush()

    # * method: get_assignment
    def get_assignment(self, mission_id: str) -> Optional[DeviceAssignmentAggregate]:
        '''
        Retrieve the active device assignment for a mission.

        :param mission_id: The mission identifier.
        :type mission_id: str
        :return: The device assignment aggregate, or None.
        :rtype: DeviceAssignmentAggregate | None
        '''

        with self.client(mode='r') as h5:

            # Check if the assignments table exists.
            if not h5.node_exists(ASSIGNMENTS_PATH):
                return None

            # Query for the assignment.
            table = h5.get_table(ASSIGNMENTS_PATH)
            for row in table.where(f'mission_id == b"{mission_id}"'):
                obj = DeviceAssignmentTableObject.from_row(row)
                return obj.map()

        # No assignment found.
        return None

    # * method: delete_assignment
    def delete_assignment(self, mission_id: str) -> None:
        '''
        Delete the device assignment for a mission. Idempotent.

        :param mission_id: The mission identifier.
        :type mission_id: str
        '''

        with self.client() as h5:

            # Check if the assignments table exists.
            if not h5.node_exists(ASSIGNMENTS_PATH):
                return

            # Remove matching rows.
            table = h5.get_table(ASSIGNMENTS_PATH)
            rows_to_remove = []
            for row in table.where(f'mission_id == b"{mission_id}"'):
                rows_to_remove.append(row.nrow)

            # Delete in reverse order to preserve indices.
            for nrow in reversed(rows_to_remove):
                table.remove_row(nrow)

            # Flush changes.
            table.flush()
            h5.flush()
