#!/usr/bin/env python3
"""ShopNow: the small online shop l3ou9 deploys in the Cloud & DevOps sessions.

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
import secrets
import sys
import urllib.parse
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


CSS = """
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:#f4f5f7;color:#16181d}
a{color:inherit;text-decoration:none}
.wrap{max-width:1200px;margin:0 auto;padding:0 24px}
.ribbon{background:#fff4e5;color:#8a4b00;border-bottom:1px solid #ffd8a8;font-size:13px;text-align:center;padding:6px}
.top{background:#12161c;color:#fff;position:sticky;top:0;z-index:5}
.top .wrap{display:flex;align-items:center;gap:24px;height:64px}
.logo{font-weight:800;font-size:22px;letter-spacing:-.5px}
.logo span{color:#ff7a1a}
.search{flex:1;display:flex}
.search input{flex:1;border:0;border-radius:8px 0 0 8px;padding:11px 14px;font-size:15px}
.search button{border:0;background:#ff7a1a;color:#fff;font-weight:700;padding:0 18px;border-radius:0 8px 8px 0;cursor:pointer}
.cartlink{display:flex;align-items:center;gap:8px;font-weight:600}
.badge{background:#ff7a1a;color:#fff;border-radius:999px;min-width:22px;height:22px;font-size:12px;display:inline-flex;align-items:center;justify-content:center;padding:0 6px}
.cats{background:#1c222b}
.cats .wrap{display:flex;gap:4px;overflow-x:auto;height:44px;align-items:center}
.cats a{color:#c9d1db;font-size:14px;padding:6px 12px;border-radius:6px;white-space:nowrap}
.cats a.on,.cats a:hover{background:#2e3744;color:#fff}
.hero{background:linear-gradient(110deg,#ff7a1a,#ff4d4d);color:#fff;border-radius:16px;margin:24px 0;padding:40px 48px;display:flex;justify-content:space-between;align-items:center;gap:24px}
.hero h1{margin:0 0 8px;font-size:36px;letter-spacing:-.5px}
.hero p{margin:0;font-size:17px;opacity:.95}
.hero .code{background:#fff;color:#ff4d4d;font-weight:800;padding:12px 18px;border-radius:10px;font-family:ui-monospace,monospace;white-space:nowrap}
.perks{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px}
.perk{background:#fff;border-radius:12px;padding:14px 18px;font-size:14px;color:#4a5260}
.perk b{display:block;color:#16181d;font-size:15px}
h2.sec{font-size:22px;margin:8px 0 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:20px;margin-bottom:40px}
.card{background:#fff;border-radius:14px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 1px 3px #0000000f;transition:box-shadow .15s,transform .15s}
.card:hover{box-shadow:0 8px 24px #00000018;transform:translateY(-2px)}
.card .img{position:relative;aspect-ratio:1;background:#eef0f3}
.card img{width:100%;height:100%;object-fit:cover;display:block}
.tag{position:absolute;top:10px;left:10px;background:#e02424;color:#fff;font-size:12px;font-weight:700;padding:4px 8px;border-radius:6px}
.tag.out{background:#4a5260}
.card .body{padding:14px 16px 16px;display:flex;flex-direction:column;gap:6px;flex:1}
.cat{font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:.5px}
.card h3{margin:0;font-size:16px;line-height:1.3}
.stars{color:#f5a524;font-size:14px}
.stars span{color:#6b7280}
.price{font-size:20px;font-weight:800}
.price s{font-size:14px;color:#9aa1ab;font-weight:400;margin-left:6px}
.btn{border:0;background:#16181d;color:#fff;font-weight:700;border-radius:8px;padding:11px 14px;cursor:pointer;font-size:14px;margin-top:auto}
.btn:hover{background:#ff7a1a}
.btn[disabled]{background:#c9ced6;cursor:not-allowed}
.btn.big{font-size:16px;padding:14px 22px}
.detail{display:grid;grid-template-columns:1fr 1fr;gap:40px;background:#fff;border-radius:16px;padding:32px;margin:24px 0 40px}
.detail img{width:100%;border-radius:12px}
.detail h1{margin:6px 0 10px;font-size:30px}
.detail .price{font-size:30px;margin:16px 0}
.stock{font-size:14px;font-weight:600;color:#0e8a4c}
.stock.low{color:#c2410c}.stock.none{color:#b91c1c}
.crumbs{font-size:14px;color:#6b7280;margin-top:20px}
.panel{background:#fff;border-radius:16px;padding:28px;margin:24px 0 40px}
.line{display:flex;align-items:center;gap:16px;padding:14px 0;border-bottom:1px solid #eceef1}
.line img{width:72px;height:72px;object-fit:cover;border-radius:8px}
.line .grow{flex:1}
.qty{display:flex;align-items:center;gap:8px}
.qty button{width:30px;height:30px;border:1px solid #d5d9df;background:#fff;border-radius:6px;cursor:pointer;font-size:16px}
.total{display:flex;justify-content:space-between;font-size:20px;font-weight:800;padding:18px 0}
form.co{display:grid;gap:14px;max-width:520px}
form.co label{font-size:14px;font-weight:600;display:grid;gap:6px}
form.co input,form.co select{padding:11px 12px;border:1px solid #d5d9df;border-radius:8px;font-size:15px}
.ok{font-size:48px}
.muted{color:#6b7280}
footer{background:#12161c;color:#9aa1ab;font-size:13px;padding:24px 0}
footer .wrap{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}
footer a{text-decoration:underline}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#16181d;color:#fff;padding:12px 20px;border-radius:10px;opacity:0;transition:opacity .2s;pointer-events:none}
.toast.show{opacity:1}
@media(max-width:760px){.perks{grid-template-columns:1fr}.detail{grid-template-columns:1fr}.hero{flex-direction:column;align-items:flex-start;padding:28px}.search{display:none}}
"""

# The cart lives in the browser (localStorage): no database, no login.
JS = """
const KEY='shopnow-cart';
const cart=()=>{try{return JSON.parse(localStorage.getItem(KEY))||{}}catch(e){return {}}};
const save=c=>{localStorage.setItem(KEY,JSON.stringify(c));badge()};
function badge(){const n=Object.values(cart()).reduce((a,b)=>a+b,0);document.querySelectorAll('.badge').forEach(b=>b.textContent=n)}
function add(id){const c=cart();c[id]=(c[id]||0)+1;save(c);toast('Added to cart')}
function setq(id,d){const c=cart();c[id]=(c[id]||0)+d;if(c[id]<=0)delete c[id];save(c);if(window.renderCart)renderCart()}
function toast(t){const e=document.querySelector('.toast');e.textContent=t;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),1400)}
document.addEventListener('DOMContentLoaded',badge);
"""


def esc(value):
    return html.escape(str(value))


def money(amount, settings):
    return "{:,} {}".format(amount, settings["currency"]).replace(",", " ")


def stars(rating):
    full = int(round(float(rating)))
    return "★" * full + "☆" * (5 - full)


def layout(settings, title, body, active=""):
    categories = ["All"] + sorted({p.get("category", "Other") for p in settings["_products"]})
    cats = "".join(
        '<a href="/{q}"{on}>{c}</a>'.format(
            q="" if c == "All" else "?category=" + urllib.parse.quote(c),
            on=' class="on"' if c == (active or "All") else "", c=esc(c))
        for c in categories)
    ribbon = ""
    if settings["env"] != "production":
        ribbon = '<div class="ribbon">{} mode: not for real customers</div>'.format(esc(settings["env"]))
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>{css}</style></head>
<body>
{ribbon}
<header class="top"><div class="wrap">
<a class="logo" href="/">{logo}</a>
<form class="search" action="/"><input name="q" placeholder="Search keyboards, cables, rubber ducks…"><button>Search</button></form>
<a class="cartlink" href="/cart">Cart <span class="badge">0</span></a>
</div></header>
<nav class="cats"><div class="wrap">{cats}</div></nav>
<main class="wrap">{body}</main>
<footer><div class="wrap"><span>© {name} · served by {hostname} · env={env}</span>
<span><a href="/health">/health</a> · <a href="/api/products">/api/products</a></span></div></footer>
<div class="toast"></div>
<script>{js}</script>
</body></html>
""".format(
        title=esc(title), css=CSS, js=JS, ribbon=ribbon, cats=cats, body=body,
        logo=esc(settings["name"][:-3]) + "<span>" + esc(settings["name"][-3:]) + "</span>"
        if len(settings["name"]) > 3 else esc(settings["name"]),
        name=esc(settings["name"]), hostname=esc(os.uname().nodename), env=esc(settings["env"]))


def card(p, settings):
    tag = ""
    if p.get("stock", 1) == 0:
        tag = '<span class="tag out">Sold out</span>'
    elif p.get("old_price"):
        tag = '<span class="tag">-{}%</span>'.format(round(100 - 100 * p["price"] / p["old_price"]))
    old = " <s>{}</s>".format(esc(money(p["old_price"], settings))) if p.get("old_price") else ""
    button = ('<button class="btn" onclick="add({})">Add to cart</button>'.format(int(p["id"]))
              if p.get("stock", 1) else '<button class="btn" disabled>Sold out</button>')
    return """<div class="card"><a class="img" href="/product/{id}"><img src="/static/img/{img}" alt="{name}" loading="lazy">{tag}</a>
<div class="body"><div class="cat">{cat}</div><a href="/product/{id}"><h3>{name}</h3></a>
<div class="stars">{stars} <span>({reviews})</span></div>
<div class="price">{price}{old}</div>{button}</div></div>""".format(
        id=int(p["id"]), img=esc(p.get("image", "")), name=esc(p["name"]), tag=tag,
        cat=esc(p.get("category", "")), stars=stars(p.get("rating", 0)), reviews=esc(p.get("reviews", 0)),
        price=esc(money(p["price"], settings)), old=old, button=button)


def render_home(settings, products, category="", query=""):
    shown = [p for p in products
             if (not category or p.get("category") == category)
             and (not query or query.lower() in (p["name"] + " " + p.get("description", "")).lower())]
    if query:
        heading = 'Results for “{}”'.format(esc(query))
    elif category:
        heading = esc(category)
    else:
        heading = "Popular right now"
    hero = "" if (category or query) else """<section class="hero"><div><h1>Gear for people who ship.</h1>
<p>Keyboards, screens, cables and rubber ducks. Delivered anywhere in Tunisia.</p></div>
<div class="code">CODE: DEPLOY10 · -10%</div></section>
<div class="perks"><div class="perk"><b>Free delivery</b>on orders over 150 {c}</div>
<div class="perk"><b>Pay on delivery</b>cash or card at your door</div>
<div class="perk"><b>30-day returns</b>no questions asked</div></div>""".format(c=esc(settings["currency"]))
    grid = "".join(card(p, settings) for p in shown) or '<p class="muted">Nothing found.</p>'
    body = '{hero}<h2 class="sec">{h}</h2><div class="grid">{grid}</div>'.format(hero=hero, h=heading, grid=grid)
    return layout(settings, settings["name"], body, active=category)


def render_product(settings, p):
    old = " <s>{}</s>".format(esc(money(p["old_price"], settings))) if p.get("old_price") else ""
    stock = p.get("stock", 1)
    if stock == 0:
        stock_html, button = '<div class="stock none">Sold out</div>', '<button class="btn big" disabled>Sold out</button>'
    else:
        stock_html = ('<div class="stock low">Only {} left</div>'.format(stock) if stock < 10
                      else '<div class="stock">In stock</div>')
        button = '<button class="btn big" onclick="add({})">Add to cart</button>'.format(int(p["id"]))
    body = """<div class="crumbs"><a href="/">Home</a> › <a href="/?category={qc}">{cat}</a> › {name}</div>
<div class="detail"><img src="/static/img/{img}" alt="{name}">
<div><div class="cat">{cat}</div><h1>{name}</h1>
<div class="stars">{stars} <span>{rating} · {reviews} reviews</span></div>
<div class="price">{price}{old}</div>{stock}
<p style="font-size:17px;line-height:1.55">{desc}</p>{button}
<p class="muted" style="font-size:14px;margin-top:18px">Free delivery over 150 {c} · Pay on delivery · 30-day returns</p>
</div></div>""".format(
        qc=urllib.parse.quote(p.get("category", "")), cat=esc(p.get("category", "")), name=esc(p["name"]),
        img=esc(p.get("image", "")), stars=stars(p.get("rating", 0)), rating=esc(p.get("rating", "")),
        reviews=esc(p.get("reviews", 0)), price=esc(money(p["price"], settings)), old=old, stock=stock_html,
        desc=esc(p.get("description", "")), button=button, c=esc(settings["currency"]))
    return layout(settings, p["name"] + " · " + settings["name"], body, active=p.get("category", ""))


def render_cart(settings, products):
    data = json.dumps({str(p["id"]): {"name": p["name"], "price": p["price"], "image": p.get("image", "")}
                       for p in products}).replace("</", "<\\/")
    body = """<div class="panel"><h2 class="sec">Your cart</h2><div id="lines"></div>
<div class="total"><span>Total</span><span id="total"></span></div>
<a href="/checkout" id="go"><button class="btn big">Checkout</button></a></div>
<script>
const P={data}, CUR={cur};
function renderCart(){{const c=cart(),ids=Object.keys(c).filter(i=>P[i]);let t=0;
document.getElementById('lines').innerHTML=ids.length?ids.map(i=>{{t+=P[i].price*c[i];
return `<div class="line"><img src="/static/img/${{P[i].image}}" alt=""><div class="grow"><b>${{P[i].name}}</b><div class="muted">${{P[i].price}} ${{CUR}}</div></div>
<div class="qty"><button onclick="setq(${{i}},-1)">−</button>${{c[i]}}<button onclick="setq(${{i}},1)">+</button></div></div>`}}).join(''):'<p class="muted">Your cart is empty. <a href="/" style="text-decoration:underline">Keep shopping</a></p>';
document.getElementById('total').textContent=t+' '+CUR;document.getElementById('go').style.display=ids.length?'':'none'}}
document.addEventListener('DOMContentLoaded',renderCart);
</script>""".format(data=data, cur=json.dumps(settings["currency"]))
    return layout(settings, "Cart · " + settings["name"], body)


def render_checkout(settings):
    body = """<div class="panel"><h2 class="sec">Checkout</h2>
<form class="co" method="post" action="/checkout" onsubmit="document.getElementById('items').value=JSON.stringify(cart())">
<label>Full name<input name="name" required maxlength="80"></label>
<label>Phone<input name="phone" required maxlength="20" placeholder="+216 …"></label>
<label>City<select name="city"><option>Tunis</option><option>Sousse</option><option>Sfax</option><option>Monastir</option><option>Bizerte</option><option>Other</option></select></label>
<label>Address<input name="address" required maxlength="160"></label>
<input type="hidden" name="items" id="items">
<button class="btn big">Place order · pay on delivery</button>
<p class="muted" style="font-size:13px">Demo shop: no payment is taken and nothing is shipped.</p>
</form></div>"""
    return layout(settings, "Checkout · " + settings["name"], body)


def render_order(settings, order_id, name):
    body = """<div class="panel" style="text-align:center"><div class="ok">✅</div>
<h2 class="sec">Thank you, {name}!</h2><p>Order <b>#{oid}</b> is confirmed. You pay on delivery.</p>
<p class="muted">Demo shop: nothing will actually be shipped.</p>
<p><a href="/"><button class="btn big">Keep shopping</button></a></p></div>
<script>localStorage.removeItem(KEY);</script>""".format(name=esc(name), oid=esc(order_id))
    return layout(settings, "Order confirmed · " + settings["name"], body)


STATIC_TYPES = {".jpg": "image/jpeg", ".png": "image/png", ".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml"}


def make_handler(settings, products):
    settings["_products"] = products
    by_id = {int(p["id"]): p for p in products}
    static_root = (BASE / "static").resolve()

    class Handler(BaseHTTPRequestHandler):
        def send(self, status, body, content_type):
            data = body.encode() if isinstance(body, str) else body
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            if content_type.startswith("image/"):
                self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

        def not_found(self):
            self.send(404, json.dumps({"error": "not found"}), "application/json")

        def do_GET(self):
            url = urllib.parse.urlsplit(self.path)
            path, query = url.path, urllib.parse.parse_qs(url.query)
            if path == "/":
                page = render_home(settings, products, query.get("category", [""])[0][:40], query.get("q", [""])[0][:80])
                self.send(200, page, "text/html; charset=utf-8")
            elif path.startswith("/product/") and path[9:].isdigit() and int(path[9:]) in by_id:
                self.send(200, render_product(settings, by_id[int(path[9:])]), "text/html; charset=utf-8")
            elif path == "/cart":
                self.send(200, render_cart(settings, products), "text/html; charset=utf-8")
            elif path == "/checkout":
                self.send(200, render_checkout(settings), "text/html; charset=utf-8")
            elif path == "/health":
                self.send(200, json.dumps({"status": "ok", "env": settings["env"]}), "application/json")
            elif path == "/api/products":
                self.send(200, json.dumps(products), "application/json")
            elif path.startswith("/static/"):
                target = (static_root / urllib.parse.unquote(path[8:])).resolve()
                kind = STATIC_TYPES.get(target.suffix.lower())
                if kind and target.is_relative_to(static_root) and target.is_file():
                    self.send(200, target.read_bytes(), kind)
                else:
                    self.not_found()
            else:
                self.not_found()

        do_HEAD = do_GET

        def do_POST(self):
            if self.path != "/checkout":
                return self.not_found()
            length = min(int(self.headers.get("Content-Length") or 0), 10000)
            form = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
            name = form.get("name", [""])[0].strip()[:80] or "friend"
            order_id = "SN{}".format(secrets.randbelow(900000) + 100000)
            # The order only goes to the log: this is a demo shop.
            print("ORDER {} items={}".format(order_id, form.get("items", ["{}"])[0][:200]), flush=True)
            self.send(200, render_order(settings, order_id, name), "text/html; charset=utf-8")

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
