import requests
import json


class JSONRPCError(Exception):
    def __init__(self, code, message):
        super().__init__()
        self._code = code
        self._message = message

    @property
    def code(self):
        return self._code

    @property
    def message(self):
        return self._message

    def __str__(self):
        return f"JSONRPCError (code: {self.code}, message: {self.message})"


class BSHLocalAPI:
    def __init__(self, controller_ip: str, certificate, key):
        self._certificate = certificate
        self._key = key
        self._controller_ip = controller_ip
        self._api_root = f"https://{self._controller_ip}:8444/smarthome"
        self._rpc_root = f"https://{self._controller_ip}:8444/remote/json-rpc"

        # Settings for all API calls
        self._requests_session = requests.Session()
        self._requests_session.cert = (self._certificate, self._key)
        self._requests_session.headers.update({"api-version": "1.0", "Content-Type": "application/json"})
        self._requests_session.verify = False

        import urllib3
        urllib3.disable_warnings()

    def _get_api_result_or_fail(self, api_url, expected_type=None, expected_element_type=None, headers=None):
        result = self._requests_session.get(api_url, headers=headers)
        if not result.ok:
            self._process_nok_result(result)

        else:
            if len(result.content) > 0:
                result = json.loads(result.content)
                if expected_type is not None:
                    assert result['@type'] == expected_type
                if expected_element_type is not None:
                    for result_ in result:
                        assert result_['@type'] == expected_element_type

                return result
            else:
                return {}

    def _put_api_or_fail(self, api_url, body):
        result = self._requests_session.put(api_url, data=json.dumps(body))
        if not result.ok:
            self._process_nok_result(result)
        if len(result.content) > 0:
            return json.loads(result.content)
        else:
            return {}

    def _post_api_or_fail(self, api_url, body):
        result = self._requests_session.post(api_url, data=json.dumps(body))
        if not result.ok:
            self._process_nok_result(result)
        if len(result.content) > 0:
            return json.loads(result.content)
        else:
            return {}

    def _process_nok_result(self, result):
        print(f"Body: {result.request.body}")
        print(f"Headers: {result.request.headers}")
        print(f"URL: {result.request.url}")
        raise ValueError(f"API call returned non-OK result (code {result.status_code})!: {result.content}")

    # API calls here
    def get_rooms(self):
        api_url = f"{self._api_root}/rooms"
        return self._get_api_result_or_fail(api_url, expected_element_type="room")

    def get_devices(self):
        api_url = f"{self._api_root}/devices"
        return self._get_api_result_or_fail(api_url, expected_element_type="device")

    def get_device_service(self, device_id, service_id):
        api_url = f"{self._api_root}/devices/{device_id}/services/{service_id}"
        return self._get_api_result_or_fail(api_url, expected_type="DeviceServiceData")

    def put_device_service_state(self, device_id, service_id, state_update):
        api_url = f"{self._api_root}/devices/{device_id}/services/{service_id}/state"
        self._put_api_or_fail(api_url, state_update)

    def long_polling_subscribe(self):
        data = [
            {
                "jsonrpc": "2.0",
                "method": "RE/subscribe",
                "params": ["com/bosch/sh/remote/*", None]
            }
        ]
        result = self._post_api_or_fail(self._rpc_root, data)
        assert result[0]["jsonrpc"] == "2.0"
        if "error" in result[0].keys():
            raise JSONRPCError(result[0]['error']['code'], result[0]['error']['message'])
        else:
            return result[0]["result"]

    def long_polling_poll(self, poll_id, wait_seconds=30):
        data = [
            {
                "jsonrpc": "2.0",
                "method": "RE/longPoll",
                "params": [poll_id, wait_seconds]
            }
        ]
        result = self._post_api_or_fail(self._rpc_root, data)
        assert result[0]["jsonrpc"] == "2.0"
        if "error" in result[0].keys():
            raise JSONRPCError(result[0]['error']['code'], result[0]['error']['message'])
        else:
            return result[0]["result"]

    def long_polling_unsubscribe(self, poll_id):
        data = [
            {
                "jsonrpc": "2.0",
                "method": "RE/unsubscribe",
                "params": [poll_id]
            }
        ]
        result = self._post_api_or_fail(self._rpc_root, data)
        assert result[0]["jsonrpc"] == "2.0"
        if "error" in result[0].keys():
            raise JSONRPCError(result[0]['error']['code'], result[0]['error']['message'])
        else:
            return result[0]["result"]