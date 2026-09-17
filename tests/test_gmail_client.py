import logging
import threading
import unittest

from storage_manager.gmail_client import GmailClient
from storage_manager.models import ScanResult


class FakeRequest:
    def __init__(self, response):
        self.response = response

    def execute(self, num_retries=0):
        return self.response


class FakeBatch:
    def __init__(self, callback):
        self.callback = callback
        self.requests = []

    def add(self, request, request_id):
        self.requests.append((request_id, request))

    def execute(self):
        for request_id, request in self.requests:
            self.callback(request_id, request.response, None)


class FakeMessages:
    def __init__(self):
        self.list_calls = []
        self.deleted_groups = []

    def list(self, **kwargs):
        self.list_calls.append(kwargs)
        if kwargs.get("pageToken") is None:
            return FakeRequest(
                {
                    "messages": [{"id": "m1"}, {"id": "m2"}],
                    "nextPageToken": "next-page",
                }
            )
        return FakeRequest({"messages": [{"id": "m3"}]})

    def get(self, **kwargs):
        number = int(kwargs["id"][-1])
        return FakeRequest(
            {
                "id": kwargs["id"],
                "sizeEstimate": number * 100,
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": f"Assunto {number}"},
                        {"name": "Date", "value": f"Data {number}"},
                    ]
                },
            }
        )

    def batchDelete(self, **kwargs):
        self.deleted_groups.append(list(kwargs["body"]["ids"]))
        return FakeRequest({})


class FakeUsers:
    def __init__(self, messages):
        self._messages = messages

    def messages(self):
        return self._messages

    def getProfile(self, **_kwargs):
        return FakeRequest({"emailAddress": "colaborador@gmail.com"})


class FakeApi:
    def __init__(self):
        self.messages_resource = FakeMessages()

    def users(self):
        return FakeUsers(self.messages_resource)

    def new_batch_http_request(self, callback):
        return FakeBatch(callback)


def make_client():
    client = GmailClient.__new__(GmailClient)
    client.api = FakeApi()
    client.logger = logging.getLogger("test-gmail-client")
    return client


class GmailClientTests(unittest.TestCase):
    def test_accepts_connected_account_when_no_account_is_fixed(self):
        client = make_client()
        self.assertEqual(client.verify_account(), "colaborador@gmail.com")

    def test_scan_collects_every_page_before_returning(self):
        client = make_client()
        progress = []

        result = client.scan_sender(
            "from:diligencia@mlradvogados.com",
            preview_limit=2,
            cancel=threading.Event(),
            progress=lambda current, total, text: progress.append((current, total, text)),
        )

        self.assertEqual(result.message_ids, ["m1", "m2", "m3"])
        self.assertEqual(result.total_bytes, 600)
        self.assertEqual(len(result.previews), 2)
        self.assertEqual(len(client.api.messages_resource.list_calls), 2)
        self.assertTrue(
            all(call["includeSpamTrash"] for call in client.api.messages_resource.list_calls)
        )
        self.assertTrue(progress)

    def test_delete_splits_frozen_ids_into_safe_batches(self):
        client = make_client()
        ids = [f"m{index}" for index in range(1001)]
        scan = ScanResult(query="from:teste@example.com", message_ids=ids, total_bytes=1234)

        result = client.permanently_delete(
            scan,
            batch_size=500,
            cancel=threading.Event(),
            progress=lambda _current, _total, _text: None,
        )

        groups = client.api.messages_resource.deleted_groups
        self.assertEqual([len(group) for group in groups], [500, 500, 1])
        self.assertEqual([item for group in groups for item in group], ids)
        self.assertEqual(result.deleted, 1001)
        self.assertEqual(result.failed, 0)


if __name__ == "__main__":
    unittest.main()
