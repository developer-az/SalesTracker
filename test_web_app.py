import os
import tempfile
import shutil
import json
import importlib
import unittest
from unittest.mock import patch


class WebAppTestCase(unittest.TestCase):
    def setUp(self):
        # Temp storage for recipients/subscriptions
        self.tmpdir = tempfile.mkdtemp()
        self.recipients_path = os.path.join(self.tmpdir, "recipients.json")
        self.subscriptions_path = os.path.join(self.tmpdir, "subscriptions.json")

        # Inject paths
        import recipients_store
        import subscriptions_store
        recipients_store.RECIPIENTS_FILE = self.recipients_path
        subscriptions_store.SUBSCRIPTIONS_FILE = self.subscriptions_path

        # Set cron token env and (re)load app
        os.environ["CRON_TOKEN"] = "testtoken"
        global web_app
        import web_app as _web_app
        importlib.reload(_web_app)
        web_app = _web_app
        web_app.app.config["TESTING"] = True
        self.client = web_app.app.test_client()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_recipients_flow(self):
        # Initially empty
        resp = self.client.get("/api/recipients")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["success"]) 
        self.assertEqual(resp.json["recipients"], [])

        # Add
        resp = self.client.post("/api/recipients", json={"email": "user@example.com"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["success"]) 

        # List
        resp = self.client.get("/api/recipients")
        self.assertIn("user@example.com", resp.json["recipients"]) 

        # Remove
        resp = self.client.delete("/api/recipients", json={"email": "user@example.com"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["success"]) 

    def test_subscriptions_flow(self):
        email = "user@example.com"
        url = "https://www.nike.com/t/unlimited-mens-repel-hooded-versatile-jacket-56pDjs/FB7551-010"

        # Add product
        resp = self.client.post("/api/subscriptions", json={"email": email, "url": url})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["success"]) 

        # List for user
        resp = self.client.get(f"/api/subscriptions?email={email}")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["success"]) 
        self.assertEqual(len(resp.json.get("products", [])), 1)

        # Remove
        resp = self.client.delete("/api/subscriptions", json={"email": email, "url": url})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["success"]) 

    @patch("web_app.main_improved.send_personalized_emails", return_value=None)
    def test_cron_send_authorized(self, _mock_send):
        resp = self.client.post("/api/cron/send", headers={"X-CRON-TOKEN": "testtoken"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["success"]) 

    def test_cron_send_unauthorized(self):
        resp = self.client.post("/api/cron/send", headers={"X-CRON-TOKEN": "wrong"})
        self.assertEqual(resp.status_code, 401)
        self.assertFalse(resp.json["success"]) 


if __name__ == "__main__":
    unittest.main(verbosity=2)


