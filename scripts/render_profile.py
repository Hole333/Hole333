import argparse,collections,datetime,json,os,re,urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--data');parser.add_argument('--output',default=str(root/'assets/template'));args=parser.parse_args()
out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
profile=json.loads((root/'profile.json').read_text(encoding='utf-8'))
assert re.fullmatch(r'[A-Za-z0-9-]+',profile['login'])
def api(path):
    headers={'Accept':'application/vnd.github+json','User-Agent':'HaloMoon-profile'}
    if os.environ.get('GH_TOKEN'):headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
    with urllib.request.urlopen(urllib.request.Request('https://api.github.com/'+path,headers=headers),timeout=30) as r:return json.load(r)
if args.data:data=json.loads(Path(args.data).read_text(encoding='utf-8'))
else:
    repos=[];page=1
    while True:
        chunk=api('users/'+profile['login']+'/repos?type=owner&per_page=100&page='+str(page));repos+=chunk
        if len(chunk)<100:break
        page+=1
    data={'user':api('users/'+profile['login']),'repos':repos}
assert data['user']['login'].lower()==profile['login'].lower()
repos={r['name']:r for r in data['repos'] if not r.get('private',False)}
projects=[r for r in repos.values() if not r['fork'] and r['name'].lower()!=profile['login'].lower()]
date=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
font="'Segoe UI','Microsoft YaHei','Noto Sans CJK SC',Arial,sans-serif"
mono="Consolas,Menlo,monospace"
def txt(x,y,value,size=16,color='#392C3D',weight='400',anchor='start',family=None):
    return '<text x="'+str(x)+'" y="'+str(y)+'" font-size="'+str(size)+'" fill="'+color+'" font-weight="'+weight+'" text-anchor="'+anchor+'" font-family="'+(family or font)+'">'+escape(str(value))+'</text>'
def svg(name,width,height,body,style='',title='Halo Moon'):
    result='<svg xmlns="http://www.w3.org/2000/svg" width="'+str(width)+'" height="'+str(height)+'" viewBox="0 0 '+str(width)+' '+str(height)+'" role="img" aria-labelledby="title"><title id="title">'+escape(title)+'</title>'
    if style:result+='<style>'+style+'</style>'
    result+=body+'</svg>\n';(out/name).write_bytes(result.encode('utf-8'))
gradient='<defs><linearGradient id="warm" x1="0" x2="1" y1="0" y2="0"><stop stop-color="#FF5F6D"/><stop offset=".55" stop-color="#FF9671"/><stop offset="1" stop-color="#FFC371"/></linearGradient></defs>'
wave='<path class="wave" d="M-280 198'+('q70 -25 140 0t140 0'*6)+'v80H-280Z" fill="#fff" opacity=".2"/>'
surface='M0 0H1120V207Q840 272 560 208T0 211Z'
header=gradient+'<defs><clipPath id="headerClip"><path d="'+surface+'"/></clipPath></defs><path d="'+surface+'" fill="url(#warm)"/><g clip-path="url(#headerClip)">'+wave+'</g>'
header+='<g class="headline">'+txt(560,112,profile['name'],76,'#542642','700','middle')+txt(560,159,'halomoon.cn',22,'#542642','500','middle')+'</g>'
motion='@keyframes drift{to{transform:translateX(-280px)}}@keyframes enter{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}.wave{animation:drift 12s linear infinite}.headline{animation:enter 200ms cubic-bezier(0.23,1,0.32,1) both}@media(prefers-reduced-motion:reduce){.wave,.headline{animation:none}}'
svg('header-wave.svg',1120,250,header,motion)
svg('header-static.svg',1120,250,header)
surface='M0 30Q280 92 560 38T1120 36V110H0Z'
footer=gradient+'<defs><clipPath id="footerClip"><path d="'+surface+'"/></clipPath></defs><path d="'+surface+'" fill="url(#warm)"/><g clip-path="url(#footerClip)"><g transform="translate(0,-155)">'+wave+'</g></g>'
svg('footer-wave.svg',1120,110,footer,motion);svg('footer-static.svg',1120,110,footer)
line='Embedded Linux  /  MCU  /  FreeRTOS  /  Machine Vision';n=len(line);length=n*13;start=(1000-length)/2
letters=txt(0,48,line,22,'#2483B7','600',family=mono).replace('<text ','<text textLength="'+str(length)+'" lengthAdjust="spacingAndGlyphs" ')
typing='<g transform="translate('+str(start)+',0)"><g class="typed">'+letters+'</g><rect class="caret" x="0" y="28" width="2" height="27" fill="#2483B7"/></g>'
typingcss='@keyframes type{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}@keyframes cursor{to{transform:translateX('+str(length)+'px)}}@keyframes blink{50%{opacity:0}}.typed{clip-path:inset(0 0 0 0);animation:type 3s steps('+str(n)+',end) both}.caret{animation:cursor 3s steps('+str(n)+',end) forwards,blink 800ms steps(2,end) infinite}@media(prefers-color-scheme:dark){text,.caret{fill:#72C9F1}}@media(prefers-reduced-motion:reduce){.typed{animation:none}.caret{display:none}}'
svg('focus-typing.svg',1000,80,typing,typingcss,title=line)
svg('focus-static.svg',1000,80,txt(500,48,line,22,'#2483B7','600','middle',mono),'@media(prefers-color-scheme:dark){text{fill:#72C9F1}}',line)
for name,label,color,width in [('github','GitHub','#252A33',122),('blog','个人博客','#D84A67',140),('notes','学习笔记','#CA7A38',140)]:
    b='<rect width="'+str(width)+'" height="34" rx="5" fill="'+color+'"/>'+txt(width/2,23,label,14,'#FFFFFF','600','middle')
    svg('link-'+name+'.svg',width,34,b,title=label)
themes={'light':{'bg':'#FFFBFC','border':'#E8D8E0','fg':'#342B3C','muted':'#76647B','accent':'#C83E62','chip':'#F6EDF2'},'dark':{'bg':'#151321','border':'#393145','fg':'#F5EDF4','muted':'#B4A4BB','accent':'#FF7F97','chip':'#251E32'}}
colors=['#376AB1','#244879','#47414B','#C47A49','#22885A','#AD4C68','#238E58','#5E54A2','#D4593E','#A04864']
def symbol(index,x,y):
    if index in (3,9):
        b='<rect x="'+str(x+31)+'" y="'+str(y+17)+'" width="38" height="38" rx="5" fill="none" stroke="white" stroke-width="3"/>'
        for delta in [0,12,24]:
            b+='<path d="M'+str(x+38+delta)+' '+str(y+10)+'v7m0 38v7M'+str(x+24)+' '+str(y+24+delta)+'h7m38 0h7" stroke="white" stroke-width="3"/>'
        return b
    if index==4:
        return ''.join('<rect x="'+str(x+25)+'" y="'+str(y+18+j*13)+'" width="50" height="7" rx="3" fill="white" opacity="'+str(1-j*.2)+'"/>' for j in range(3))
    if index==5:
        return '<circle cx="'+str(x+50)+'" cy="'+str(y+35)+'" r="21" fill="none" stroke="white" stroke-width="4"/><circle cx="'+str(x+50)+'" cy="'+str(y+35)+'" r="7" fill="white"/>'
    labels={0:'C',1:'C++',2:'Linux',6:'Qt',7:'cm',8:'git'}
    return txt(x+50,y+47,labels[index],28 if index!=2 else 22,'white','700','middle')
languages=collections.Counter(r['language'] for r in projects if r.get('language'))
stars=sum(r['stargazers_count'] for r in projects)
for theme,c in themes.items():
    for item in profile['focus']:
        key={'Embedded Linux':'linux','MCU':'mcu','FreeRTOS':'freertos','Machine Vision':'vision'}[item['title']]
        body='<rect x="1" y="1" width="418" height="138" rx="12" fill="'+c['bg']+'" stroke="'+c['border']+'"/>'
        body+='<rect x="1" y="1" width="5" height="138" rx="2" fill="'+c['accent']+'"/>'
        body+=txt(24,40,item['title'],22,c['accent'],'700')+txt(24,67,item['subtitle'],14,c['muted'])+txt(24,108,item['topics'],16,c['fg'])
        svg('focus-'+key+'-'+theme+'.svg',420,140,body,title=item['subtitle']+' / '+item['topics'])
    tiles=''
    for i,label in enumerate(profile['tools']):
        x=30+(i%5)*155;y=12+(i//5)*110
        tiles+='<rect x="'+str(x)+'" y="'+str(y)+'" width="100" height="72" rx="16" fill="'+colors[i]+'"/>'+symbol(i,x,y)+txt(x+50,y+95,label,14,c['fg'],'600','middle')
    svg('tools-'+theme+'.svg',800,230,tiles,title=' / '.join(profile['tools']))
    frame='<rect x="1" y="1" width="898" height="178" rx="14" fill="'+c['bg']+'" stroke="'+c['border']+'"/>'
    body=frame+txt(28,31,'GitHub / '+profile['login'],16,c['accent'],'700')
    values=[('公开仓库',len(repos)),('原创项目获星',stars),('关注者',data['user']['followers'])]
    for i,(label,value) in enumerate(values):
        x=150+i*300;body+=txt(x,86,value,35,c['fg'],'700','middle')+txt(x,117,label,14,c['muted'],'400','middle')
    body+=txt(870,160,'Updated '+date+' UTC',11,c['muted'],'400','end')
    svg('stats-'+theme+'.svg',900,180,body,title='Hole333 public GitHub statistics')
    body=frame+txt(28,32,'主要语言',17,c['accent'],'700')+txt(870,32,'原创项目 · 按仓库主要语言',12,c['muted'],'400','end')
    total=sum(languages.values());x=28
    legend=languages.most_common(3)
    if len(languages)>3:legend.append(('Other',sum(v for _,v in languages.most_common()[3:])))
    for i,(lang,count) in enumerate(legend):
        width=844*count/max(total,1);color=['#FF7F97','#FFB775','#73BADA','#93CFA4','#B69ADB'][i%5]
        body+='<rect x="'+str(x)+'" y="53" width="'+str(width)+'" height="18" fill="'+color+'"/>';x+=width
        body+=txt(28+i*215,108,lang+' · '+str(count),14,c['fg'],'600')
    body+=txt(870,160,'Updated '+date+' UTC',11,c['muted'],'400','end')
    svg('languages-'+theme+'.svg',900,180,body,title='Primary languages of original public projects')
    for p in profile['projects']:
        assert re.fullmatch(r'[A-Za-z0-9_.-]+',p['repo']) and p['repo'] not in ('.','..')
        r=repos[p['repo']];assert not r['fork'],'Only original projects belong in this list.'
        body='<rect x="1" y="1" width="418" height="158" rx="12" fill="'+c['bg']+'" stroke="'+c['border']+'"/>'
        body+=txt(22,36,p['label'],19,c['accent'],'700')+txt(22,62,p['repo'],11,c['muted'],family=mono)+txt(22,91,p['description'],14,c['fg'])+txt(22,127,p['stack'],12,c['muted'])+txt(396,146,'★ '+str(r['stargazers_count']),11,c['muted'],'400','end')
        svg('project-'+p['repo']+'-'+theme+'.svg',420,160,body,title=p['label']+' / '+p['repo'])
snapshot={'asOf':date+' UTC','login':profile['login'],'publicRepositories':len(repos),'originalProjectStars':stars,'followers':data['user']['followers'],'primaryLanguages':dict(languages),'projects':[{'name':p['repo'],'stars':repos[p['repo']]['stargazers_count'],'fork':repos[p['repo']]['fork']} for p in profile['projects']]}
(out/'profile-data.json').write_bytes((json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'assets':len(list(out.glob('*.svg'))),'account':profile['login'],'publicRepositories':len(repos),'projects':len(profile['projects']),'noInventedStats':True}))
