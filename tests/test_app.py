import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.parse
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

    def test_product_page(self):
        status, body = self.get("/product/9")
        self.assertEqual(status, 200)
        self.assertIn("Rubber duck", body)
        self.assertIn("Add to cart", body)

    def test_category_and_search(self):
        _, body = self.get("/?category=Merch")
        self.assertIn("Penguin plush", body)
        self.assertNotIn("Wireless mouse", body)
        _, body = self.get("/?q=duck")
        self.assertIn("Rubber duck", body)
        self.assertNotIn("Penguin plush", body)

    def test_search_is_escaped(self):
        _, body = self.get("/?q=%3Cscript%3Ex")
        self.assertNotIn("<script>x", body)

    def test_static_image_and_no_escape(self):
        with urllib.request.urlopen(self.base + "/static/img/duck.jpg") as r:
            self.assertEqual(r.headers["Content-Type"], "image/jpeg")
        for bad in ("/static/../app.py", "/static/%2e%2e/config.yml", "/static/img/../../config.yml"):
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                self.get(bad)
            self.assertEqual(ctx.exception.code, 404)

    def test_checkout_confirms_order(self):
        data = urllib.parse.urlencode({"name": "Amira", "phone": "1", "address": "x", "items": "{}"}).encode()
        with urllib.request.urlopen(self.base + "/checkout", data=data) as r:
            body = r.read().decode()
        self.assertIn("Thank you, Amira!", body)

    def test_env_overrides_config(self):
        settings = app.load_settings({"SHOP_HOST": "0.0.0.0", "SHOP_PORT": "9000"})
        self.assertEqual((settings["host"], settings["port"]), ("0.0.0.0", 9000))

    def test_unreadable_config_raises(self):
        with self.assertRaises(OSError):
            app.load_settings({"SHOP_CONFIG": os.devnull + "-missing"})


if __name__ == "__main__":
    unittest.main()
