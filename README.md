# Instagram MCP for Claude

A remote [MCP](https://modelcontextprotocol.io) server that lets Claude work with your Instagram business account: read your profile, posts and insights, publish images and videos, and read and reply to DMs. It runs on Vercel and you add it to Claude as a custom connector.

The URL contains a secret token, so only people who have the full URL can use it.

Based on [jlbadano/ig-mcp](https://github.com/jlbadano/ig-mcp) (MIT), adapted to run over HTTP on Vercel.

## 1. Clone it

```bash
git clone https://github.com/tunde-alao/instagram-mcp.git
cd instagram-mcp
```

The server code lives in the `ig-mcp/` folder.

## 2. Get your environment variables

You need five values:

| Variable | What it is |
|---|---|
| `FACEBOOK_APP_ID` | Your Meta app's ID |
| `FACEBOOK_APP_SECRET` | Your Meta app's secret |
| `INSTAGRAM_ACCESS_TOKEN` | A Page access token for the Facebook Page linked to your Instagram |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Your Instagram account's numeric ID (not your @username) |
| `MCP_SECRET` | A random string you make up; it goes in the connector URL |

**Before you start:** your Instagram account must be a professional account (Business or Creator) and linked to a Facebook Page. You can switch and link it in the Instagram app's settings.

### Create the Meta app

1. Go to [developers.facebook.com](https://developers.facebook.com) and sign up as a developer with your Facebook account.
2. Click **My Apps → Create App**.
3. When asked what you want your app to do, choose **Other**.
4. For the app type, choose **Business**.
5. Finish creating the app, then add the **Instagram** product from the app dashboard.
6. Go to **App settings → Basic** and copy the **App ID** (`FACEBOOK_APP_ID`) and **App Secret** (`FACEBOOK_APP_SECRET`).

Leave the app in **Development** mode. In Development mode, anyone with a role on the app (you, as its creator) can use every permission on their own accounts, so you don't need Meta's App Review.

### Get the access token and account ID

1. Open the [Graph API Explorer](https://developers.facebook.com/tools/explorer/) and select your app.
2. Make sure **User or Page** is set to **User Token**.
3. Add these permissions:
   `pages_show_list`, `pages_read_engagement`, `business_management`, `instagram_basic`, `instagram_manage_insights`, `instagram_content_publish`, `instagram_manage_comments`, `instagram_manage_messages`
4. Click **Generate Access Token**. In the popup, select your Facebook Page and Instagram account.
5. Paste the token into the [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/) and click **Extend Access Token**. Copy the long-lived token.
6. Back in the Graph API Explorer, paste the long-lived token into the token field and run:
   ```
   me/accounts?fields=name,access_token,instagram_business_account
   ```
7. From the entry for your Page, copy:
   - `access_token`: this is your `INSTAGRAM_ACCESS_TOKEN`. A Page token created from a long-lived user token doesn't expire.
   - `instagram_business_account.id`: this is your `INSTAGRAM_BUSINESS_ACCOUNT_ID`.
   - `id`: your Facebook Page ID. It isn't an environment variable, but you'll need it for the DM tools.

Meta still limits data access to 90 days. When it lapses, repeat these steps and update the token.

### Make an MCP secret

```bash
openssl rand -hex 32
```

Use the output as `MCP_SECRET`. Never commit any of these values; `.env` files are gitignored.

## 3. Deploy to Vercel

1. Push your clone to your own GitHub account and import it at [vercel.com/new](https://vercel.com/new).
2. Set **Root Directory** to `ig-mcp`.
3. Add the five environment variables from step 2.
4. Deploy. Your server URL is:
   ```
   https://<your-project>.vercel.app/<MCP_SECRET>/mcp
   ```

If you change an environment variable later, redeploy for it to take effect.

## 4. Add the connector to Claude

1. On [claude.ai](https://claude.ai), go to **Settings → Connectors → Add custom connector**.
2. Give it a name (for example "Instagram") and paste your server URL from step 3. Leave the OAuth fields empty.
3. Click **Add**.
4. In a chat, turn on the connector from the tools menu and try: *"Show my Instagram profile info."*

Tips:

- For DMs, include your Facebook Page ID: *"List my Instagram DMs using page_id 1234567890."*
- `publish_media` and `send_dm` really post and send messages, so read Claude's approval prompt before allowing them.
- Treat the URL like a password. If it leaks, change `MCP_SECRET` in Vercel, redeploy, and update the connector.
