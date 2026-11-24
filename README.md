# ShopNow

The online shop Sara puts online in the Cloud & DevOps sessions. It's one Python file with
nothing to install, so it runs on any Linux server, including your lab server.

```bash
python3 app.py                        # ShopNow (development) listening on 127.0.0.1:8000
curl http://127.0.0.1:8000/health     # {"status": "ok", "env": "development"}
```

| Path | Returns |
|---|---|
| `/` | the shop page |
| `/health` | `{"status": "ok"}`, for health checks and deploy scripts |
| `/api/products` | the products as JSON |

Settings are in `config.yml`. These environment variables win over it: `SHOP_HOST`,
`SHOP_PORT`, `SHOP_ENV` (`development` shows an orange banner, `production` hides it) and
`SHOP_CONFIG`. Each request is logged on one line, such as `GET /health 200`.

`deploy/` holds the files from the slides: `shop.service` (systemd), `nginx-shop.conf`
(reverse proxy) and `deploy.sh`. Tests: `python3 -m unittest discover tests`.

## Deploy it on your practice server (Session 1)

The slides walk through this with Sara. Run step 1 on your laptop, in the folder holding your
key (`student07.key`) and `shopnow.zip` (from the session site), and the rest on the server
(`ssh -i student07.key sara@session1.nateg-issatso.live -p 2307`). Replace `07` with your number.

1. **Upload it:** `scp -P 2307 -i student07.key shopnow.zip sara@session1.nateg-issatso.live:~`
   (scp takes a capital `-P` for the port), then on the server `unzip shopnow.zip`.
2. **Put it in place:** `sudo cp -r ~/shopnow /opt/shop`, then lock the config, which holds
   secrets: `sudo chmod 600 /opt/shop/config.yml`.
3. **Run it:** `python3 /opt/shop/app.py` fails with `PermissionError`. `ls -l` shows why;
   `sudo chown -R sara /opt/shop` fixes it.
4. **Keep it running:** `sudo cp /opt/shop/deploy/shop.service /etc/systemd/system/`,
   `sudo systemctl daemon-reload`, `sudo systemctl enable --now shop`,
   then `curl 127.0.0.1:8000/health` and `journalctl -u shop -n 5`.
5. **Put nginx in front** (`sudo apt install -y nginx` first):
   ```bash
   sudo cp /opt/shop/deploy/nginx-shop.conf /etc/nginx/sites-available/shop
   sudo ln -s ../sites-available/shop /etc/nginx/sites-enabled/
   sudo rm /etc/nginx/sites-enabled/default
   sudo nginx -t && sudo systemctl reload nginx
   ```
   Open `http://session1.nateg-issatso.live:2407`: that's your shop, on the internet.
6. **Redeploy:** `/opt/shop/deploy/deploy.sh` restarts it and checks `/health`.

## Later sessions

- **Session 2:** put it in a Docker image (`SHOP_HOST=0.0.0.0` inside a container).
- **Session 3:** run it on a cloud VM behind nginx.
- **Session 4:** run the tests and the deploy in a CI/CD pipeline.
