"""tiferet_mission Repos SQLite"""

# *** imports

# ** core
from pathlib import Path
from typing import List, Optional

# ** app
from tiferet.utils import Sqlite
from ..interfaces.mission import MissionService
from ..mappers.mission import MissionAggregate, MissionItemAggregate
from ..mappers.assignment import DeviceAssignmentAggregate
from ..mappers.mission_sql import (
    MissionSqlObject,
    MissionItemSqlObject,
    DeviceAssignmentSqlObject,
)

# *** constants

# ** constant: schema_sql
SCHEMA_SQL = '''
CREATE TABLE IF NOT EXISTS missions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    drone_type TEXT NOT NULL,
    device_id TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS mission_items (
    id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    command TEXT NOT NULL,
    command_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    frame TEXT NOT NULL DEFAULT 'GLOBAL_RELATIVE_ALT',
    param1 REAL DEFAULT 0.0,
    param2 REAL DEFAULT 0.0,
    param3 REAL DEFAULT 0.0,
    param4 REAL DEFAULT 0.0,
    latitude REAL DEFAULT 0.0,
    longitude REAL DEFAULT 0.0,
    altitude REAL DEFAULT 0.0,
    autocontinue INTEGER DEFAULT 1,
    description TEXT
);
CREATE TABLE IF NOT EXISTS device_assignments (
    mission_id TEXT PRIMARY KEY REFERENCES missions(id) ON DELETE CASCADE,
    device_id TEXT NOT NULL,
    drone_type TEXT NOT NULL,
    assigned_at REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
);
'''

# *** repos

# ** repo: mission_sqlite_repository
class MissionSqliteRepository(MissionService):
    '''
    SQLite-backed implementation of MissionService.
    '''

    # * attribute: db_path
    db_path: str

    # * attribute: mode
    mode: str

    # * init
    def __init__(self, db_path: str, mode: str = 'rwc'):
        '''
        Initialize the MissionSqliteRepository.

        :param db_path: Path to the SQLite database file.
        :type db_path: str
        :param mode: SQLite connection mode.
        :type mode: str
        '''

        # Store configuration.
        self.db_path = db_path
        self.mode = mode

        # Ensure schema exists.
        self._ensure_schema()

    # * method: _ensure_schema
    def _ensure_schema(self) -> None:
        '''
        Create tables if they do not exist.
        '''

        # Open the database and execute schema DDL.
        with Sqlite(path=self.db_path, mode=self.mode) as db:
            db.executescript(SCHEMA_SQL)
            db.commit()

    # * method: exists
    def exists(self, id: str) -> bool:
        '''
        Check if a mission exists by ID.

        :param id: The mission identifier.
        :type id: str
        :return: True if the mission exists.
        :rtype: bool
        '''

        # Query for the mission ID.
        with Sqlite(path=self.db_path, mode='ro') as db:
            row = db.fetch_one('SELECT 1 FROM missions WHERE id = ?', (id,))
            return row is not None

    # * method: get
    def get(self, id: str) -> Optional[MissionAggregate]:
        '''
        Retrieve a mission by ID with its items.

        :param id: The mission identifier.
        :type id: str
        :return: The mission aggregate, or None.
        :rtype: MissionAggregate | None
        '''

        # Fetch the mission row.
        with Sqlite(path=self.db_path, mode='ro') as db:
            mission_row = db.fetch_one(
                'SELECT * FROM missions WHERE id = ?', (id,),
            )
            if mission_row is None:
                return None

            # Fetch associated items.
            item_rows = db.fetch_all(
                'SELECT * FROM mission_items WHERE mission_id = ? ORDER BY sequence',
                (id,),
            )

        # Map mission row to SQL object then to aggregate.
        mission_cols = ['id', 'name', 'description', 'status', 'drone_type', 'device_id', 'created_at', 'updated_at']
        mission_dict = dict(zip(mission_cols, mission_row))

        # Map item rows to aggregates.
        item_cols = ['id', 'mission_id', 'sequence', 'command', 'command_id', 'category', 'frame',
                     'param1', 'param2', 'param3', 'param4', 'latitude', 'longitude', 'altitude',
                     'autocontinue', 'description']
        items = []
        for row in item_rows:
            item_dict = dict(zip(item_cols, row))
            item_dict['autocontinue'] = bool(item_dict['autocontinue'])
            item_obj = MissionItemSqlObject.from_sql_row(item_dict)
            items.append(item_obj.map())

        # Map and return the aggregate with items.
        mission_obj = MissionSqlObject.from_sql_row(mission_dict)
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

        # Build the query with optional filters.
        query = 'SELECT id FROM missions WHERE 1=1'
        params = []
        if drone_type is not None:
            query += ' AND drone_type = ?'
            params.append(drone_type)
        if status is not None:
            query += ' AND status = ?'
            params.append(status)

        # Fetch matching IDs.
        with Sqlite(path=self.db_path, mode='ro') as db:
            rows = db.fetch_all(query, tuple(params))

        # Retrieve full missions by ID.
        return [self.get(row[0]) for row in rows if self.get(row[0]) is not None]

    # * method: save
    def save(self, mission: MissionAggregate) -> None:
        '''
        Save or update a mission and its items.

        :param mission: The mission aggregate to persist.
        :type mission: MissionAggregate
        '''

        # Serialize the mission to a SQL dict.
        mission_obj = MissionSqlObject.from_model(mission)
        data = mission_obj.to_sql_dict()

        with Sqlite(path=self.db_path, mode=self.mode) as db:

            # Upsert the mission row.
            db.execute(
                '''INSERT OR REPLACE INTO missions
                   (id, name, description, status, drone_type, device_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (data['id'], data['name'], data.get('description'), data['status'],
                 data['drone_type'], data.get('device_id'), data['created_at'], data['updated_at']),
            )

            # Delete existing items and re-insert.
            db.execute('DELETE FROM mission_items WHERE mission_id = ?', (data['id'],))
            for item in mission.items:
                item_obj = MissionItemSqlObject.from_model(item, mission_id=data['id'])
                idata = item_obj.to_sql_dict()
                db.execute(
                    '''INSERT INTO mission_items
                       (id, mission_id, sequence, command, command_id, category, frame,
                        param1, param2, param3, param4, latitude, longitude, altitude,
                        autocontinue, description)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (idata['id'], idata['mission_id'], idata['sequence'], idata['command'],
                     idata['command_id'], idata['category'], idata['frame'],
                     idata.get('param1', 0.0), idata.get('param2', 0.0),
                     idata.get('param3', 0.0), idata.get('param4', 0.0),
                     idata.get('latitude', 0.0), idata.get('longitude', 0.0),
                     idata.get('altitude', 0.0), int(idata.get('autocontinue', True)),
                     idata.get('description')),
                )

            # Commit the transaction.
            db.commit()

    # * method: delete
    def delete(self, id: str) -> None:
        '''
        Delete a mission by ID. Idempotent.

        :param id: The mission identifier.
        :type id: str
        '''

        # Delete the mission and cascading items.
        with Sqlite(path=self.db_path, mode=self.mode) as db:
            db.execute('DELETE FROM mission_items WHERE mission_id = ?', (id,))
            db.execute('DELETE FROM device_assignments WHERE mission_id = ?', (id,))
            db.execute('DELETE FROM missions WHERE id = ?', (id,))
            db.commit()

    # * method: save_assignment
    def save_assignment(self, assignment: DeviceAssignmentAggregate) -> None:
        '''
        Persist a device assignment record.

        :param assignment: The device assignment aggregate.
        :type assignment: DeviceAssignmentAggregate
        '''

        # Serialize and upsert.
        obj = DeviceAssignmentSqlObject.from_model(assignment)
        data = obj.to_sql_dict()

        with Sqlite(path=self.db_path, mode=self.mode) as db:
            db.execute(
                '''INSERT OR REPLACE INTO device_assignments
                   (mission_id, device_id, drone_type, assigned_at, status)
                   VALUES (?, ?, ?, ?, ?)''',
                (data['mission_id'], data['device_id'], data['drone_type'],
                 data['assigned_at'], data['status']),
            )
            db.commit()

    # * method: get_assignment
    def get_assignment(self, mission_id: str) -> Optional[DeviceAssignmentAggregate]:
        '''
        Retrieve the active device assignment for a mission.

        :param mission_id: The mission identifier.
        :type mission_id: str
        :return: The device assignment aggregate, or None.
        :rtype: DeviceAssignmentAggregate | None
        '''

        # Fetch the assignment row.
        with Sqlite(path=self.db_path, mode='ro') as db:
            row = db.fetch_one(
                'SELECT * FROM device_assignments WHERE mission_id = ?',
                (mission_id,),
            )
            if row is None:
                return None

        # Map to aggregate.
        cols = ['mission_id', 'device_id', 'drone_type', 'assigned_at', 'status']
        data = dict(zip(cols, row))
        obj = DeviceAssignmentSqlObject.from_sql_row(data)
        return obj.map()

    # * method: delete_assignment
    def delete_assignment(self, mission_id: str) -> None:
        '''
        Delete the device assignment for a mission. Idempotent.

        :param mission_id: The mission identifier.
        :type mission_id: str
        '''

        # Delete the assignment row.
        with Sqlite(path=self.db_path, mode=self.mode) as db:
            db.execute(
                'DELETE FROM device_assignments WHERE mission_id = ?',
                (mission_id,),
            )
            db.commit()
