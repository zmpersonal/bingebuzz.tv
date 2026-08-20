
from pathlib import Path
import os,json,re,math,csv,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from urllib.parse import urlparse,parse_qs
import requests, subprocess, sys
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[1]
API='https://www.googleapis.com/youtube/v3'
S=requests.Session()
S.headers.update({'User-Agent':'BingeBuzz.TV comedy discovery updater'})
KEY=os.environ.get('YOUTUBE_API_KEY','').strip()
if not KEY: raise RuntimeError('YOUTUBE_API_KEY is not set')

def now(): return datetime.now(timezone.utc)
def dt(s):
    try:return datetime.fromisoformat(s.replace('Z','+00:00'))
    except:return now()
def iso_dur(s):
    m=re.match(r'P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',s or '')
    if not m:return 0
    d,h,mi,se=[int(x or 0) for x in m.groups()]
    return d*86400+h*3600+mi*60+se
def chunks(a,n):
    for i in range(0,len(a),n):yield a[i:i+n]
def api(path,**params):
    params['key']=KEY
    r=S.get(API+path,params=params,timeout=40)
    if r.status_code!=200:
        raise RuntimeError(f'YouTube {path} failed {r.status_code}: {r.text[:500]}')
    return r.json()
def percentile(vals,x):
    vals=sorted(vals)
    if not vals:return .5
    if len(vals)==1:return 1.0
    import bisect
    return bisect.bisect_right(vals,x)/len(vals)
def classify(title,desc,default,dur):
    t=(title+' '+desc).lower()
    if dur and dur<=90:return 'shorts'
    if any(k in t for k in ['crowd work','crowdwork','heckler']):return 'crowdwork'
    if any(k in t for k in ['podcast','episode ',' ep.',' ep ','full episode','interview']):return 'podcast'
    if any(k in t for k in ['sketch','skit','parody']):return 'sketch'
    if any(k in t for k in ['stand up','stand-up','comedy special','full special','live comedy']):return 'standup'
    return default or 'standup'
def yt_id(url):
    try:
      u=urlparse(url)
      if u.hostname in ('youtu.be','www.youtu.be'): return u.path.strip('/').split('/')[0]
      if 'youtube.com' in (u.hostname or ''):
        if u.path=='/watch':return parse_qs(u.query).get('v',[''])[0]
        m=re.search(r'/(?:shorts|embed)/([^/?]+)',u.path)
        if m:return m.group(1)
    except:pass
    return ''
def resolve_sources(config):
    out=[]
    for src in config:
        try:
            d=api('/channels',part='snippet,contentDetails,statistics',forHandle=src['handle'],maxResults=1)
            if not d.get('items'):
                print('SKIP unresolved handle',src['handle']);continue
            c=d['items'][0]
            out.append({**src,'channel_id':c['id'],'channel_title':c['snippet']['title'],
                'uploads':c['contentDetails']['relatedPlaylists']['uploads'],
                'channel_subscribers':int(c.get('statistics',{}).get('subscriberCount',0) or 0)})
            print('SOURCE OK',src['handle'],'=>',c['snippet']['title'])
        except Exception as e: print('SOURCE FAIL',src['handle'],e)
    return out
def recent_upload_ids(sources):
    ids=[]; source_by_id={}
    for src in sources:
        try:
            d=api('/playlistItems',part='snippet,contentDetails',playlistId=src['uploads'],maxResults=20)
            for x in d.get('items',[]):
                vid=x.get('contentDetails',{}).get('videoId')
                if vid: ids.append(vid);source_by_id[vid]=src
        except Exception as e:print('UPLOAD FAIL',src['handle'],e)
    return list(dict.fromkeys(ids)),source_by_id
def fetch_videos(ids):
    out=[]
    for batch in chunks(list(dict.fromkeys(ids)),50):
        d=api('/videos',part='snippet,contentDetails,statistics,status',id=','.join(batch),maxResults=50)
        out.extend(d.get('items',[]))
    return out
def rss_video_ids():
    cfg=json.load(open(ROOT/'data/rss_feeds.json')).get('feeds',[])
    ids=[]
    for f in cfg:
        try:
            r=S.get(f['url'],timeout=25);r.raise_for_status()
            x=ET.fromstring(r.content)
            for e in x.iter():
                txt=(e.text or '')+' '+str(e.attrib)
                for m in re.findall(r'https?://[^\s"<>]+',txt):
                    v=yt_id(m)
                    if v:ids.append(v)
        except Exception as e:print('RSS FAIL',f.get('url'),e)
    return list(dict.fromkeys(ids))
def previous_velocity(hist,vid,views):
    arr=hist.get(vid,[])
    if not arr:return None
    last=arr[-1]
    try:
        hrs=max(.25,(now()-dt(last['at'])).total_seconds()/3600)
        return max(0,(views-int(last['views']))/hrs)
    except:return None

channel_cfg=json.load(open(ROOT/'data/channels.json'))['channels']
sources=resolve_sources(channel_cfg)
if len(sources)<6:
    raise RuntimeError(f'Only {len(sources)} configured YouTube sources resolved; refusing to publish a thin feed.')

existing=json.load(open(ROOT/'data/feed.json'))
existing_by={v['video_id']:v for v in existing.get('videos',[])}
history=json.load(open(ROOT/'data/history.json'))

newids,srcmap=recent_upload_ids(sources)
newids += rss_video_ids()
allids=list(dict.fromkeys(newids+list(existing_by.keys())))[:1500]
raw=fetch_videos(allids)

videos=[]
for x in raw:
    st=x.get('status',{})
    if st.get('privacyStatus')!='public' or st.get('embeddable') is False:continue
    sn=x['snippet']; stats=x.get('statistics',{}); dur=iso_dur(x.get('contentDetails',{}).get('duration'))
    vid=x['id'];views=int(stats.get('viewCount',0) or 0);likes=int(stats.get('likeCount',0) or 0)
    pub=sn.get('publishedAt'); age=max(.5,(now()-dt(pub)).total_seconds()/3600)
    src=srcmap.get(vid,{})
    default=src.get('default_category') or existing_by.get(vid,{}).get('source_default') or 'standup'
    thumb=(sn.get('thumbnails',{}).get('maxres') or sn.get('thumbnails',{}).get('standard') or sn.get('thumbnails',{}).get('high') or {}).get('url','')
    videos.append({
      'video_id':vid,'title':sn.get('title',''),'description':sn.get('description','')[:1500],
      'creator':sn.get('channelTitle',''),'channel_id':sn.get('channelId',''),
      'published_at':pub,'age_hours':round(age,2),'duration_seconds':dur,
      'views':views,'likes':likes,'comments':int(stats.get('commentCount',0) or 0),
      'engagement':(likes/views if views else 0),'age_velocity':views/age,
      'snapshot_velocity':previous_velocity(history,vid,views),'thumbnail':thumb,
      'youtube_url':f'https://www.youtube.com/watch?v={vid}',
      'source_default':default,'category':classify(sn.get('title',''),sn.get('description',''),default,dur)
    })

videos=[v for v in videos if v['age_hours']<=24*730]
recent=[v for v in videos if v['age_hours']<=24*30]
vels=[math.log1p(v['age_velocity']) for v in recent]
deltas=[math.log1p(v['snapshot_velocity'] or 0) for v in recent]
engs=[v['engagement'] for v in recent]
reaches=[math.log1p(v['views']) for v in recent]

for v in videos:
    if v in recent:
      pv=percentile(vels,math.log1p(v['age_velocity']))
      pd=percentile(deltas,math.log1p(v['snapshot_velocity'] or 0))
      pe=percentile(engs,v['engagement'])
      pr=percentile(reaches,math.log1p(v['views']))
      fresh=math.exp(-v['age_hours']/(24*8))
      if v['snapshot_velocity'] is not None: score=100*(.35*pd+.25*pv+.18*pe+.12*pr+.10*fresh)
      else: score=100*(.45*pv+.23*pe+.17*pr+.15*fresh)
      v['buzz_score']=round(min(99,max(1,score)),1)
    else:
      v['buzz_score']=round(min(70,25+20*percentile(reaches,math.log1p(v['views']))),1) if reaches else 25

stamp=now().isoformat()
for v in videos:
    arr=history.setdefault(v['video_id'],[])
    arr.append({'at':stamp,'views':v['views'],'likes':v['likes']})
    history[v['video_id']]=arr[-16:]

cv=defaultdict(list)
for v in videos:
    if v['age_hours']<=24*45:cv[v['creator']].append(v)
creators=[]
for name,vs in cv.items():
    vs=sorted(vs,key=lambda x:x['buzz_score'],reverse=True)
    buzz=sum(v['buzz_score'] for v in vs[:5])/min(5,len(vs))
    snap=[v['snapshot_velocity'] or 0 for v in vs[:5]]
    momentum=sum(math.log1p(x) for x in snap)/max(1,len(snap))
    creators.append({'creator':name,'creator_buzz':round(buzz,1),'momentum_score':round(momentum*10,1),
                     'recent_views':sum(v['views'] for v in vs),'clip_count':len(vs)})
creators.sort(key=lambda c:(c['creator_buzz'],c['recent_views']),reverse=True)
videos.sort(key=lambda v:(v['buzz_score'],v['views']),reverse=True)

meta={'generated':stamp,'live':True,'sources_resolved':len(sources),'videos_indexed':len(videos),'scoring_window_days':30}
json.dump({'meta':meta,'videos':videos},open(ROOT/'data/feed.json','w'),indent=2)
json.dump(history,open(ROOT/'data/history.json','w'),indent=2)
json.dump(creators,open(ROOT/'data/creators.json','w'),indent=2)

with open(ROOT/'data/videos.csv','w',newline='') as f:
    w=csv.writer(f);w.writerow(['video_id','title','creator','category','published_at','views','likes','buzz_score','url'])
    for v in videos:w.writerow([v['video_id'],v['title'],v['creator'],v['category'],v['published_at'],v['views'],v['likes'],v['buzz_score'],f'https://bingebuzz.tv/videos/{v["video_id"]}/'])

social=[]
for i,v in enumerate([x for x in videos if x['age_hours']<=24*14][:20],1):
    social.append({'rank':i,'title':v['title'],'creator':v['creator'],'buzz_score':v['buzz_score'],
      'thumbnail':v['thumbnail'],'url':f'https://bingebuzz.tv/videos/{v["video_id"]}/',
      'suggested_caption':f'🔥 #{i} on BingeBuzz right now: {v["creator"]} — {v["title"]} | Buzz {int(round(v["buzz_score"]))}'})
json.dump(social,open(ROOT/'data/social-queue.json','w'),indent=2)

print(f'LIVE: {len(videos)} videos, {len(creators)} creators, {len(sources)} sources')
subprocess.check_call([sys.executable,str(ROOT/'scripts/build_site.py')])
