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

## Practice on your lab server (Session 1)

Run these from your laptop, in the folder holding your key (`student07.key`) and the unzipped `shopnow`
folder. Replace `07` with your server number.

1. **Upload it** (scp takes a capital `-P` for the port):
   `scp -P 2207 -i student07.key -r shopnow lab@session1.nateg-issatso.live:~`
2. **Run it** on the server: `cd shopnow && python3 app.py &`, then `curl http://127.0.0.1:8000/health`.
3. **Read its log**: each `curl` prints a line in the terminal where the app runs.
4. **Break the permissions**: `chmod 000 config.yml`, restart the app, read the error, and fix it
   with `chmod 600 config.yml`.
5. **Change an environment variable**: `SHOP_ENV=production python3 app.py &`, then
   `curl -s http://127.0.0.1:8000/ | grep mode`. The banner is gone.
6. **Stop it**: `kill %1`, or find its PID with `pgrep -f app.py` and `kill` it.
7. **Log out and back in**: an app started with `&` dies with your session. That's why
   `deploy/shop.service` exists.

## Later sessions

- **Session 2:** put it in a Docker image (`SHOP_HOST=0.0.0.0` inside a container).
- **Session 3:** run it on a cloud VM behind nginx.
- **Session 4:** run the tests and the deploy in a CI/CD pipeline.
