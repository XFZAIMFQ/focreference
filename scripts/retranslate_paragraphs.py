"""Re-translate split HTML paragraphs with their full sentence context.

Inline tags become numbered placeholders, then the translated text and the
original corresponding tags are reassembled. Results go to a review directory.
"""
import concurrent.futures
import copy
import json
import os
import pathlib
import re
import sys
import threading
import time
from collections import Counter

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT=pathlib.Path(__file__).resolve().parents[1]
EN=ROOT/'src/docs/en'
BASE=ROOT/'src/docs/zh'
OUT=ROOT/'src/docs/zh-paragraph-candidate'
CACHE_FILE=ROOT/'scripts/qwen_paragraph_memory.json'
REPORT=ROOT/'scripts/qwen_paragraph_report.json'
KEY=os.environ.get('DASHSCOPE_API_KEY')
ENDPOINT='https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
BLOCK_RE=re.compile(r'⟦BLOCK_(\d{3})⟧\s*')
PH_RE=re.compile(r'⟦PH_(\d+)⟧')
NUM_RE=re.compile(r'(?<![A-Za-z_])\d+(?:\.\d+)?')
SELECTOR='main p, main li, main h2, main h3, main figcaption, main th, main td'

def valid(source,target):
    nums=PH_RE.findall(source)
    got=PH_RE.findall(target)
    if sorted(nums)!=sorted(got) or target.strip()==source.strip():return False
    src=Counter(NUM_RE.findall(PH_RE.sub('',source)))
    dst=Counter(NUM_RE.findall(PH_RE.sub('',target)))
    return all(dst[n]>=count for n,count in src.items())

def prepare(en,zh):
    if len(en.get_text(' ',strip=True))<80:return None
    e_tags=[x for x in en.contents if isinstance(x,Tag)]
    z_tags=[x for x in zh.contents if isinstance(x,Tag)]
    if not e_tags or len(e_tags)!=len(z_tags):return None
    if [x.name for x in e_tags]!=[x.name for x in z_tags]:return None
    if any(len(x.get_text(' ',strip=True))>100 for x in e_tags):return None
    if not any(isinstance(x,NavigableString) and str(x).strip() for x in en.contents):return None
    bits=[];gloss=[];n=0
    for child in en.contents:
        if isinstance(child,Tag):
            bits.append(f'⟦PH_{n}⟧')
            label=child.get_text(' ',strip=True)
            if len(label)>45:label=label[:45]+'…'
            gloss.append(f'PH_{n}={label or child.name}')
            n+=1
        else:bits.append(str(child))
    source=''.join(bits).strip()
    if len(source)<65 or len(source)>1900:return None
    return {'source':source,'gloss':', '.join(gloss),'tags':z_tags}

pages={};unique={};skipped=Counter()
for file in sorted(EN.glob('*.html')):
    zh_file=BASE/file.name
    if not zh_file.exists():continue
    en_soup=BeautifulSoup(file.read_text(encoding='utf8'),'html.parser')
    zh_soup=BeautifulSoup(zh_file.read_text(encoding='utf8'),'html.parser')
    en_blocks=en_soup.select(SELECTOR);zh_blocks=zh_soup.select(SELECTOR)
    if len(en_blocks)!=len(zh_blocks):raise ValueError(f'block count {file.name}')
    indexed=[]
    for i,(en,zh) in enumerate(zip(en_blocks,zh_blocks)):
        item=prepare(en,zh)
        if item:
            indexed.append((i,item));unique[item['source']]=item['gloss']
    pages[file.name]=(zh_soup,indexed)
    print('PAGE',file.name,len(indexed),flush=True)

cache=json.loads(CACHE_FILE.read_text(encoding='utf8')) if CACHE_FILE.exists() else {}
invalid=[s for s,t in cache.items() if not valid(s,t)]
for s in invalid:del cache[s]
if invalid:print('RETRY_INVALID_CACHE',len(invalid),flush=True)
pending=[(s,g) for s,g in unique.items() if s not in cache]
groups=[];group=[];size=0
for pair in pending:
    extra=len(pair[0])+len(pair[1])+40
    if group and (len(group)>=4 or size+extra>3300):groups.append(group);group=[];size=0
    group.append(pair);size+=extra
if group:groups.append(group)
print('BLOCKS',sum(len(v[1]) for v in pages.values()),'UNIQUE',len(unique),
      'PENDING',len(pending),'BATCHES',len(groups),flush=True)
if pending and not KEY:raise SystemExit('DASHSCOPE_API_KEY required')

local=threading.local();rate_lock=threading.Lock();lock=threading.Lock();last=[0.0]
usage=Counter();failures=[]
def slot():
    with rate_lock:
        delay=max(0,last[0]+3.8-time.monotonic())
        if delay:time.sleep(delay)
        last[0]=time.monotonic()

def translate(items):
    if not hasattr(local,'session'):local.session=requests.Session()
    source='\n'.join(f'⟦BLOCK_{i:03d}⟧\n{x}' for i,(x,_) in enumerate(items))
    gloss='; '.join(f'BLOCK_{i:03d}: {g}' for i,(_,g) in enumerate(items))
    domain=('FOC technical documentation for electrical engineers. Translate each entire paragraph '
            'into fluent, accurate Simplified Chinese. Preserve every ⟦BLOCK_...⟧ boundary and '
            'every ⟦PH_...⟧ inline placeholder exactly once. Inline placeholders stand for links, '
            'formulas, or emphasized terms. Do not add, omit, or change technical claims, numbers, '
            'signs, directions or negation. '+gloss)
    payload={'model':'qwen-mt-plus','messages':[{'role':'user','content':source}],
             'translation_options':{'source_lang':'English','target_lang':'Chinese',
                                    'domains':domain,'terms':[
                {'source':'space vector','target':'空间矢量'},
                {'source':'Clarke and Park','target':'Clarke 与 Park'},
                {'source':'per-unit','target':'标幺值'},
                {'source':'anti-windup','target':'抗积分饱和'},
                {'source':'deadtime','target':'死区时间'},
                {'source':'field weakening','target':'弱磁控制'}]}}
    error='unknown'
    for attempt in range(3):
        try:
            slot()
            r=local.session.post(ENDPOINT,headers={'Authorization':'Bearer '+KEY},json=payload,timeout=90)
            if r.status_code in (429,500,502,503,504):raise RuntimeError(f'HTTP {r.status_code}')
            r.raise_for_status();data=r.json();target=data['choices'][0]['message']['content']
            with lock:usage.update({k:int((data.get('usage') or {}).get(k,0)) for k in
                ('prompt_tokens','completion_tokens','total_tokens')})
            parts=BLOCK_RE.split(target)
            found={int(parts[i]):parts[i+1].strip() for i in range(1,len(parts)-1,2)}
            if len(items)==1 and not found:found={0:target.strip()}
            if len(found)==len(items) and all(i in found and valid(items[i][0],found[i]) for i in range(len(items))):
                return {items[i][0]:found[i] for i in range(len(items))}
            error=f'marker mismatch {len(found)}/{len(items)}'
            if len(items)>1:break
        except Exception as e:
            error=str(e)[:150]
            time.sleep(5*(attempt+1))
    if len(items)>1:
        mid=len(items)//2
        return translate(items[:mid])|translate(items[mid:])
    with lock:failures.append({'source':items[0][0][:150],'error':error})
    return {}

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    jobs={pool.submit(translate,g):i for i,g in enumerate(groups)}
    for n,f in enumerate(concurrent.futures.as_completed(jobs),1):
        result=f.result()
        if result:
            with lock:
                cache.update(result)
                CACHE_FILE.write_text(json.dumps(cache,ensure_ascii=False,indent=1),encoding='utf8')
        if n%10==0 or n==len(groups):print('PROGRESS',n,'/',len(groups),'CACHE',len(cache),flush=True)

OUT.mkdir(parents=True,exist_ok=True)
applied=0
for name,(soup,indexed) in pages.items():
    blocks=soup.select(SELECTOR)
    for i,item in indexed:
        target=cache.get(item['source'])
        if not target or not valid(item['source'],target):continue
        pieces=PH_RE.split(target)
        new=[]
        for j,piece in enumerate(pieces):
            if j%2==0:
                if piece:new.append(NavigableString(piece))
            else:new.append(copy.copy(item['tags'][int(piece)]))
        block=blocks[i]
        block.clear()
        block.extend(new)
        applied+=1
    (OUT/name).write_text(str(soup),encoding='utf8')
REPORT.write_text(json.dumps({'model':'qwen-mt-plus','paragraphs':sum(len(v[1]) for v in pages.values()),
    'unique':len(unique),'applied':applied,'failures':failures,'usage_this_run':dict(usage)},
    ensure_ascii=False,indent=2),encoding='utf8')
print('DONE',applied,'OF',sum(len(v[1]) for v in pages.values()),'FAILURES',len(failures),flush=True)
