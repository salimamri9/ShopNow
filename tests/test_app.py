import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import app  # noqa: E402


class ShopNowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings = app.load_settings({"SHOP_PORT": "0", "SHOP_ENV": "test"})
        products = app.load_products(settings["products_file"])
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), app.make_handler(settings, products))
        cls.base = "http://127.0.0.1:%d" % cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as r:
            return r.status, r.read().decode()

    def test_health(self):
        status, body = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["status"], "ok")

    def test_products(self):
        status, body = self.get("/api/products")
        self.assertEqual(status, 200)
        self.assertGreater(len(json.loads(body)), 0)

    def test_home_shows_products(self):
        status, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn("Rubber duck", body)
        self.assertIn("test mode", body)

    def test_unknown_page_is_404(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/nope")
        self.assertEqual(ctx.exception.code, 404)

    def test_env_overrides_config(self):
        settings = app.load_settings({"SHOP_HOST": "0.0.0.0", "SHOP_PORT": "9000"})
        self.assertEqual((settings["host"], settings["port"]), ("0.0.0.0", 9000))

    def test_unreadable_config_raises(self):
        with self.assertRaises(OSError):
            app.load_settings({"SHOP_CONFIG": os.devnull + "-missing"})


if __name__ == "__main__":
    unittest.main()
