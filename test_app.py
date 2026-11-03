import tempfile
from pathlib import Path
import unittest
from app import initialize, create_incident, list_incidents, update_incident


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / 'test.sqlite3')
        initialize(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_close_and_reopen(self):
        incident_id = create_incident(self.path, {'title': 'Database alert', 'priority': 'high'})
        self.assertEqual(list_incidents(self.path)[0]['status'], 'open')
        self.assertTrue(update_incident(self.path, incident_id, 'closed'))
        self.assertEqual(list_incidents(self.path)[0]['status'], 'closed')
        self.assertTrue(update_incident(self.path, incident_id, 'open'))

    def test_parameterized_text_and_persistence(self):
        title = "Example'); DROP TABLE incidents; --"
        create_incident(self.path, {'title': title})
        initialize(self.path)
        self.assertEqual(list_incidents(self.path)[0]['title'], title)

    def test_invalid_input_and_missing_id(self):
        for data in [{'title': 'x'}, {'title': 'Example', 'priority': 'urgent'}, []]:
            with self.assertRaises(ValueError):
                create_incident(self.path, data)
        with self.assertRaises(ValueError):
            update_incident(self.path, 1, 'deleted')
        self.assertFalse(update_incident(self.path, 999, 'closed'))


if __name__ == '__main__':
    unittest.main()
