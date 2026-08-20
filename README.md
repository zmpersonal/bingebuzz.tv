# BingeBuzz.TV

Automated comedy discovery and ranking site for GitHub Pages.

## Required GitHub secret

`YOUTUBE_API_KEY`

The updater uses public read-only YouTube Data API requests. OAuth is not required.

## Setup

1. Upload everything, including `.github`.
2. GitHub → Settings → Pages → Source = GitHub Actions.
3. Set custom domain to `bingebuzz.tv`.
4. In Google Cloud, enable **YouTube Data API v3** and create an API key.
5. GitHub → Settings → Secrets and variables → Actions → New repository secret.
6. Name it exactly `YOUTUBE_API_KEY`.
7. Run `Update comedy heat feed and deploy` once.

The scheduled updater runs every 3 hours.

## Add/remove comedy sources

Edit `data/channels.json`. Modern YouTube handles are resolved automatically using `channels.list?forHandle`.

## Output data

- `data/feed.json`
- `data/videos.csv`
- `data/creators.json`
- `data/social-queue.json`

`social-queue.json` is intended for Make/Buffer/Zapier-style social automation.
