"""tiferet_mission Interfaces Device"""

# *** imports

# ** core
from abc import abstractmethod
from typing import Optional

# ** app
from tiferet.interfaces import Service

# *** interfaces

# ** interface: device_registry_service
class DeviceRegistryService(Service):
    '''
    Read-only service interface for querying device information from
    the consuming application's device registry.

    This interface is NOT implemented by tiferet-mission — the consuming
    application must provide a concrete implementation and inject it
    via container configuration.
    '''

    # * method: device_exists
    @abstractmethod
    def device_exists(self, device_id: str) -> bool:
        '''
        Check whether a device exists in the registry.

        :param device_id: The device identifier.
        :type device_id: str
        :return: True if the device exists.
        :rtype: bool
        '''
        raise NotImplementedError()

    # * method: get_device_type
    @abstractmethod
    def get_device_type(self, device_id: str) -> Optional[str]:
        '''
        Retrieve the drone type classification for a device.

        :param device_id: The device identifier.
        :type device_id: str
        :return: The drone type string (e.g., 'copter', 'plane'), or None if not found.
        :rtype: str | None
        '''
        raise NotImplementedError()
