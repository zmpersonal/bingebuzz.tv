from pathlib import Path
import json, re, html, math, textwrap, unicodedata
from datetime import datetime, timezone, date
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
DATA = json.load(open(ROOT/'data/feed.json'))
VIDEOS = DATA.get('videos', [])
CREATORS = json.load(open(ROOT/'data/creators.json')) if (ROOT/'data/creators.json').exists() else []
CHANNELS = json.load(open(ROOT/'data/channels.json')).get('channels', [])
BASE = 'https://bingebuzz.tv'


def esc(s): return html.escape(str(s or ''), quote=True)
def slug(s):
    s = re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')
    return s or 'creator'
def human(n):
    n = int(n or 0)
    if n >= 1_000_000_000: return f'{n/1_000_000_000:.1f}B'
    if n >= 1_000_000: return f'{n/1_000_000:.1f}M'
    if n >= 1_000: return f'{n/1_000:.1f}K'
    return str(n)
def compact_rate(n):
    n = float(n or 0)
    if n >= 1_000_000: return f'{n/1_000_000:.1f}M/hr'
    if n >= 1_000: return f'{n/1_000:.0f}K/hr'
    return f'{int(n)}/hr'
def age_label(iso):
    try:
        d = datetime.fromisoformat(iso.replace('Z', '+00:00'))
        h = max(0, (datetime.now(timezone.utc)-d).total_seconds()/3600)
        if h < 1: return 'just now'
        if h < 24: return f'{int(h)}h ago'
        if h < 24*30: return f'{int(h/24)}d ago'
        return d.strftime('%b %d, %Y').replace(' 0', ' ')
    except Exception:
        return ''
def sorted_buzz(vs): return sorted(vs, key=lambda x:(x.get('buzz_score',0), x.get('views',0)), reverse=True)
def sorted_funny(vs): return sorted(vs, key=lambda x:(x.get('funny_score',0), x.get('buzz_score',0), x.get('views',0)), reverse=True)
def sorted_breakout(vs): return sorted(vs, key=lambda x:(x.get('breakout_score',0), x.get('snapshot_velocity') or 0), reverse=True)


def head(title, desc, path='/', image=''):
    can = BASE + path
    im = image or BASE + '/assets/social-default.png'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(can)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(can)}"><meta property="og:image" content="{esc(im)}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{esc(im)}"><link rel="stylesheet" href="/assets/style.css"></head><body>'''

NAV = '''<div class="ticker"><div class="wrap">THE INTERNET WATCHES • BINGEBUZZ KEEPS SCORE • LIVE RANKINGS UPDATED THROUGHOUT THE DAY</div></div><header><div class="wrap nav"><a class="brand" href="/"><span class="live-dot"></span>BINGE<b>BUZZ</b></a><nav><a href="/trending/">Trending</a><a href="/funniest-this-week/">Funniest 25</a><a href="/viral-usa/">Viral USA</a><a href="/charts/bingebuzz-100/">Creators</a><a class="nav-cta" href="/battle/">⚔ Laugh Battle</a></nav><button class="menu" aria-label="Open navigation">Menu</button></div></header>'''
TABS = '''<div class="wrap tabs"><a class="tab hot" href="/trending/">🔥 Trending</a><a class="tab" href="/funniest-this-week/">😂 Funniest</a><a class="tab" href="/viral-usa/">🇺🇸 Viral USA</a><a class="tab" href="/today/">Just Dropped</a><a class="tab" href="/standup/">Stand-Up</a><a class="tab" href="/podcasts/">Podcasts</a><a class="tab" href="/crowdwork/">Crowd Work</a><a class="tab" href="/shorts/">Shorts</a><a class="tab" href="/sketch/">Sketch</a></div>'''
FOOT = '''<footer><div class="wrap"><div class="foot"><div><h3>BingeBuzz.TV</h3><p>The live scoreboard for internet comedy and viral video. BingeBuzz ranks public source videos; playback stays with the original platform and creator.</p></div><div><h4>Charts</h4><a href="/trending/">Trending Now</a><a href="/funniest-this-week/">Funniest 25</a><a href="/viral-this-week/">Viral 25</a><a href="/charts/bingebuzz-100/">BingeBuzz 100</a><a href="/battle/">Laugh Battle</a></div><div><h4>About</h4><a href="/methodology/">How rankings work</a><a href="/sources/">Sources</a><a href="/api-setup/">API setup</a><a href="/data/videos.csv">Feed data</a></div></div><div class="copy"><span>© 2026 BingeBuzz.TV</span><span>The internet watches. BingeBuzz keeps score.</span></div></div></footer><script src="/assets/site.js"></script></body></html>'''

# Current chart universes
COMEDY = [v for v in VIDEOS if v.get('category') != 'viral']
FRESH = [v for v in COMEDY if v.get('age_hours',9999) <= 24]
TREND = sorted_buzz([v for v in COMEDY if v.get('age_hours',9999) <= 24*21]) or sorted_buzz(COMEDY)
FUN_WEEK = sorted_funny([v for v in COMEDY if v.get('age_hours',9999) <= 24*7])[:25]
VIRAL_WEEK = sorted_buzz([v for v in VIDEOS if v.get('viral_us') and v.get('age_hours',9999) <= 24*7])[:25]
if not VIRAL_WEEK:
    VIRAL_WEEK = sorted_buzz([v for v in VIDEOS if v.get('viral_us')])[:25]
BREAKOUT = sorted_breakout([v for v in COMEDY if v.get('age_hours',9999) <= 24*7 and v.get('views',0) < 5_000_000])[:8]
CATS = defaultdict(list)
for v in COMEDY: CATS[v.get('category','standup')].append(v)
for k in CATS: CATS[k] = sorted_buzz(CATS[k])

TREND_RANK = {v['video_id']:i for i,v in enumerate(TREND,1)}
FUN_RANK = {v['video_id']:i for i,v in enumerate(FUN_WEEK,1)}
VIRAL_RANK = {v['video_id']:i for i,v in enumerate(VIRAL_WEEK,1)}


def video_story(v):
    vid = v.get('video_id')
    if vid in FUN_RANK and FUN_RANK[vid] <= 10:
        return f'#{FUN_RANK[vid]} FUNNIEST THIS WEEK', f'LAUGH {int(round(v.get("funny_score",0)))}'
    if vid in VIRAL_RANK and VIRAL_RANK[vid] <= 10:
        return f'#{VIRAL_RANK[vid]} VIRAL IN USA', f'BUZZ {int(round(v.get("buzz_score",0)))}'
    if vid in TREND_RANK and TREND_RANK[vid] <= 10:
        return f'#{TREND_RANK[vid]} RIGHT NOW', f'BUZZ {int(round(v.get("buzz_score",0)))}'
    if v.get('breakout_score',0) >= 80:
        return 'BEFORE IT BLOWS UP', f'BREAKOUT {int(round(v.get("breakout_score",0)))}'
    return 'BINGEBUZZ RANKED', f'BUZZ {int(round(v.get("buzz_score",0)))}'


def status_line(v):
    story, score = video_story(v)
    vel = v.get('snapshot_velocity') or v.get('age_velocity') or 0
    move = int(v.get('rank_change') or 0)
    move_txt = f'<span class="move up">↑{move}</span>' if move > 0 else (f'<span class="move down">↓{abs(move)}</span>' if move < 0 else '')
    return f'''<div class="status-strip"><div><span class="status-label">{esc(story)}</span><strong>{esc(score)}</strong></div><div class="status-metrics"><span>{human(v.get('views'))} views</span><span>{compact_rate(vel)}</span>{move_txt}</div></div>'''


def card(v, rank=None, mode='standard'):
    rank_html = f'<span class="rank-number">#{rank}</span>' if rank else ''
    signal = int(round(v.get('funny_score',0))) if mode=='funny' else int(round(v.get('buzz_score',0)))
    label = 'LAUGH' if mode=='funny' else 'BUZZ'
    return f'''<a class="card" href="/videos/{esc(v['video_id'])}/"><div class="thumb"><img loading="lazy" src="{esc(v.get('thumbnail'))}" alt=""><span class="badge">{esc(v.get('category','comedy'))}</span>{rank_html}<span class="buzzbadge">{label} {signal}</span></div><div class="card-body"><h3>{esc(v['title'])}</h3><div class="creator">{esc(v.get('creator'))}</div><div class="statsline"><span>{human(v.get('views'))} views</span><span>{compact_rate(v.get('snapshot_velocity') or v.get('age_velocity'))}</span><span>{age_label(v.get('published_at',''))}</span></div></div></a>'''


def grid(vs, n=12, mode='standard', ranked=False):
    if not vs:
        return '<div class="empty"><strong>Feed warming up.</strong>Run the GitHub update workflow once after adding the YouTube API key.</div>'
    return '<div class="grid">'+''.join(card(v, i if ranked else None, mode) for i,v in enumerate(vs[:n],1))+'</div>'


def section(title, sub, vs, link='', mode='standard', ranked=False, eyebrow=''):
    more = f'<a href="{link}">View all →</a>' if link else ''
    eye = f'<div class="section-eyebrow">{esc(eyebrow)}</div>' if eyebrow else ''
    return f'<section class="section"><div class="wrap"><div class="section-head"><div>{eye}<h2>{esc(title)}</h2><p>{esc(sub)}</p></div>{more}</div>{grid(vs, mode=mode, ranked=ranked)}</div></section>'


def featured(vs):
    if not vs:
        return '<div class="empty"><strong>No live videos yet.</strong>Add <code>YOUTUBE_API_KEY</code> and run the update workflow.</div>'
    lead = vs[0]
    rest = vs[1:5]
    minis = ''.join(f'''<a class="mini" href="/videos/{esc(v['video_id'])}/"><div class="mini-rank">#{i+2}</div><img src="{esc(v.get('thumbnail'))}" alt=""><div><span class="buzz">BUZZ {int(round(v.get('buzz_score',0)))}</span><h3>{esc(v['title'])}</h3><div class="creator">{esc(v.get('creator'))}</div></div></a>''' for i,v in enumerate(rest))
    return f'''<div class="feature"><a class="video-hero" href="/videos/{esc(lead['video_id'])}/"><img src="{esc(lead.get('thumbnail'))}" alt=""><span class="score">{int(round(lead.get('buzz_score',0)))}</span><div class="overlay"><span class="rank">#1 RIGHT NOW • {esc(lead.get('category','COMEDY')).upper()}</span><h2>{esc(lead['title'])}</h2><div class="meta"><span>{esc(lead.get('creator'))}</span><span>{human(lead.get('views'))} views</span><span>{compact_rate(lead.get('snapshot_velocity') or lead.get('age_velocity'))}</span></div><span class="play">▶ Watch & judge it</span></div></a><div class="side-stack">{minis}</div></div>'''


def battle_block(a,b,compact=False):
    if not a or not b: return ''
    cls = 'battle battle-compact' if compact else 'battle'
    return f'''<div class="{cls}" data-battle-once><div class="battle-card" data-id="{esc(a['video_id'])}"><a class="battle-thumb" href="/videos/{esc(a['video_id'])}/"><img src="{esc(a.get('thumbnail'))}" alt=""><span>#{TREND_RANK.get(a['video_id'],'—')}</span></a><div class="battle-body"><div class="kicker">Buzz {int(round(a.get('buzz_score',0)))}</div><h3>{esc(a['title'])}</h3><p>{esc(a.get('creator'))}</p><button class="vote" data-battle-vote="{esc(a['video_id'])}">😂 This one wins</button></div></div><div class="vs">VS</div><div class="battle-card" data-id="{esc(b['video_id'])}"><a class="battle-thumb" href="/videos/{esc(b['video_id'])}/"><img src="{esc(b.get('thumbnail'))}" alt=""><span>#{TREND_RANK.get(b['video_id'],'—')}</span></a><div class="battle-body"><div class="kicker">Buzz {int(round(b.get('buzz_score',0)))}</div><h3>{esc(b['title'])}</h3><p>{esc(b.get('creator'))}</p><button class="vote" data-battle-vote="{esc(b['video_id'])}">😂 This one wins</button></div></div></div><div class="battle-result" data-battle-result hidden></div>'''


def chart_rows(vs, mode='funny', maxn=25):
    rows=[]
    for i,v in enumerate(vs[:maxn],1):
        value = int(round(v.get('funny_score',0))) if mode=='funny' else int(round(v.get('buzz_score',0)))
        label = 'LAUGH' if mode=='funny' else 'BUZZ'
        rows.append(f'''<a class="chart-row clip-chart" href="/videos/{esc(v['video_id'])}/"><span class="num">{i}</span><div><h3>{esc(v['title'])}</h3><small>{esc(v.get('creator'))} • {human(v.get('views'))} views</small></div><strong>{label} {value}</strong><span>{compact_rate(v.get('snapshot_velocity') or v.get('age_velocity'))}</span><span class="chip">{esc(age_label(v.get('published_at','')))}</span></a>''')
    return ''.join(rows)


def make_social_card(path, eyebrow, title, creator='', metric='', footer='BINGEBUZZ.TV'):
    def safe_text(value):
        return ''.join(ch for ch in str(value or '') if unicodedata.category(ch) not in ('So','Cs'))
    eyebrow, title, creator, metric, footer = map(safe_text, (eyebrow,title,creator,metric,footer))
    try:
        from PIL import Image, ImageDraw, ImageFont
        out = ROOT/path.lstrip('/')
        out.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new('RGB',(1200,630),(9,9,9)); d=ImageDraw.Draw(img)
        red=(255,81,56); gold=(255,211,78); white=(247,244,237); muted=(167,162,154)
        font_paths=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/dejavu/DejaVuSans.ttf']
        bold=font_paths[0]; reg=font_paths[1]
        f_brand=ImageFont.truetype(bold,34); f_eye=ImageFont.truetype(bold,28); f_title=ImageFont.truetype(bold,64); f_creator=ImageFont.truetype(reg,30); f_metric=ImageFont.truetype(bold,38); f_footer=ImageFont.truetype(bold,26)
        d.rectangle((0,0,1200,14), fill=red)
        d.text((62,52),'BINGE',font=f_brand,fill=white); w=d.textlength('BINGE',font=f_brand); d.text((62+w,52),'BUZZ',font=f_brand,fill=red)
        d.text((62,128),eyebrow.upper(),font=f_eye,fill=gold)
        words=title.split(); lines=[]; cur=''
        for word in words:
            test=(cur+' '+word).strip()
            if d.textlength(test,font=f_title)>1060 and cur:
                lines.append(cur); cur=word
            else: cur=test
        if cur: lines.append(cur)
        lines=lines[:3]
        y=184
        for line in lines:
            d.text((62,y),line,font=f_title,fill=white); y+=76
        if creator: d.text((62,min(y+6,466)),creator,font=f_creator,fill=muted)
        if metric:
            bbox=d.textbbox((0,0),metric,font=f_metric); mw=bbox[2]-bbox[0]
            d.rounded_rectangle((1200-mw-116,500,1138,572),radius=18,fill=red)
            d.text((1200-mw-90,514),metric,font=f_metric,fill=white)
        d.text((62,540),footer,font=f_footer,fill=muted)
        img.save(out,'PNG',optimize=True)
        return BASE + '/' + str(out.relative_to(ROOT)).replace('\\','/')
    except Exception:
        return BASE + '/assets/social-default.png'

# Default social image
make_social_card('/assets/social-default.png','LIVE INTERNET SCOREBOARD','WHAT\'S FUNNY RIGHT NOW?','','THE INTERNET WATCHES. WE KEEP SCORE.')

# Homepage
updated = DATA.get('meta',{}).get('generated') or 'awaiting first live refresh'
lead = TREND[0] if TREND else None
hero_player = ''
if lead:
    hero_player = f'''<a class="hero-lead" href="/videos/{esc(lead['video_id'])}/"><div class="hero-lead-thumb"><img src="{esc(lead.get('thumbnail'))}" alt=""><span class="hero-rank">#1 RIGHT NOW</span><span class="hero-play">▶</span></div><div class="hero-lead-copy"><strong>{esc(lead['title'])}</strong><span>{esc(lead.get('creator'))} • BUZZ {int(round(lead.get('buzz_score',0)))}</span></div></a>'''

home = head('BingeBuzz.TV | The Internet Watches. We Keep Score.','Live comedy and viral-video rankings. See what is blowing up, vote on what is actually funny, and discover clips before everyone else.') + NAV + f'''
<section class="hero"><div class="wrap hero-grid"><div><div class="kicker">Live internet scoreboard</div><h1>What’s <em>funny</em><br>right now?</h1><p class="hero-copy hero-copy-left">BingeBuzz tracks velocity, engagement and momentum to show <strong>what is winning right now</strong>—and what may blow up next.</p></div><div>{hero_player}<div class="pulse pulse-wide"><div><b>{int(DATA.get('meta',{}).get('videos_indexed') or len(VIDEOS))}</b><span>clips analyzed</span></div><div><b>LIVE</b><span>rankings updated all day</span></div></div></div></div></section>''' + TABS
home += f'''<section class="section"><div class="wrap"><div class="section-head"><div><div class="section-eyebrow">LIVE SCOREBOARD</div><h2>🔥 Trending Right Now</h2><p>Buzz Score recalculated from public source signals. Updated {esc(updated)}.</p></div><a href="/methodology/">How it works →</a></div>{featured(TREND)}</div></section>'''
if len(TREND)>=3:
    home += f'''<section class="section battle-section"><div class="wrap"><div class="section-head"><div><div class="section-eyebrow">YOUR VOTE</div><h2>⚔ Defend #1</h2><p>Can today’s strongest challenger take down the current leader?</p></div><a href="/battle/">More battles →</a></div>{battle_block(TREND[0], TREND[1], True)}</div></section>'''
home += section('😂 BingeBuzz Funniest 25','The weekly comedy chart weighted toward audience engagement, momentum and current heat.',FUN_WEEK,'/funniest-this-week/','funny',True,'THIS WEEK')
home += section('👀 Before It Blows Up','Smaller clips showing unusually strong acceleration before they become obvious hits.',BREAKOUT,'/rising/','standard',False,'EARLY SIGNAL')
home += section('🇺🇸 Viral in America','Videos currently appearing in YouTube’s U.S. most-popular feed, reranked by BingeBuzz momentum.',VIRAL_WEEK,'/viral-usa/','standard',True,'VIRAL USA')
home += section('Just Dropped','Fresh uploads from tracked comedy sources.',sorted(FRESH,key=lambda x:x.get('published_at',''),reverse=True),'/today/')
home += section('Stand-Up Heat','Sets, specials, stage clips and live comedy.',CATS['standup'],'/standup/')
home += section('Podcast Chaos','Comedy podcast clips and episodes getting traction.',CATS['podcast'],'/podcasts/')
home += FOOT
(ROOT/'index.html').write_text(home)

# Category pages
page_defs={
 'trending':('Trending Now','The hottest comedy clips in the BingeBuzz index right now.',TREND,'standard'),
 'today':('Just Dropped','Comedy uploads published in the last 24 hours.',sorted(FRESH,key=lambda x:x.get('published_at',''),reverse=True),'standard'),
 'standup':('Stand-Up','Stand-up sets, stage clips and specials.',CATS['standup'],'standard'),
 'podcasts':('Comedy Podcasts','Comedy podcast clips and episodes.',CATS['podcast'],'standard'),
 'crowdwork':('Crowd Work','Crowd-work clips ranked by current heat.',CATS['crowdwork'],'standard'),
 'shorts':('Comedy Shorts','Short-form comedy from tracked sources.',CATS['shorts'],'standard'),
 'sketch':('Sketch Comedy','Sketches and scripted comedy clips.',CATS['sketch'],'standard'),
}
for pg,(title,desc,vs,mode) in page_defs.items():
    d=ROOT/pg; d.mkdir(parents=True,exist_ok=True)
    body=head(f'{title} | BingeBuzz.TV',desc,f'/{pg}/')+NAV+TABS+f'''<section class="subhero"><div class="wrap"><div class="kicker">BingeBuzz live feed</div><h1>{esc(title)}</h1><p>{esc(desc)}</p></div></section>'''+section(title,f'{len(vs)} indexed clips',vs,mode=mode)+FOOT
    (d/'index.html').write_text(body)

# Flagship weekly charts
for pg,title,desc,vs,mode in [
    ('funniest-this-week','BingeBuzz Funniest 25','The 25 comedy clips with the strongest BingeBuzz Funny Signal this week.',FUN_WEEK,'funny'),
    ('viral-this-week','BingeBuzz Viral 25','The videos America could not stop watching this week, ranked by BingeBuzz momentum.',VIRAL_WEEK,'buzz'),
    ('viral-usa','Viral USA','What is blowing up across YouTube in the United States right now.',VIRAL_WEEK,'buzz'),
]:
    d=ROOT/pg; d.mkdir(parents=True,exist_ok=True)
    image=make_social_card(f'/assets/social/{pg}.png','WEEKLY CHART',title,'',f'{len(vs)} RANKED')
    rows=chart_rows(vs,'funny' if mode=='funny' else 'buzz',25)
    body=head(f'{title} | BingeBuzz.TV',desc,f'/{pg}/',image)+NAV+f'''<section class="subhero chart-hero"><div class="wrap"><div class="kicker">Official BingeBuzz chart</div><h1>{esc(title)}.</h1><p>{esc(desc)} Rankings update throughout the week; each weekly result becomes part of the BingeBuzz archive.</p><div class="share-row"><button class="share share-primary" data-share="{BASE}/{pg}/" data-title="{esc(title)}">Share this chart</button><a class="share" href="/battle/">⚔ Help judge the rankings</a></div></div></section><section class="section"><div class="wrap"><div class="chart">{rows or '<div class="empty"><strong>Chart warming up.</strong>Run the updater once.</div>'}</div></div></section>'''+FOOT
    (d/'index.html').write_text(body)

# Creator pages with status
creator_fun_rank={}
for i,v in enumerate(FUN_WEEK,1):
    creator_fun_rank[v.get('creator')] = min(i, creator_fun_rank.get(v.get('creator'),999))
creator_trend_rank={}
for i,v in enumerate(TREND,1):
    creator_trend_rank[v.get('creator')] = min(i, creator_trend_rank.get(v.get('creator'),999))

for c in CREATORS:
    name=c.get('creator'); cslug=slug(name); d=ROOT/'creators'/cslug; d.mkdir(parents=True,exist_ok=True)
    cv=sorted_buzz([v for v in COMEDY if v.get('creator')==name])
    fr=creator_fun_rank.get(name); tr=creator_trend_rank.get(name)
    achievement = f'TOP {fr} FUNNIEST THIS WEEK' if fr and fr<=10 else (f'#{tr} TRENDING CREATOR' if tr and tr<=10 else f'CREATOR BUZZ {int(round(c.get("creator_buzz",0)))}')
    image=make_social_card(f'/assets/social/creator-{cslug}.png','CREATOR STATUS',achievement,name,f'BUZZ {int(round(c.get("creator_buzz",0)))}')
    body=head(f'{name} | BingeBuzz Creator Profile',f'BingeBuzz rankings and recent clips for {name}.',f'/creators/{cslug}/',image)+NAV+f'''<section class="subhero creator-hero"><div class="wrap"><div class="kicker">Creator status</div><div class="achievement-pill">{esc(achievement)}</div><h1>{esc(name)}</h1><p>Current creator Buzz <strong>{int(round(c.get('creator_buzz',0)))}</strong> • {human(c.get('recent_views',0))} indexed recent views • {len(cv)} clips tracked.</p><div class="share-row"><button class="share share-primary" data-share="{BASE}/creators/{cslug}/" data-title="{esc(name+' on BingeBuzz')}">Share creator status</button></div></div></section>'''+section('Latest heat','Ranked by current Buzz Score.',cv)+FOOT
    (d/'index.html').write_text(body)

# Creator charts
rising=sorted(CREATORS,key=lambda c:(c.get('momentum_score',0),c.get('creator_buzz',0)),reverse=True)
rows=''.join(f'''<a class="chart-row" href="/creators/{slug(c.get('creator'))}/"><span class="num">{i}</span><div><h3>{esc(c.get('creator'))}</h3><small>{c.get('clip_count',0)} recent clips</small></div><strong>{int(round(c.get('creator_buzz',0)))}</strong><span>{human(c.get('recent_views',0))} views</span><span class="chip">↑ {int(round(c.get('momentum_score',0)))}</span></a>''' for i,c in enumerate(rising[:100],1))
(ROOT/'rising').mkdir(exist_ok=True)
(ROOT/'rising/index.html').write_text(head('Rising Comedy Creators | BingeBuzz.TV','Comedy creators currently outperforming their recent BingeBuzz baseline.','/rising/')+NAV+'''<section class="subhero"><div class="wrap"><div class="kicker">Momentum chart</div><h1>Rising creators.</h1><p>Creators with the strongest recent clip momentum across the BingeBuzz source universe.</p></div></section>'''+f'<section class="section"><div class="wrap"><div class="chart">{rows or "<div class=empty><strong>Chart warming up.</strong></div>"}</div></div></section>'+FOOT)

bb100=sorted(CREATORS,key=lambda c:(c.get('creator_buzz',0),c.get('recent_views',0)),reverse=True)[:100]
rows=''.join(f'''<a class="chart-row" href="/creators/{slug(c.get('creator'))}/"><span class="num">{i}</span><div><h3>{esc(c.get('creator'))}</h3><small>{c.get('clip_count',0)} clips in current window</small></div><strong>{int(round(c.get('creator_buzz',0)))}</strong><span>{human(c.get('recent_views',0))} views</span><span class="chip">BUZZ</span></a>''' for i,c in enumerate(bb100,1))
(ROOT/'charts/bingebuzz-100').mkdir(parents=True,exist_ok=True)
(ROOT/'charts/bingebuzz-100/index.html').write_text(head('BingeBuzz 100 | Comedy Creator Chart','The BingeBuzz 100 ranks comedy creators using current video performance signals.','/charts/bingebuzz-100/')+NAV+'''<section class="subhero"><div class="wrap"><div class="kicker">Creator scoreboard</div><h1>BingeBuzz 100.</h1><p>The comedy creators generating the most heat across the BingeBuzz index.</p></div></section>'''+f'<section class="section"><div class="wrap"><div class="chart">{rows or "<div class=empty><strong>Chart warming up.</strong></div>"}</div></div></section>'+FOOT)

# Video pages
for v in VIDEOS:
    d=ROOT/'videos'/v['video_id']; d.mkdir(parents=True,exist_ok=True)
    url=f'{BASE}/videos/{v["video_id"]}/'; story, metric=video_story(v)
    social=make_social_card(f'/assets/social/video-{v["video_id"]}.png',story,v['title'],v.get('creator',''),metric)
    desc=f'{story}: {v.get("creator")} — {v.get("title")}. {metric}. Watch from the original source and share your take.'
    opponent=None
    if v.get('category')!='viral':
        for candidate in TREND:
            if candidate['video_id'] != v['video_id']:
                opponent=candidate; break
    challenge=f'''<a class="share" href="/battle/?champ={esc(v['video_id'])}">⚔ Challenge this ranking</a>''' if opponent else ''
    rank_context = status_line(v)
    body=head(f"{v['title']} | BingeBuzz.TV",desc,f"/videos/{v['video_id']}/",social)+NAV+f'''<main class="wrap video-page"><section><div class="player" data-embed="{esc(v['video_id'])}" style="cursor:pointer;background:url('{esc(v.get('thumbnail'))}') center/cover"><button class="play player-button">▶ Play original video</button></div>{rank_context}<section class="take-panel" data-take-panel data-video="{esc(v['video_id'])}" data-title="{esc(v['title'])}" data-url="{esc(url)}"><div><div class="kicker">YOUR TAKE</div><h2>Was it actually good?</h2><p>One tap. No account.</p></div><div class="take-buttons"><button class="take" data-take="funny">😂 Funny</button><button class="take" data-take="nope">😐 Nope</button></div><div class="take-result" data-take-result hidden></div></section><div class="share-row"><button class="share share-primary" data-share-take data-share="{esc(url)}" data-title="{esc(story+': '+v['title'])}">Share your take</button>{challenge}<a class="share" href="{esc(v.get('youtube_url'))}" rel="noopener" target="_blank">Open on YouTube ↗</a></div></section><aside class="video-info"><div class="kicker">{esc(v.get('category','comedy'))} • {esc(story)}</div><h1>{esc(v['title'])}</h1><div class="metric-stack"><div><strong>{int(round(v.get('buzz_score',0)))}</strong><span>Buzz</span></div><div><strong>{int(round(v.get('funny_score',0)))}</strong><span>Laugh signal</span></div><div><strong>{int(round(v.get('breakout_score',0)))}</strong><span>Breakout</span></div></div><div class="meta"><span>{human(v.get('views'))} views</span><span>{human(v.get('likes'))} likes</span><span>{age_label(v.get('published_at',''))}</span></div><div class="creator-panel"><b>{esc(v.get('creator'))}</b><p>BingeBuzz indexes public source metadata and plays this video from its original source. Views and engagement stay with the creator/platform.</p><a class="play" href="/creators/{slug(v.get('creator'))}/">See creator status →</a></div></aside></main>'''
    if opponent:
        body += f'''<section class="section"><div class="wrap"><div class="section-head"><div><div class="section-eyebrow">NEXT ACTION</div><h2>⚔ Can it beat this?</h2><p>Pick the clip you think deserves the higher spot.</p></div></div>{battle_block(v,opponent,True)}</div></section>'''
    body += FOOT
    (d/'index.html').write_text(body)

# Battle page with a pool rendered by JS
pool=TREND[:16]
pool_json=json.dumps([{k:v.get(k) for k in ['video_id','title','creator','thumbnail','buzz_score']} | {'rank':TREND_RANK.get(v['video_id'])} for v in pool]).replace('</','<\\/')
if len(pool)>=2:
    initial=battle_block(pool[0],pool[1])
else:
    initial='<div class="empty"><strong>Battle warming up.</strong>Run the updater once.</div>'
(ROOT/'battle').mkdir(exist_ok=True)
(ROOT/'battle/index.html').write_text(head('Laugh Battle | BingeBuzz.TV','Judge head-to-head comedy clips and see whether your taste matches the current BingeBuzz rankings.','/battle/')+NAV+'''<section class="subhero battle-hero"><div class="wrap"><div class="kicker">Help judge the chart</div><h1>Laugh Battle.</h1><p>Two hot clips enter. Pick the winner, then keep going. Your picks are saved on this device—no account required.</p></div></section>'''+f'''<section class="section"><div class="wrap"><div class="battle-progress"><strong data-battle-count>0</strong><span>battles judged</span></div><div id="battle-arena">{initial}</div><div class="battle-actions"><button class="share" data-next-battle>Next battle →</button><button class="share share-primary" data-share="{BASE}/battle/" data-title="Laugh Battle on BingeBuzz">Challenge a friend</button></div><script type="application/json" id="battle-pool">{pool_json}</script></div></section>'''+FOOT)

# Methodology / sources / setup
(ROOT/'methodology').mkdir(exist_ok=True)
(ROOT/'methodology/index.html').write_text(head('BingeBuzz Ranking Methodology | BingeBuzz.TV','How BingeBuzz ranks trending, funny, viral and breakout clips.','/methodology/')+NAV+'''<section class="subhero"><div class="wrap"><div class="kicker">Transparent ranking</div><h1>How BingeBuzz works.</h1><p>A live discovery scoreboard—not a scientific measurement of comedy.</p></div></section><section class="section"><div class="wrap content"><h2>Buzz Score</h2><p>Buzz combines recent view acceleration, velocity since upload, like-to-view engagement, reach and freshness. It is normalized against other recent videos in the current dataset.</p><h2>Laugh Signal</h2><p>The weekly Funniest 25 uses an algorithmic comedy signal weighted toward engagement, discussion, current heat and freshness. It is a score, not a claim that a percentage of people laughed. One-tap visitor reactions are stored on-device in the current static build.</p><h2>Viral USA</h2><p>BingeBuzz also ingests YouTube's U.S. most-popular chart and reranks those videos using the same momentum framework. This creates a broader viral feed without diluting the comedy source universe.</p><h2>Breakout Signal</h2><p>Breakout rewards videos with unusually strong velocity and acceleration while their total reach is still relatively small. It is designed to surface clips before they become obvious hits.</p><div class="callout"><strong>The principle:</strong>The internet watches. BingeBuzz keeps score.</div><h2>Source integrity</h2><p>BingeBuzz stores metadata and original rankings, not copies of creator videos. Playback uses source-platform embeds and every clip page links to the original video.</p></div></section>'''+FOOT)

source_rows=''.join(f'<div class="chart-row"><span class="num">{i}</span><div><h3>{esc(c.get("label"))}</h3><small>{esc(c.get("handle"))}</small></div><strong>{esc(c.get("default_category"))}</strong><span></span><span class="chip">TRACKED</span></div>' for i,c in enumerate(CHANNELS,1))
(ROOT/'sources').mkdir(exist_ok=True)
(ROOT/'sources/index.html').write_text(head('Comedy Sources | BingeBuzz.TV','Official comedy channels tracked by BingeBuzz.','/sources/')+NAV+'''<section class="subhero"><div class="wrap"><div class="kicker">Source universe</div><h1>Who we watch.</h1><p>Official comedy channels plus a separate U.S. viral chart feed. BingeBuzz ranks public videos without rehosting them.</p></div></section>'''+f'<section class="section"><div class="wrap"><div class="chart">{source_rows}</div><div class="content"><h2>Add or remove comedy sources</h2><p>Edit <code>data/channels.json</code>. The updater resolves YouTube handles automatically.</p></div></div></section>'+FOOT)

(ROOT/'api-setup').mkdir(exist_ok=True)
(ROOT/'api-setup/index.html').write_text(head('YouTube API Setup | BingeBuzz.TV','Connect the YouTube Data API key used by the BingeBuzz GitHub Actions updater.','/api-setup/')+NAV+'''<section class="subhero"><div class="wrap"><div class="kicker">One required secret</div><h1>Connect YouTube.</h1><p>BingeBuzz uses a YouTube Data API key to refresh public source metadata and the U.S. most-popular chart. OAuth is not required.</p></div></section><section class="section"><div class="wrap content"><h2>1. Enable YouTube Data API v3</h2><p>In Google Cloud, enable YouTube Data API v3 for your project.</p><h2>2. Create an API key</h2><p>Create a standard API key under APIs & Services → Credentials.</p><h2>3. Add the GitHub secret</h2><p>Repository → Settings → Secrets and variables → Actions → New repository secret.</p><div class="callout"><strong>Name it exactly:</strong><code>YOUTUBE_API_KEY</code></div><h2>4. Run the updater</h2><p>Run <strong>Update BingeBuzz feeds and deploy</strong> once. The scheduled job then refreshes every three hours.</p></div></section>'''+FOOT)

# Daily archive
if VIDEOS:
    day=(DATA.get('meta',{}).get('generated') or '')[:10] or date.today().isoformat()
    dd=ROOT/'daily'/day; dd.mkdir(parents=True,exist_ok=True)
    (dd/'index.html').write_text(head(f'Top Comedy Clips — {day} | BingeBuzz.TV',f'BingeBuzz daily chart for {day}.',f'/daily/{day}/')+NAV+f'''<section class="subhero"><div class="wrap"><div class="kicker">Daily archive</div><h1>{day}</h1><p>The top BingeBuzz comedy clips captured for this day.</p></div></section>'''+section('Daily Top 20','Archived from the live feed.',TREND[:20],ranked=True)+FOOT)

# Legacy redirects
redirects={'stand-up':'/standup/','standup-newbies':'/rising/','comedy-podcasts':'/podcasts/','top-stand-up':'/trending/','legends':'/charts/bingebuzz-100/'}
for old,target in redirects.items():
    p=ROOT/old; p.mkdir(parents=True,exist_ok=True)
    (p/'index.html').write_text(f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={target}"><link rel="canonical" href="{BASE+target}"><title>Moved | BingeBuzz.TV</title><a href="{target}">Continue</a>')

# Feeds and sitemap
rssitems=''.join(f'''<item><title>{esc(v['title'])}</title><link>{BASE}/videos/{v['video_id']}/</link><guid>{BASE}/videos/{v['video_id']}/</guid><pubDate>{esc(v.get('published_at',''))}</pubDate></item>''' for v in TREND[:25])
(ROOT/'feed.xml').write_text(f'''<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>BingeBuzz Trending</title><link>{BASE}</link><description>Comedy and viral clips ranked by BingeBuzz.</description>{rssitems}</channel></rss>''')
urls=['/','/trending/','/funniest-this-week/','/viral-this-week/','/viral-usa/','/today/','/standup/','/podcasts/','/crowdwork/','/shorts/','/sketch/','/rising/','/charts/bingebuzz-100/','/battle/','/methodology/','/sources/','/api-setup/']
urls += [f"/videos/{v['video_id']}/" for v in VIDEOS]
urls += [f"/creators/{slug(c.get('creator'))}/" for c in CREATORS]
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{BASE}{u}</loc></url>' for u in urls)+'</urlset>')
(ROOT/'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n')
(ROOT/'CNAME').write_text('bingebuzz.tv\n')
(ROOT/'404.html').write_text(head('Not Found | BingeBuzz.TV','Page not found.')+NAV+'<section class="subhero"><div class="wrap"><div class="kicker">404</div><h1>Bombed.</h1><p>That page did not survive the set.</p><a class="play" href="/">Back to the scoreboard →</a></div></section>'+FOOT)
