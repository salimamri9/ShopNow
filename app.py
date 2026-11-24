#!/usr/bin/env python3
"""ShopNow: the small online shop Sara deploys in the Cloud & DevOps sessions.

Plain Python 3, no packages to install. Settings come from config.yml and can be
overridden with environment variables:

    SHOP_HOST    address to listen on       (default 127.0.0.1)
    SHOP_PORT    port to listen on          (default 8000)
    SHOP_ENV     development or production  (default development)
    SHOP_CONFIG  path to the config file    (default config.yml next to app.py)
"""
import html
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent


def load_config(path):
    """Read a flat 'key: value' YAML file. Raises PermissionError if unreadable."""
    config = {}
    with open(path) as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            config[key.strip()] = value.strip().strip("\"'")
    return config


def load_settings(environ=os.environ):
    config_path = environ.get("SHOP_CONFIG", str(BASE / "config.yml"))
    config = load_config(config_path)
    return {
        "name": config.get("shop_name", "ShopNow"),
        "currency": config.get("currency", "TND"),
        "host": environ.get("SHOP_HOST", config.get("host", "127.0.0.1")),
        "port": int(environ.get("SHOP_PORT", config.get("port", "8000"))),
        "env": environ.get("SHOP_ENV", config.get("env", "development")),
        "products_file": str(BASE / config.get("products_file", "products.json")),
    }


def load_products(path):
    with open(path) as f:
        return json.load(f)


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name}</title>
<style>
  body {{ margin: 0; font-family: system-ui, sans-serif; background: #f6f4ef; color: #1d1d1b; }}
  header {{ background: #0b0f14; color: #f6f4ef; padding: 24px 40px; display: flex; align-items: baseline; gap: 16px; }}
  header h1 {{ margin: 0; font-size: 28px; }}
  header span {{ color: #3ddc84; font-family: monospace; }}
  .ribbon {{ background: #ffb46b; padding: 8px 40px; font-family: monospace; }}
  main {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; padding: 32px 40px; }}
  .card {{ background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px #0001; }}
  .card .emoji {{ font-size: 40px; }}
  .card h2 {{ font-size: 18px; margin: 12px 0 4px; }}
  .card p {{ margin: 0; color: #555; }}
  .price {{ margin-top: 12px; font-weight: 700; }}
  footer {{ padding: 16px 40px; color: #777; font-family: monospace; font-size: 13px; }}
</style></head>
<body>
<header><h1>{name}</h1><span>served by {hostname}</span></header>
{ribbon}
<main>{cards}</main>
<footer>env={env} · <a href="/health">/health</a> · <a href="/api/products">/api/products</a></footer>
</body></html>
"""


def render_home(settings, products):
    cards = "".join(
        '<div class="card"><div class="emoji">{e}</div><h2>{n}</h2><p>{d}</p>'
        '<div class="price">{p} {c}</div></div>'.format(
            e=html.escape(p.get("emoji", "")),
            n=html.escape(p["name"]),
            d=html.escape(p.get("description", "")),
            p=html.escape(str(p["price"])),
            c=html.escape(settings["currency"]),
        )
        for p in products
    )
    ribbon = ""
    if settings["env"] != "production":
        ribbon = '<div class="ribbon">{} mode: not for real customers</div>'.format(
            html.escape(settings["env"]))
    return PAGE.format(
        name=html.escape(settings["name"]),
        hostname=html.escape(os.uname().nodename),
        ribbon=ribbon,
        cards=cards,
        env=html.escape(settings["env"]),
    )


def make_handler(settings, products):
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, body, content_type):
            data = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                self.send(200, render_home(settings, products), "text/html; charset=utf-8")
            elif path == "/health":
                self.send(200, json.dumps({"status": "ok", "env": settings["env"]}), "application/json")
            elif path == "/api/products":
                self.send(200, json.dumps(products), "application/json")
            else:
                self.send(404, json.dumps({"error": "not found"}), "application/json")

        do_HEAD = do_GET

        def log_message(self, fmt, *args):
            pass

        def log_request(self, code="-", size="-"):
            # One line per request, like: GET /health 200
            print("{} {} {}".format(self.command, self.path, code), flush=True)

    return Handler


def main():
    settings = load_settings()
    products = load_products(settings["products_file"])
    server = ThreadingHTTPServer((settings["host"], settings["port"]), make_handler(settings, products))
    print("ShopNow ({}) listening on {}:{}".format(settings["env"], settings["host"], settings["port"]), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping.", file=sys.stderr)


if __name__ == "__main__":
    main()
