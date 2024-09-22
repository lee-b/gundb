import unittest
import uuid
from src.gundb.models import EventStream, Event, View, UserStream, UserCreatedEvent, UserUpdatedEvent, EventStreamUUID
from src.gundb.site import Site, SiteUUID

class TestModels(unittest.TestCase):

    def setUp(self):
        self.site = Site()
        self.stream_id = EventStreamUUID(uuid.uuid4())

    def test_event_stream_creation(self):
        stream = EventStream("test_stream")
        self.assertIsInstance(stream.id, uuid.UUID)
        self.assertEqual(stream.name, "test_stream")

    def test_event_creation(self):
        event = Event(self.stream_id, self.site)
        self.assertIsInstance(event.id, uuid.UUID)
        self.assertEqual(event.stream_id, self.stream_id)
        self.assertIsInstance(event.vector_clock, dict)
        self.assertIn((self.site.id, self.stream_id), event.vector_clock)

    def test_view_creation(self):
        view = View(self.stream_id)
        self.assertIsInstance(view.id, uuid.UUID)
        self.assertEqual(view.stream_id, self.stream_id)
        self.assertIsInstance(view.snapshot, dict)
        self.assertIsInstance(view.vector_clock, dict)

    def test_user_stream_creation(self):
        user_stream = UserStream()
        self.assertIsInstance(user_stream.id, uuid.UUID)
        self.assertEqual(user_stream.name, "user_stream")

    def test_user_created_event(self):
        event = UserCreatedEvent(self.stream_id, self.site, data={"username": "test_user"})
        self.assertIsInstance(event.id, uuid.UUID)
        self.assertEqual(event.stream_id, self.stream_id)
        self.assertEqual(event.data, {"username": "test_user"})

    def test_user_updated_event(self):
        event = UserUpdatedEvent(self.stream_id, self.site, data={"email": "test@example.com"})
        self.assertIsInstance(event.id, uuid.UUID)
        self.assertEqual(event.stream_id, self.stream_id)
        self.assertEqual(event.data, {"email": "test@example.com"})

    def test_site_creation(self):
        site = Site()
        self.assertIsInstance(site.id, uuid.UUID)

    def test_site_creation_with_id(self):
        site_id = SiteUUID(uuid.uuid4())
        site = Site(site_id)
        self.assertEqual(site.id, site_id)

if __name__ == '__main__':
    unittest.main()
