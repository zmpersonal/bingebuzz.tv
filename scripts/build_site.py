
from pathlib import Path
import json,csv,re,html,math
from datetime import datetime,timezone,date
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
D=json.load(open(ROOT/'data/feed.json'))
VIDEOS=D.get('videos',[])
CREATORS=json.load(open(ROOT/'data/creators.json')) if (ROOT/'data/creators.json').exists() else []
CHANNELS=json.load(open(ROOT/'data/channels.json'))['channels']
BASE='https://bingebuzz.tv'

def esc(s): return html.escape(str(s or ''),quote=True)
def slug(s):
    s=re.sub(r'[^a-z0-9]+','-',str(s).lower()).strip('-')
    return s or 'creator'
def human(n):
    n=int(n or 0)
    if n>=1_000_000: return f'{n/1_000_000:.1f}M'
    if n>=1_000: return f'{n/1_000:.1f}K'
    return str(n)
def age_label(iso):
    try:
      d=datetime.fromisoformat(iso.replace('Z','+00:00'))
      h=max(0,(datetime.now(timezone.utc)-d).total_seconds()/3600)
      if h<24:return f'{int(h)}h ago'
      if h<24*30:return f'{int(h/24)}d ago'
      return d.strftime('%b %d, %Y').replace(' 0',' ')
    except:return ''
def head(title,desc,path='/',image=''):
    can=BASE+path
    im=image or BASE+'/assets/social-default.svg'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(can)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(can)}"><meta property="og:image" content="{esc(im)}"><meta name="twitter:card" content="summary_large_image"><link rel="stylesheet" href="/assets/style.css"></head><body>'''
NAV='''<div class="ticker"><div class="wrap">LIVE COMEDY RANKINGS • UPDATED THROUGHOUT THE DAY • SOURCE-ATTRIBUTED VIDEO DISCOVERY</div></div><header><div class="wrap nav"><a class="brand" href="/"><span class="live-dot"></span>BINGE<b>BUZZ</b></a><nav><a href="/trending/">Trending</a><a href="/standup/">Stand-Up</a><a href="/podcasts/">Podcasts</a><a href="/rising/">Rising</a><a href="/charts/bingebuzz-100/">BingeBuzz 100</a><a class="nav-cta" href="/battle/">Laugh Battle</a></nav><button class="menu">Menu</button></div></header>'''
TABS='''<div class="wrap tabs"><a class="tab hot" href="/trending/">🔥 Trending</a><a class="tab" href="/today/">Just Dropped</a><a class="tab" href="/standup/">Stand-Up</a><a class="tab" href="/podcasts/">Podcasts</a><a class="tab" href="/crowdwork/">Crowd Work</a><a class="tab" href="/shorts/">Shorts</a><a class="tab" href="/sketch/">Sketch</a><a class="tab" href="/rising/">Rising Creators</a></div>'''
FOOT='''<footer><div class="wrap"><div class="foot"><div><h3>BingeBuzz.TV</h3><p>Comedy discovery powered by public source metadata and BingeBuzz ranking signals. Videos play from their original platforms; BingeBuzz does not rehost creator video files.</p></div><div><h4>Discover</h4><a href="/trending/">Trending</a><a href="/today/">Just Dropped</a><a href="/charts/bingebuzz-100/">BingeBuzz 100</a><a href="/battle/">Laugh Battle</a></div><div><h4>About</h4><a href="/methodology/">Buzz Score methodology</a><a href="/sources/">Sources & attribution</a><a href="/api-setup/">API setup</a><a href="/data/videos.csv">Download feed data</a></div></div><div class="copy"><span>© 2026 BingeBuzz.TV</span><span>Original rankings • Source-platform embeds</span></div></div></footer><script src="/assets/site.js"></script></body></html>'''

def card(v):
    return f'''<a class="card" href="/videos/{esc(v['video_id'])}/"><div class="thumb"><img loading="lazy" src="{esc(v.get('thumbnail'))}" alt=""><span class="badge">{esc(v.get('category','comedy'))}</span><span class="buzzbadge">{int(round(v.get('buzz_score',0)))}</span></div><div class="card-body"><h3>{esc(v['title'])}</h3><div class="creator">{esc(v.get('creator'))}</div><div class="statsline"><span>{human(v.get('views'))} views</span><span>{human(v.get('likes'))} likes</span><span>{age_label(v.get('published_at',''))}</span></div></div></a>'''
def grid(vs,n=12):
    if not vs:return '<div class="empty"><strong>Feed warming up.</strong>Run the GitHub update workflow once after adding the YouTube API key.</div>'
    return '<div class="grid">'+''.join(card(v) for v in vs[:n])+'</div>'
def section(title,sub,vs,link=''):
    more=f'<a href="{link}">View all →</a>' if link else ''
    return f'<section class="section"><div class="wrap"><div class="section-head"><div><h2>{esc(title)}</h2><p>{esc(sub)}</p></div>{more}</div>{grid(vs)}</div></section>'
def sorted_by_buzz(vs): return sorted(vs,key=lambda x:(x.get('buzz_score',0),x.get('views',0)),reverse=True)

fresh=[v for v in VIDEOS if v.get('age_hours',9999)<=24]
trend=sorted_by_buzz([v for v in VIDEOS if v.get('age_hours',9999)<=24*21])
if not trend:trend=sorted_by_buzz(VIDEOS)
cats=defaultdict(list)
for v in VIDEOS: cats[v.get('category','standup')].append(v)
for k in cats:cats[k]=sorted_by_buzz(cats[k])

def featured(vs):
    if not vs:return '<div class="empty"><strong>No live videos yet.</strong>Add <code>YOUTUBE_API_KEY</code> and run the update workflow.</div>'
    lead=vs[0]; rest=vs[1:5]
    minis=''.join(f'''<a class="mini" href="/videos/{esc(v['video_id'])}/"><img src="{esc(v.get('thumbnail'))}" alt=""><div><span class="buzz">BUZZ {int(round(v.get('buzz_score',0)))}</span><h3>{esc(v['title'])}</h3><div class="creator">{esc(v.get('creator'))}</div></div></a>''' for v in rest)
    return f'''<div class="feature"><a class="video-hero" href="/videos/{esc(lead['video_id'])}/"><img src="{esc(lead.get('thumbnail'))}" alt=""><span class="score">{int(round(lead.get('buzz_score',0)))}</span><div class="overlay"><span class="rank">#1 RIGHT NOW • {esc(lead.get('category','COMEDY')).upper()}</span><h2>{esc(lead['title'])}</h2><div class="meta"><span>{esc(lead.get('creator'))}</span><span>{human(lead.get('views'))} views</span><span>{age_label(lead.get('published_at',''))}</span></div><span class="play">▶ Watch from source</span></div></a><div class="side-stack">{minis}</div></div>'''

updated=D.get('meta',{}).get('generated') or 'awaiting first live refresh'
home=head('BingeBuzz.TV | What’s Funny Right Now','Live comedy discovery: trending stand-up, comedy podcasts, crowd work, shorts and rising creators ranked by the BingeBuzz Buzz Score.')+NAV+f'''
<section class="hero"><div class="wrap hero-grid"><div><div class="kicker">Live comedy heat index</div><h1>What’s <em>funny</em><br>right now?</h1></div><div><p class="hero-copy"><strong>BingeBuzz watches the comedy internet so you don’t have to.</strong> Original source videos, ranked using velocity, engagement, reach and freshness—not an editor pretending to know what you should laugh at.</p><div class="pulse"><div><b>{len(VIDEOS)}</b><span>clips indexed</span></div><div><b>{len(CREATORS)}</b><span>creators tracked</span></div></div></div></div></section>'''+TABS+f'<section class="section"><div class="wrap"><div class="section-head"><div><h2>🔥 Blowing Up Now</h2><p>Buzz Score recalculated from live public signals. Updated {esc(updated)}.</p></div><a href="/methodology/">How scoring works →</a></div>{featured(trend)}</div></section>'
home+=section('Just Dropped','Fresh uploads from tracked comedy sources.',sorted(fresh,key=lambda x:x.get('published_at',''),reverse=True),'/today/')
home+=section('Stand-Up Heat','Sets, specials, stage clips and live comedy.',cats['standup'],'/standup/')
home+=section('Podcast Chaos','Comedy podcast clips and episodes getting traction.',cats['podcast'],'/podcasts/')
home+=section('Crowd Work','Comics doing dangerous things with microphones and strangers.',cats['crowdwork'],'/crowdwork/')
home+=section('Short Attention Span','Short-form comedy and compact destruction.',cats['shorts'],'/shorts/')
home+=FOOT
(ROOT/'index.html').write_text(home)

page_defs={
 'trending':('Trending Comedy','The hottest comedy clips in the BingeBuzz index right now.',trend),
 'today':('Just Dropped','Comedy uploads published in the last 24 hours.',sorted(fresh,key=lambda x:x.get('published_at',''),reverse=True)),
 'standup':('Stand-Up','Stand-up sets, stage clips and specials.',cats['standup']),
 'podcasts':('Comedy Podcasts','Comedy podcast clips and episodes.',cats['podcast']),
 'crowdwork':('Crowd Work','Crowd work clips ranked by live Buzz Score.',cats['crowdwork']),
 'shorts':('Comedy Shorts','Short-form comedy from tracked sources.',cats['shorts']),
 'sketch':('Sketch Comedy','Sketches and scripted comedy clips.',cats['sketch'])
}
for pg,(title,desc,vs) in page_defs.items():
    body=head(f'{title} | BingeBuzz.TV',desc,f'/{pg}/')+NAV+TABS+f'<section class="subhero"><div class="wrap"><div class="kicker">BingeBuzz live feed</div><h1>{esc(title)}</h1><p>{esc(desc)}</p></div></section>'+section(title,f'{len(vs)} indexed clips',vs)+FOOT
    (ROOT/pg/'index.html').write_text(body)

for c in CREATORS:
    cslug=slug(c.get('creator')); d=ROOT/'creators'/cslug;d.mkdir(parents=True,exist_ok=True)
    cv=sorted_by_buzz([v for v in VIDEOS if v.get('creator')==c.get('creator')])
    body=head(f"{c.get('creator')} | BingeBuzz Creator Profile",f"Live BingeBuzz ranking and recent comedy clips for {c.get('creator')}.",f"/creators/{cslug}/",cv[0].get('thumbnail') if cv else '')+NAV+f'''<section class="subhero"><div class="wrap"><div class="kicker">Creator profile</div><h1>{esc(c.get('creator'))}</h1><p>Current creator Buzz: <strong>{int(round(c.get('creator_buzz',0)))}</strong> • {human(c.get('recent_views',0))} indexed recent views • {len(cv)} clips tracked.</p></div></section>'''+section('Latest heat','Ranked by current Buzz Score.',cv)+FOOT
    (d/'index.html').write_text(body)

rising=sorted(CREATORS,key=lambda c:(c.get('momentum_score',0),c.get('creator_buzz',0)),reverse=True)
rows=''.join(f'''<a class="chart-row" href="/creators/{slug(c.get('creator'))}/"><span class="num">{i}</span><div><h3>{esc(c.get('creator'))}</h3><small>{c.get('clip_count',0)} recent clips</small></div><strong>{int(round(c.get('creator_buzz',0)))}</strong><span>{human(c.get('recent_views',0))} views</span><span class="chip">↑ {int(round(c.get('momentum_score',0)))}</span></a>''' for i,c in enumerate(rising[:100],1))
body=head('Rising Comedy Creators | BingeBuzz.TV','Comedy creators and channels currently outperforming their recent BingeBuzz baseline.','/rising/')+NAV+'''<section class="subhero"><div class="wrap"><div class="kicker">Momentum chart</div><h1>Rising creators.</h1><p>Creators with the strongest recent clip momentum across the BingeBuzz source universe.</p></div></section>'''+f'<section class="section"><div class="wrap"><div class="chart">{rows or "<div class=empty><strong>Chart warming up.</strong>Run the update workflow once.</div>"}</div></div></section>'+FOOT
(ROOT/'rising/index.html').write_text(body)

bb100=sorted(CREATORS,key=lambda c:(c.get('creator_buzz',0),c.get('recent_views',0)),reverse=True)[:100]
rows=''.join(f'''<a class="chart-row" href="/creators/{slug(c.get('creator'))}/"><span class="num">{i}</span><div><h3>{esc(c.get('creator'))}</h3><small>{c.get('clip_count',0)} clips in current window</small></div><strong>{int(round(c.get('creator_buzz',0)))}</strong><span>{human(c.get('recent_views',0))} views</span><span class="chip">BUZZ</span></a>''' for i,c in enumerate(bb100,1))
body=head('BingeBuzz 100 | Comedy Creator Chart','The BingeBuzz 100 ranks comedy creators and channels using current video performance signals.','/charts/bingebuzz-100/')+NAV+'''<section class="subhero"><div class="wrap"><div class="kicker">Updated automatically</div><h1>BingeBuzz 100.</h1><p>The comedy creators and channels generating the most heat across the BingeBuzz index.</p></div></section>'''+f'<section class="section"><div class="wrap"><div class="chart">{rows or "<div class=empty><strong>Chart warming up.</strong>Run the update workflow once.</div>"}</div></div></section>'+FOOT
(ROOT/'charts/bingebuzz-100/index.html').write_text(body)

for v in VIDEOS:
    d=ROOT/'videos'/v['video_id'];d.mkdir(parents=True,exist_ok=True)
    url=f'{BASE}/videos/{v["video_id"]}/'
    desc=f"{v.get('creator')} — {v.get('title')}. Buzz Score {int(round(v.get('buzz_score',0)))}. Embedded from the original YouTube source."
    body=head(f"{v['title']} | BingeBuzz.TV",desc,f"/videos/{v['video_id']}/",v.get('thumbnail',''))+NAV+f'''<main class="wrap video-page"><section><div class="player" data-embed="{esc(v['video_id'])}" style="cursor:pointer;background:url('{esc(v.get('thumbnail'))}') center/cover"><button class="play" style="position:relative;margin:24px">▶ Play original video</button></div><div class="share-row"><button class="share" data-share="{esc(url)}" data-title="{esc(v['title'])}">Share clip</button><a class="share" href="{esc(v.get('youtube_url'))}" rel="noopener" target="_blank">Open on YouTube ↗</a></div></section><aside class="video-info"><div class="kicker">{esc(v.get('category','comedy'))} • Buzz {int(round(v.get('buzz_score',0)))}</div><h1>{esc(v['title'])}</h1><div class="meta"><span>{human(v.get('views'))} views</span><span>{human(v.get('likes'))} likes</span><span>{age_label(v.get('published_at',''))}</span></div><div class="creator-panel" style="margin-top:25px"><b>{esc(v.get('creator'))}</b><p>BingeBuzz indexes public YouTube metadata and plays this video from its original source. Views and engagement remain with the creator/platform.</p><a class="play" href="/creators/{slug(v.get('creator'))}/">Creator profile →</a></div></aside></main>'''+FOOT
    (d/'index.html').write_text(body)

battle=trend[:2]
if len(battle)>=2:
    chunks=[]
    for i,v in enumerate(battle):
        chunks.append(f'''<div class="battle-card" data-id="{v['video_id']}"><a href="/videos/{v['video_id']}/"><img src="{esc(v.get('thumbnail'))}" alt=""></a><div class="battle-body"><div class="kicker">Buzz {int(round(v.get('buzz_score',0)))}</div><h2>{esc(v['title'])}</h2><p>{esc(v.get('creator'))}</p><button class="vote">😂 This one wins</button></div></div>''')
        if i==0: chunks.append('<div class="vs">VS</div>')
    battlehtml='<div class="battle" data-battle>'+''.join(chunks)+'</div>'
else:battlehtml='<div class="empty"><strong>Battle warming up.</strong>Run the live feed updater to load contenders.</div>'
body=head('Laugh Battle | BingeBuzz.TV','Pick the funnier of two trending comedy clips and share your choice.','/battle/')+NAV+'''<section class="subhero"><div class="wrap"><div class="kicker">Head to head</div><h1>Laugh Battle.</h1><p>Two hot clips enter. Your browser remembers your pick. No login, no fake global vote count.</p></div></section>'''+f'<section class="section"><div class="wrap">{battlehtml}</div></section>'+FOOT
(ROOT/'battle/index.html').write_text(body)

method=head('Buzz Score Methodology | BingeBuzz.TV','How the BingeBuzz Buzz Score ranks comedy clips using public YouTube performance signals.','/methodology/')+NAV+'''<section class="subhero"><div class="wrap"><div class="kicker">Transparent ranking</div><h1>How Buzz Score works.</h1><p>A discovery score, not a scientific measurement of funny.</p></div></section><section class="section"><div class="wrap content"><h2>Signals</h2><p>For recent videos, BingeBuzz combines four public performance signals: view velocity since upload, change in views since our prior snapshot, like-to-view engagement, and total reach. Freshness is used as a smaller decay factor so a new clip can compete with an older hit.</p><div class="callout"><strong>Buzz Score is relative.</strong>The score is normalized against other recent videos in the tracked comedy source universe. A 90 means a clip is unusually hot inside this dataset, not that 90% of viewers found it funny.</div><h2>Format caveat</h2><p>YouTube changed Shorts view counting in 2025. Shorts therefore are not perfectly comparable with long-form video. BingeBuzz keeps dedicated Shorts views and categories so users can browse formats separately.</p><h2>Creator charts</h2><p>The BingeBuzz 100 aggregates recent clip performance by creator/channel. Rising rankings emphasize current momentum rather than lifetime popularity.</p><h2>Source integrity</h2><p>BingeBuzz stores metadata and rankings, not copies of creator videos. Playback uses the original YouTube embed, and every clip page links back to the original source.</p></div></section>'''+FOOT
(ROOT/'methodology/index.html').write_text(method)

source_rows=''.join(f'<div class="chart-row"><span class="num">{i}</span><div><h3>{esc(c["label"])}</h3><small>{esc(c["handle"])}</small></div><strong>{esc(c["default_category"])}</strong><span></span><span class="chip">TRACKED</span></div>' for i,c in enumerate(CHANNELS,1))
src=head('Comedy Sources | BingeBuzz.TV','The source channels tracked by BingeBuzz for automated comedy discovery.','/sources/')+NAV+'''<section class="subhero"><div class="wrap"><div class="kicker">Source universe</div><h1>Who we watch.</h1><p>BingeBuzz tracks official comedy channels and creator accounts, then ranks their public videos without rehosting them.</p></div></section>'''+f'<section class="section"><div class="wrap"><div class="chart">{source_rows}</div><div class="content"><h2>Add more sources</h2><p>Edit <code>data/channels.json</code> in the repository. The updater resolves modern YouTube handles automatically using the YouTube Data API.</p></div></div></section>'+FOOT
(ROOT/'sources/index.html').write_text(src)

api=head('YouTube API Setup | BingeBuzz.TV','How to connect the free YouTube Data API key used by the BingeBuzz GitHub Actions updater.','/api-setup/')+NAV+'''<section class="subhero"><div class="wrap"><div class="kicker">One required secret</div><h1>Connect YouTube.</h1><p>BingeBuzz uses a YouTube Data API key from Google Cloud to refresh public channel/video metadata. OAuth is not required for the public read-only workflow used here.</p></div></section><section class="section"><div class="wrap content"><h2>1. Create or select a Google Cloud project</h2><p>Open Google Cloud Console, create a project (or select an existing one), then open the API Library.</p><h2>2. Enable YouTube Data API v3</h2><p>Search the API Library for <strong>YouTube Data API v3</strong> and click Enable.</p><h2>3. Create an API key</h2><p>Go to <strong>APIs & Services → Credentials → Create credentials → API key</strong>. This site only performs public read requests from GitHub Actions.</p><h2>4. Add the GitHub secret</h2><p>In the BingeBuzz repository go to <strong>Settings → Secrets and variables → Actions → New repository secret</strong>.</p><div class="callout"><strong>Name the secret exactly:</strong><code>YOUTUBE_API_KEY</code></div><p>Paste the Google API key as the secret value, save it, then manually run <strong>Update comedy heat feed and deploy</strong> once.</p><h2>Quota design</h2><p>The updater intentionally avoids broad YouTube search queries. It resolves configured channels, reads their upload playlists, and batches video-statistics requests. This is significantly more quota-efficient than repeatedly searching YouTube.</p></div></section>'''+FOOT
(ROOT/'api-setup/index.html').write_text(api)

if VIDEOS:
    day=(D.get('meta',{}).get('generated') or '')[:10] or date.today().isoformat()
    dd=ROOT/'daily'/day;dd.mkdir(parents=True,exist_ok=True)
    bd=head(f'Top Comedy Clips — {day} | BingeBuzz.TV',f'BingeBuzz daily comedy chart for {day}.',f'/daily/{day}/')+NAV+f'''<section class="subhero"><div class="wrap"><div class="kicker">Daily archive</div><h1>{day}</h1><p>The top BingeBuzz comedy clips captured for this day.</p></div></section>'''+section('Daily Top 20','Archived from the live feed.',trend[:20])+FOOT
    (dd/'index.html').write_text(bd)

redirects={'stand-up':'/standup/','standup-newbies':'/rising/','comedy-podcasts':'/podcasts/','top-stand-up':'/trending/','legends':'/charts/bingebuzz-100/'}
for old,target in redirects.items():
    p=ROOT/old;p.mkdir(parents=True,exist_ok=True)
    (p/'index.html').write_text(f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={target}"><link rel="canonical" href="{BASE+target}"><title>Moved | BingeBuzz.TV</title><a href="{target}">Continue</a>')

rssitems=''.join(f'''<item><title>{esc(v['title'])}</title><link>{BASE}/videos/{v['video_id']}/</link><guid>{BASE}/videos/{v['video_id']}/</guid><pubDate>{esc(v.get('published_at',''))}</pubDate></item>''' for v in trend[:25])
(ROOT/'feed.xml').write_text(f'''<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>BingeBuzz Trending Comedy</title><link>{BASE}</link><description>Comedy clips ranked by BingeBuzz.</description>{rssitems}</channel></rss>''')
urls=['/','/trending/','/today/','/standup/','/podcasts/','/crowdwork/','/shorts/','/sketch/','/rising/','/charts/bingebuzz-100/','/battle/','/methodology/','/sources/','/api-setup/']
urls += [f"/videos/{v['video_id']}/" for v in VIDEOS]
urls += [f"/creators/{slug(c.get('creator'))}/" for c in CREATORS]
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{BASE}{u}</loc></url>' for u in urls)+'</urlset>')
(ROOT/'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n')
(ROOT/'CNAME').write_text('bingebuzz.tv\n')
(ROOT/'404.html').write_text(head('Not Found | BingeBuzz.TV','Page not found.')+NAV+'<section class="subhero"><div class="wrap"><div class="kicker">404</div><h1>Bombed.</h1><p>That page did not survive the set.</p><a class="play" href="/">Back to the funny →</a></div></section>'+FOOT)
