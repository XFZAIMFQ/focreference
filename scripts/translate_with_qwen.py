"""Translate English text nodes while preserving the original HTML structure."""
import concurrent.futures
import json
import os
import pathlib
import re
import sys
import threading
import time
from collections import Counter

import requests

from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parents[1]
EN = ROOT/'src/docs/en'
OUT = ROOT / 'src/docs/zh-candidate'
CACHE_FILE = ROOT / 'scripts/qwen_translation_memory.json'
PARA_CACHE_FILE = ROOT / 'scripts/legacy_translation_memory.json'
REPORT = ROOT / 'scripts/qwen_translation_report.json'
KEY = os.environ.get('DASHSCOPE_API_KEY')
ENDPOINT = os.environ.get('QWEN_MT_ENDPOINT', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions')
SKIP = {'script','style','svg','math','code','pre','kbd','samp'}
WORD = re.compile(r'[A-Za-z]{2,}')
SEG = re.compile(r'⟦SEG_(\d{3})⟧\s*')
DOMAIN = ('This text comes from a technical educational website about field-oriented control (FOC) '
          'of permanent-magnet synchronous motors (PMSM). Translate into precise natural Simplified '
          'Chinese for electrical engineers. Keep variables, symbols, numbers, signs, units, acronyms '
          'and placeholders unchanged. Preserve each ⟦SEG_...⟧ marker exactly once and in order. '
          'Some items may be sentence fragments split by inline equations or links; translate them '
          'faithfully without adding or omitting content.')
TERMS = [
 ('field-oriented control','磁场定向控制'),('space vector','空间矢量'),
 ('space-vector PWM','空间矢量 PWM'),('space-vector modulation','空间矢量调制'),
 ('Clarke transform','Clarke 变换'),('Park transform','Park 变换'),
 ('d-axis','d 轴'),('q-axis','q 轴'),('stator frame','定子坐标系'),
 ('rotor frame','转子坐标系'),('deadtime','死区时间'),
 ('anti-windup','抗积分饱和'),('windup','积分饱和'),
 ('field weakening','弱磁控制'),('current loop','电流环'),
 ('speed loop','速度环'),('position loop','位置环'),
 ('back-EMF','反电动势'),('DC link','直流母线'),
 ('shunt','分流电阻'),('per-unit','标幺值'),
 ('common-mode','共模'),('zero-sequence','零序'),
 ('magnetomotive force','磁动势'),('reluctance torque','磁阻转矩'),
 ('magnet torque','永磁转矩'),('exact-ZOH','精确零阶保持'),
 ('observer','观测器'),('MTPA','最大转矩电流比（MTPA）'),
]
MANUAL = {
 'FOC Reference':'FOC 参考手册',
 'Field-oriented control':'磁场定向控制',
 'Foundations':'基础', 'The machine':'电机', 'The inverter':'逆变器',
 'Sensing':'传感与测量', 'Control and estimation':'控制与估算',
 'Implementation':'工程实现', 'Reference':'参考资料', 'Contents':'目录',
 'Search':'搜索', 'Start learning':'开始学习', 'Formula sheet':'公式速查',
 'Notation':'符号约定', 'What goes wrong':'故障排查',
 'Space vectors':'空间矢量','Power in three phases':'三相功率',
 'Clarke and Park':'Clarke 与 Park 变换','Per-unit and scaling':'标幺值与缩放',
 'The PMSM dq model':'PMSM 的 dq 模型','PMSM dq model':'PMSM 的 dq 模型',
 'Measuring the machine':'电机参数测量','Torque and MTPA':'转矩与 MTPA',
 'Field weakening':'弱磁控制','The bridge':'三相桥',
 'Six-step commutation':'六步换相','Space-vector PWM':'空间矢量 PWM',
 'Deadtime':'死区时间','Current measurement':'电流测量',
 'The converter':'模数转换器','The DC link':'直流母线',
 'Position sensors':'位置传感器','The current loop':'电流环',
 'Speed and position loops':'速度环与位置环','Sampled time':'采样时间',
 'Sensorless position':'无位置传感器估算',
 'Timing and synchronisation':'时序与同步',
 'The peripherals it needs':'所需外设',
 'Software architecture':'软件架构',
 'Bringing a drive up':'驱动系统调试',
}


def wanted(node):
    if any(a.name in SKIP or 'katex' in a.get('class', [])
           for a in [node.parent,*node.parents] if getattr(a,'name',None)):
        return False
    t=str(node).strip()
    if not t or not WORD.search(t): return False
    words=re.findall(r'[A-Za-z]+',t)
    return not (words and all(w.isupper() for w in words))


files=list(EN.glob('*.html'))
strings=set()
for file in files:
    soup=BeautifulSoup(file.read_text(encoding='utf8'),'html.parser')
    for node in soup.find_all(string=True):
        if wanted(node): strings.add(str(node).strip())
    for tag in soup.find_all(True):
        for attr in ('aria-label','alt','placeholder','title'):
            val=tag.get(attr)
            if isinstance(val,str) and WORD.search(val): strings.add(val.strip())

cache=json.loads(CACHE_FILE.read_text(encoding='utf8')) if CACHE_FILE.exists() else {}
cache.update(MANUAL)
if PARA_CACHE_FILE.exists():
    import hashlib
    para=json.loads(PARA_CACHE_FILE.read_text(encoding='utf8'))
    for source in strings:
        if source not in cache:
            val=para.get(hashlib.sha256(source.encode('utf8')).hexdigest())
            if val and not re.search(r'⟦[A-Z]+_\d+⟧',val): cache[source]=val
pending=sorted((s for s in strings if s not in cache),key=len,reverse=True)
print('STRINGS',len(strings),'PENDING',len(pending),'CHARS',sum(map(len,pending)),flush=True)

groups=[]; group=[]; size=0
for item in pending:
    extra=len(item)+16
    if group and (size+extra>2700 or len(group)>=20):
        groups.append(group);group=[];size=0
    group.append(item);size+=extra
if group:groups.append(group)
print('BATCHES',len(groups),flush=True)
if os.environ.get('QWEN_DRY_RUN'):
    (ROOT / 'scripts/qwen_first_batch.txt').write_text('\n'.join(f'⟦SEG_{i:03d}⟧\n{x}' for i,x in enumerate(groups[0])),encoding='utf8')
    raise SystemExit('dry run complete')
if pending and not KEY: raise SystemExit('DASHSCOPE_API_KEY required')

local=threading.local(); rate_lock=threading.Lock(); lock=threading.Lock(); last=[0.0]
usage=Counter();fallbacks=[];failures=[]
def slot():
    with rate_lock:
        delay=max(0,last[0]+3.8-time.monotonic())
        if delay:time.sleep(delay)
        last[0]=time.monotonic()

def translate(items):
    if not hasattr(local,'session'):local.session=requests.Session()
    source='\n'.join(f'⟦SEG_{i:03d}⟧\n{x}' for i,x in enumerate(items))
    lower=source.lower()
    terms=[{'source':a,'target':b} for a,b in TERMS if a.lower() in lower]
    payload={'model':'qwen-mt-plus','messages':[{'role':'user','content':source}],
             'translation_options':{'source_lang':'English','target_lang':'Chinese',
                                    'domains':DOMAIN,'terms':terms}}
    last_error=None
    for attempt in range(4):
        try:
            slot()
            r=local.session.post(ENDPOINT,headers={'Authorization':'Bearer '+KEY},json=payload,timeout=90)
            if r.status_code in (429,500,502,503,504):
                raise RuntimeError(f'HTTP {r.status_code}: {r.text[:180]}')
            r.raise_for_status()
            data=r.json();t=data['choices'][0]['message']['content']
            with lock:
                usage.update({k:int((data.get('usage') or {}).get(k,0)) for k in
                              ('prompt_tokens','completion_tokens','total_tokens')})
            parts=SEG.split(t)
            found={int(parts[i]):parts[i+1].strip() for i in range(1,len(parts)-1,2)}
            if len(items)==1 and not found:found={0:t.strip()}
            if len(found)==len(items) and all(i in found for i in range(len(items))):
                return {x:found[i] for i,x in enumerate(items)}
            last_error=ValueError(f'markers {len(found)}/{len(items)}')
            if len(items)>1:break
        except Exception as e:
            last_error=e
            if attempt<3:time.sleep(8*(attempt+1) if '429' in str(e) else 2*(attempt+1))
    if len(items)>1:
        mid=len(items)//2
        return translate(items[:mid])|translate(items[mid:])
    with lock:fallbacks.append({'source':items[0][:120],'error':str(last_error)[:160]})
    return {items[0]:items[0]}

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    tasks={pool.submit(translate,g):i for i,g in enumerate(groups)}
    for n,f in enumerate(concurrent.futures.as_completed(tasks),1):
        try:result=f.result()
        except Exception as e:
            failures.append({'batch':tasks[f],'error':str(e)[:250]});continue
        with lock:
            cache.update(result)
            CACHE_FILE.write_text(json.dumps(cache,ensure_ascii=False,indent=1),encoding='utf8')
        if n%10==0 or n==len(groups):print('PROGRESS',n,'/',len(groups),'CACHE',len(cache),flush=True)

missing=strings-cache.keys()
if missing or failures:raise SystemExit(f'{len(missing)} missing strings, {len(failures)} failures')
OUT.mkdir(parents=True,exist_ok=True)
for file in files:
    soup=BeautifulSoup(file.read_text(encoding='utf8'),'html.parser')
    if soup.html:soup.html['lang']='zh-CN'
    for node in soup.find_all(string=True):
        if not wanted(node):continue
        old=str(node);s=old.strip()
        leading=old[:len(old)-len(old.lstrip())]
        trailing=old[len(old.rstrip()):]
        node.replace_with(leading+cache[s]+trailing)
    for tag in soup.find_all(True):
        for attr in ('aria-label','alt','placeholder','title'):
            val=tag.get(attr)
            if isinstance(val,str) and val.strip() in cache:tag[attr]=cache[val.strip()]
    (OUT/file.name).write_text(str(soup),encoding='utf8')

checks=[]
for source,target in cache.items():
    src=Counter(re.findall(r'(?<![A-Za-z_])\d+(?:[.,]\d+)?%?',source))
    dst=Counter(re.findall(r'(?<![A-Za-z_])\d+(?:[.,]\d+)?%?',target))
    if src!=dst:checks.append({'source':source[:160],'target':target[:160],
                               'source_numbers':dict(src),'target_numbers':dict(dst)})
REPORT.write_text(json.dumps({'model':'qwen-mt-plus','pages':len(files),'strings':len(strings),
                              'usage_this_run':dict(usage),'fallbacks':fallbacks,
                              'failures':failures,'number_mismatches':checks},ensure_ascii=False,indent=2),encoding='utf8')
print('DONE',len(files),'PAGES','FALLBACKS',len(fallbacks),'NUMBER_CHECKS',len(checks),'USAGE',dict(usage),flush=True)
