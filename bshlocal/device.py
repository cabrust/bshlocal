import typing
import logging

from .device_service import BSHLocalDeviceService
from .services_impl import build, SUPPORTED_DEVICE_SERVICE_IDS

logger = logging.getLogger("bshlocal")


class BSHLocalDevice:
    def __init__(self, api, raw_device):
        self._api = api
        self._raw_device = raw_device

        self._device_services_by_id = {}
        self._enumerate_services()

    def _enumerate_services(self):
        for device_service_id in self._raw_device['deviceServiceIds']:
            if device_service_id not in SUPPORTED_DEVICE_SERVICE_IDS:
                continue

            raw_device_service_data = self._api.get_device_service(self.id, device_service_id)
            device_service = build(self._api, raw_device_service_data)

            self._device_services_by_id[device_service_id] = device_service

    @property
    def root_device_id(self):
        return self._raw_device['rootDeviceId']

    @property
    def id(self):
        return self._raw_device['id']

    @property
    def manufacturer(self):
        return self._raw_device['manufacturer']

    @property
    def room_id(self):
        return self._raw_device['roomId']

    @property
    def device_model(self):
        return self._raw_device['deviceModel']

    @property
    def serial(self):
        return self._raw_device['serial']

    @property
    def profile(self):
        return self._raw_device['profile']

    @property
    def name(self):
        return self._raw_device['name']

    @property
    def status(self):
        return self._raw_device['status']

    @property
    def device_services(self) -> typing.Sequence[BSHLocalDeviceService]:
        return list(self._device_services_by_id.values())

    @property
    def device_service_ids(self) -> typing.Set[str]:
        return set(self._device_services_by_id.keys())
    
    def device_service(self, device_service_id):
        return self._device_services_by_id[device_service_id]

    def summary(self):
        print(f"Device: {self.id}")
        print(f"  Name          : {self.name}")
        print(f"  Manufacturer  : {self.manufacturer}")
        print(f"  Model         : {self.device_model}")
        print(f"  Room          : {self.room_id}")
        print(f"  Serial        : {self.serial}")
        for device_service in self.device_services:
            device_service.summary()

    def process_long_polling_poll_result(self, raw_result):
        assert raw_result["@type"] == "DeviceServiceData"
        device_service_id = raw_result["id"]
        if device_service_id in self._device_services_by_id.keys():
            device_service = self._device_services_by_id[device_service_id]
            device_service.process_long_polling_poll_result(raw_result)
        else:
            logger.debug(f"Skipping polling result with unknown device service id {device_service_id}.")
