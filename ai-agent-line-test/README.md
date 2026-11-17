# AI Agent LINE Test

Standalone prototype for LINE Login, LIFF, and the LINE Messaging API. The React app runs in a normal browser and inside LINE. Django verifies the LINE ID token and answers Official Account messages. There is no AI, no password login, and no database signup.

LINE credentials are never stored in the repository. Copy them from the LINE Developers console into local `.env` files and into the hosting dashboards.

## Layout

```text
ai-agent-line-test/
  frontend/          React, TypeScript, Vite, LIFF
  backend/           Django, Django REST framework, SQLite
  render.yaml        Render web service definition
```

The browser talks to LIFF and to Django. Only Django calls `https://api.line.me`.

Two LINE channels are required. They are not interchangeable:

| Variable | Channel | Used for |
| --- | --- | --- |
| `VITE_LIFF_ID` | LINE Login, LIFF tab | `liff.init()` |
| `LINE_LOGIN_CHANNEL_ID` | LINE Login, Basic settings, Channel ID | ID token `client_id` |
| `LINE_CHANNEL_SECRET` | Messaging API, Basic settings, Channel secret | Webhook signature |
| `LINE_CHANNEL_ACCESS_TOKEN` | Messaging API, Messaging API tab, Channel access token | Reply messages |

## Prerequisites

- Node.js 20 or newer and npm
- Python 3.12
- A free [LINE Developers](https://developers.line.biz/console/) account
- A free [GitHub](https://github.com/) repository
- A free [Cloudflare Pages](https://pages.cloudflare.com/) project
- A free [Render](https://render.com/) web service

Expected public URLs after deployment:

- Frontend: `https://ai-agent-line.pages.dev`
- Backend: `https://ai-agent-line-api.onrender.com`
- Webhook: `https://ai-agent-line-api.onrender.com/api/line/webhook/`
- Health: `https://ai-agent-line-api.onrender.com/api/health/`

SQLite is only for this test, mainly to remember webhook event IDs so a redelivery is not answered twice. Render's free web service disk is ephemeral. The database file is deleted when the instance restarts, spins down, or is redeployed. Do not store real users in it.

The Render free instance also sleeps after a period of inactivity. The first request after sleep can take half a minute or more. LINE may time out that first webhook and redeliver it once the process is awake.

## 1. Install frontend dependencies

From the project root:

```bash
cd frontend
npm install
cp .env.example .env
```

Leave `VITE_LIFF_ID` empty until the LIFF app exists. Keep `VITE_API_BASE_URL=http://localhost:8000` for local Django.

## 2. Install backend dependencies

From the project root, in a second terminal:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead of `source .venv/bin/activate`.

Generate a local secret and put it in `backend/.env` as `DJANGO_SECRET_KEY`. Any long random string is fine:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Leave the three `LINE_` values empty until the console steps below.

## 3. Run React locally

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

- `/` shows the title, short description, Signup, Login, and Open in LINE.
- `/signup` collects a full name and email in this browser, then starts LINE Login.
- `/login` initializes LIFF and can verify an existing LINE session.
- `/profile` redirects to `/login` until Django has verified an ID token.

Stop the dev server with Ctrl+C. Production build:

```bash
npm run build
```

The static site is written to `frontend/dist`.

## 4. Run Django locally

```bash
cd backend
source .venv/bin/activate
python manage.py runserver
```

Check the API:

```bash
curl http://127.0.0.1:8000/api/health/
```

Expected body:

```json
{"status":"success","message":"AI Agent backend is running"}
```

A verify call without a token returns 400:

```bash
curl -i -X POST http://127.0.0.1:8000/api/auth/verify/ \
  -H 'Content-Type: application/json' \
  -d '{"id_token":""}'
```

An unsigned webhook returns 400 once `LINE_CHANNEL_SECRET` is set, and 503 while that secret is still empty:

```bash
curl -i -X POST http://127.0.0.1:8000/api/line/webhook/ \
  -H 'Content-Type: application/json' \
  -d '{"events":[]}'
```

Run the automated backend tests:

```bash
python manage.py test
```

## 5. Configure a LINE Provider

1. Open [LINE Developers console](https://developers.line.biz/console/).
2. Log in with the LINE account that will own the bot.
3. Create a provider, for example `AI Agent LINE Test`.
4. Create both channels in the next two sections under this same provider.

## 6. Configure the LINE Login channel

1. In the provider, choose **Create a new channel** and then **LINE Login**.
2. Fill in the required app name, description, and email. App type: **Web app**.
3. Open the new channel. On **Basic settings**, copy **Channel ID**. That value is `LINE_LOGIN_CHANNEL_ID`. Do not use the Messaging API channel ID here.
4. Open the **LINE Login** tab.
5. Under **Callback URL**, add each URL on its own line:

```text
https://ai-agent-line.pages.dev
https://ai-agent-line.pages.dev/login
https://ai-agent-line.pages.dev/signup
http://localhost:5173
http://localhost:5173/login
http://localhost:5173/signup
```

6. Save. Under **OpenID Connect**, email permission can stay off unless you want the verified email on the profile page. The app requires the `openid` scope because it reads an ID token.

LINE Login from a desktop browser can use `http://localhost:5173` only when that callback URL is saved on this channel. The LIFF endpoint itself still has to be HTTPS. See the next section.

## 7. Create the LIFF application

1. Stay in the LINE Login channel and open the **LIFF** tab.
2. Choose **Add**.
3. Use these settings:

| Field | Value |
| --- | --- |
| LIFF app name | AI Agent LINE Test |
| Size | Full |
| Endpoint URL | `https://ai-agent-line.pages.dev` |
| Scopes | `profile`, `openid`. Add `email` only if you enabled the email permission. |
| Bot link feature | On (normal), after the Messaging API channel exists |

4. Add the app and copy the **LIFF ID**. That value is `VITE_LIFF_ID`. It looks like `1234567890-AbcdEfgh`. Put the real ID in `frontend/.env`. Do not commit that file.
5. Restart `npm run dev` after changing `frontend/.env`. Vite only reads environment variables when it starts.

`openid` is required. Without it, `liff.getIDToken()` is empty and the profile page cannot be verified.

## 8. Configure the LIFF Endpoint URL

The endpoint URL is the page LINE opens. It must be HTTPS, and it must be the same origin that calls `liff.init()`.

- Deployed app: `https://ai-agent-line.pages.dev`
- Local UI only: `http://localhost:5173` runs the screens, but a LIFF ID whose endpoint is `https://ai-agent-line.pages.dev` will not initialize on localhost.
- Local LINE login inside LIFF: expose the Vite server with an HTTPS tunnel, set the LIFF Endpoint URL to that HTTPS origin, and add the tunnel origin to the LINE Login callback URLs. Change the endpoint back to `https://ai-agent-line.pages.dev` before you rely on the public bot.

The **Open in LINE** button points at `https://liff.line.me/<LIFF ID>`.

## 9. Create the Messaging API channel

1. In the same provider, create a channel of type **Messaging API**.
2. On **Basic settings**, copy **Channel secret**. That value is `LINE_CHANNEL_SECRET`.
3. Open the **Messaging API** tab and issue a **Channel access token (long-lived)**. That value is `LINE_CHANNEL_ACCESS_TOKEN`.
4. On the same tab, turn **Auto-reply messages** off and **Greeting messages** off. LINE's built-in auto-reply would hide Django's reply.
5. Leave **Use webhook** off until the Render URL is live, then complete the next section.
6. Open the QR code on the Messaging API tab and add the Official Account as a friend from your phone. The webhook only receives messages sent to this account.

## 10. Configure the webhook URL

After the backend is deployed:

1. Messaging API tab, **Webhook URL**:

```text
https://ai-agent-line-api.onrender.com/api/line/webhook/
```

2. Choose **Verify**. LINE sends a signed request with an empty event list. Django returns HTTP 200 when `LINE_CHANNEL_SECRET` matches this Messaging API channel.
3. Enable **Use webhook**.
4. If the console shows **Webhook redelivery**, you can enable it. Django stores `webhookEventId` and skips a second reply for the same event.

Wake the free Render service first if it has been idle, then click Verify again if the first attempt times out:

```bash
curl https://ai-agent-line-api.onrender.com/api/health/
```

## 11. Configure environment variables

Frontend, `frontend/.env` locally and Cloudflare Pages at build time:

```text
VITE_LIFF_ID=
VITE_API_BASE_URL=
```

Local API base URL: `http://localhost:8000`

Deployed API base URL: `https://ai-agent-line-api.onrender.com`

Vite bakes `VITE_` variables into the static build. Changing them on Cloudflare requires a new deployment.

Backend, `backend/.env` locally and Render environment variables:

```text
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=
FRONTEND_URL=
LINE_LOGIN_CHANNEL_ID=
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
```

Local values:

```text
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
FRONTEND_URL=http://localhost:5173
```

Render values:

```text
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=ai-agent-line-api.onrender.com
FRONTEND_URL=https://ai-agent-line.pages.dev
```

`FRONTEND_URL` is the only browser origin allowed to call the API in production. Add another HTTPS origin with a comma-separated `CORS_ALLOWED_ORIGINS` value if you use a Cloudflare preview URL. Do not set `CORS_ALLOW_ALL_ORIGINS`.

Restart Django after changing `backend/.env`.

## 12. Deploy the frontend to Cloudflare Pages

1. Create a GitHub repository and push this project. From `ai-agent-line-test`:

```bash
git init
git add .
git status
git commit -m "Add LINE Login, LIFF, and Messaging API test app."
git branch -M main
git remote add origin https://github.com/<your-account>/<your-repo>.git
git push -u origin main
```

Confirm `git status` does not list `.env`, `.venv`, `node_modules`, or `db.sqlite3`.

2. In the Cloudflare dashboard, create a **Pages** project and connect that repository.
3. Use these build settings:

| Setting | Value |
| --- | --- |
| Production branch | `main` |
| Root directory | `frontend` |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Environment variable `NODE_VERSION` | `22` |
| Environment variable `VITE_LIFF_ID` | the LIFF ID from the console |
| Environment variable `VITE_API_BASE_URL` | `https://ai-agent-line-api.onrender.com` |

4. Deploy. `frontend/public/_redirects` sends unknown paths such as `/login` back to `index.html`, which React Router needs.
5. In **Custom domains**, confirm the project is served at `https://ai-agent-line.pages.dev`. If Cloudflare assigns a different `pages.dev` subdomain, use that exact origin as the LIFF Endpoint URL, the LINE Login callback URLs, `FRONTEND_URL` on Render, and then redeploy both sides.

Pages on the free plan is enough. No Cloudflare Workers plan is required.

## 13. Deploy the backend to Render

`render.yaml` describes one free Python web service. You can apply it as a Blueprint, or create the service by hand with the same commands.

Blueprint:

1. In Render, choose **New** and then **Blueprint**.
2. Connect the GitHub repository.
3. Apply `render.yaml`.
4. When Render asks for the secret values, paste `LINE_LOGIN_CHANNEL_ID`, `LINE_CHANNEL_SECRET`, and `LINE_CHANNEL_ACCESS_TOKEN`. Leave them blank in Git.
5. If `plan: free` is not available on the account, create a Web Service manually and choose the free instance type.

Manual service:

| Setting | Value |
| --- | --- |
| Root directory | `backend` |
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate` |
| Start command | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 30` |
| Health check path | `/api/health/` |
| Instance type | Free |

Set the environment variables from section 11, including a generated `DJANGO_SECRET_KEY`. Render's `render.yaml` can generate that key on the first blueprint sync.

The service name `ai-agent-line-api` produces `https://ai-agent-line-api.onrender.com` when that hostname is still available. If Render assigns a different hostname, put that host in `DJANGO_ALLOWED_HOSTS` and in `VITE_API_BASE_URL`, then redeploy.

Confirm production:

```bash
curl https://ai-agent-line-api.onrender.com/api/health/
```

Django redirects HTTP to HTTPS in production and reads `X-Forwarded-Proto` from Render. CORS allows `FRONTEND_URL` only, plus localhost while `DJANGO_DEBUG=True`.

## 14. Test LINE Login

1. Set the real `VITE_LIFF_ID` and API base URL, then rebuild or restart Vite.
2. On a phone, open the deployed site and tap **Open in LINE**, or open `https://liff.line.me/<LIFF ID>` from the LINE app.
3. Tap **Login** or submit **Signup**.
4. Approve the LINE permission screen if it appears.
5. The app reads the LINE profile and ID token in the browser, then `POST`s only the ID token to `/api/auth/verify/`.
6. Django checks the token at `https://api.line.me/oauth2/v2.1/verify` with `LINE_LOGIN_CHANNEL_ID` as `client_id`. The profile page shows the display name, user ID, picture, and status message from that verified result and from `liff.getProfile()`.
7. **Refresh Profile** repeats verification. **Logout** clears the local session and calls `liff.logout()`.
8. Open `/profile` in a private window. It returns to `/login`.

Name and email on the signup form are not sent to Django and are not an account.

## 15. Test the LINE Messaging API

1. Confirm `LINE_CHANNEL_SECRET` and `LINE_CHANNEL_ACCESS_TOKEN` are set on Render and the webhook verifies.
2. From the LINE account that added the Official Account, send `Hi`.
3. Expected reply:

```text
Hello! Welcome to AI Agent. Your LINE Messaging API integration is working successfully.
```

4. Send any other text, for example `Test`. Expected reply:

```text
Thank you for your message! Your AI Agent test bot is working.
```

5. In Render logs, a successful delivery is an HTTP 200 on `POST /api/line/webhook/`. A bad signature is HTTP 400. A missing channel secret is HTTP 503, and the event is not treated as delivered.

Stickers and other non-text events are acknowledged with HTTP 200 and no reply.

## API

`GET /api/health/`

```json
{"status":"success","message":"AI Agent backend is running"}
```

`POST /api/auth/verify/`

```json
{"id_token":"LINE_ID_TOKEN"}
```

The response `user` object is built from LINE's verification payload (`sub`, `name`, `picture`, `email`, `exp`). Extra profile fields posted by the browser are ignored.

`POST /api/line/webhook/`

LINE signs the raw body with HMAC-SHA256 and the channel secret, then sends the digest in `X-Line-Signature`. Django compares that header before it parses events. Text messages are answered with the Messaging API reply endpoint. The same `webhookEventId` is stored after a successful reply so a redelivery does not send a second message. A failed reply deletes that marker and returns a non-200 status so LINE can try again.

## Local test results to expect before LINE credentials exist

- `python manage.py test` passes without calling LINE.
- `npm run build` produces `frontend/dist`.
- Home, signup, and login render at `http://localhost:5173`.
- `/profile` redirects to `/login`.
- Login and signup show a LIFF configuration error until `VITE_LIFF_ID` is set to a real LIFF app whose endpoint matches the page origin.
