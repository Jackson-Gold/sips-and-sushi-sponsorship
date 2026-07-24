# Sips and Sushi — Event Site

Chic, garden-themed static site for the August 22 NYC event. Deploy to **Vercel** with this folder as the project root.

## Pages

| File | Purpose |
|------|---------|
| `index.html` | Landing — brand hero, Request invite CTA |
| `evening.html` | The evening — rooftop, cocktails, sushi |
| `invite.html` | Sliding puzzle → guest invite form |
| `sponsors.html` | Sponsor / outreach form (no puzzle) |

## Local preview

```bash
cd event-site
python3 -m http.server 5173
```

Open http://localhost:5173

## Web3Forms (email you on submit)

1. Create a free access key at [web3forms.com](https://web3forms.com). The inbox is set there — it is not shown on the site.
2. Copy the example config and add your key locally:

```bash
cp js/form-config.example.js js/form-config.js
```

```js
window.SIPS_FORM_CONFIG = {
  accessKey: "your-real-key",
};
```

`js/form-config.js` is **gitignored** and will not be pushed.

3. For Vercel, add the same file in the project (or inject `accessKey` at deploy) so production can submit. Guest and sponsor forms use different subjects so you can tell them apart.

Until a real key is set, the UI shows a clear “not configured” message instead of failing silently.

## Vercel deploy

1. Import this GitHub repo in Vercel.
2. Deploy from branch **`main`**.
3. Framework Preset: **Other** (or leave default).
4. Root Directory can stay **empty / repo root** — `npm run build` copies this folder into `public/` for Vercel.

Optional: set Root Directory to `event-site` instead (also supported).

The sponsorship outreach dashboard (GitHub Pages) lives on the `outreach-dashboard` branch separately.

## Stack

- Static HTML / CSS / JS
- [anime.js](https://animejs.com/) (CDN) for hero + scroll reveals + puzzle unlock
- Vanilla 3×3 sliding puzzle (`js/puzzle.js`)
- Web3Forms for inbox delivery

The sponsorship outreach dashboard in `/docs` is unchanged and still deploys via GitHub Pages.
