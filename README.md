# BingeBuzz.TV

Automated comedy + U.S. viral-video discovery and ranking site for GitHub Pages.

## What this build adds

- Preserves the black/red/gold BingeBuzz visual system and source-platform player.
- Expands the comedy source universe from 16 configured channels to 36.
- Adds YouTube `mostPopular` ingestion for `regionCode=US` to power **Viral USA**.
- Adds **BingeBuzz Funniest 25** and **BingeBuzz Viral 25** weekly charts.
- Adds Buzz, Laugh Signal, Breakout Signal and rank-movement data.
- Adds **Defend #1** and a continuous **Laugh Battle** experience.
- Rebuilds individual clip pages around ranking context, one-tap takes, challenges and sharing.
- Adds creator-status/achievement pages.
- Generates branded 1200×630 Open Graph PNGs for chart, creator and video pages.
- Replaces the old generic social queue with a **shareworthiness/social-opportunity queue**.

## Required GitHub secret

`YOUTUBE_API_KEY`

The updater uses public read-only YouTube Data API requests. OAuth is not required.

## Deploy

1. Upload the contents of this folder over the repository root, including `.github`.
2. GitHub → Settings → Pages → Source = GitHub Actions.
3. Keep custom domain set to `bingebuzz.tv`.
4. Confirm `YOUTUBE_API_KEY` exists under GitHub → Settings → Secrets and variables → Actions.
5. Run **Update BingeBuzz feeds and deploy** once.

The scheduled updater runs every 3 hours.

## Important static-site note

The current site remains GitHub Pages/static. One-tap reactions and Laugh Battle choices are stored locally in each visitor's browser and are not presented as fake global vote totals. A true global Laugh Score would require a small server-side vote endpoint (Cloudflare Worker/D1, Supabase, Firebase, etc.). The redesign is structured so that layer can be added later without changing the visual experience.

## Add/remove comedy sources

Edit `data/channels.json`. Handles that fail to resolve are skipped rather than breaking the feed, provided enough sources resolve to keep the site useful.

## Output data

- `data/feed.json`
- `data/videos.csv`
- `data/creators.json`
- `data/social-queue.json`
- `assets/social/*.png`

`social-queue.json` now prioritizes events with a reason to post—top ranks, large jumps, breakout signals, etc.—instead of blindly queueing the top 20 clips.
