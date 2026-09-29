import argparse
import collections
import datetime as dt
import json
import re
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--data')
parser.add_argument('--output', default=str(ROOT / 'assets/profile'))
args = parser.parse_args()
out = Path(args.output)
out.mkdir(parents=True, exist_ok=True)
profile = json.loads((ROOT / 'profile.json').read_text(encoding='utf-8'))
login = profile['login']
assert re.fullmatch(r'[A-Za-z0-9-]+', login)
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
query = '''query($login:String!,$from:DateTime!,$to:DateTime!,$prs:String!,$issues:String!) {
  user(login:$login) { login contributionsCollection(from:$from,to:$to) {
    startedAt endedAt totalRepositoriesWithContributedCommits
    commitContributionsByRepository(maxRepositories:100) {
      repository { nameWithOwner isPrivate } contributions { totalCount }
    }
  } repositories(first:100,ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false) {
    pageInfo {hasNextPage} nodes { name isFork isPrivate stargazerCount
      languages(first:100,orderBy:{field:SIZE,direction:DESC}) {
        pageInfo {hasNextPage} edges {size node {name color}}
      }
    }
  } }
  prs:search(query:$prs,type:ISSUE,first:1){issueCount}
  issues:search(query:$issues,type:ISSUE,first:1){issueCount}
}'''
if args.data:
    data = json.loads(Path(args.data).read_text(encoding='utf-8'))
else:
    variables = {'login':login, 'from':(now-dt.timedelta(days=365)).isoformat(), 'to':now.isoformat(), 'prs':'is:pr author:'+login+' is:public', 'issues':'is:issue author:'+login+' is:public'}
    response = subprocess.run(['gh','api','graphql','--input','-'], input=json.dumps({'query':query,'variables':variables}).encode(), capture_output=True, timeout=60)
    if response.returncode:
        raise RuntimeError(response.stderr.decode('utf-8','replace'))
    result = json.loads(response.stdout)
    if result.get('errors'):
        raise RuntimeError(result['errors'])
    data = result['data']
assert data['user']['login'].lower() == login.lower()
repos = data['user']['repositories']
assert not repos['pageInfo']['hasNextPage'], 'Add pagination before displaying more than 100 repositories.'
assert all(not r['isPrivate'] and not r['isFork'] and not r['languages']['pageInfo']['hasNextPage'] for r in repos['nodes'])
contributions = data['user']['contributionsCollection']
assert contributions.get('totalRepositoriesWithContributedCommits',0) <= 100, 'Contribution repository pagination required.'
public_commits = [r for r in contributions['commitContributionsByRepository'] if not r['repository']['isPrivate']]
languages = collections.Counter()
language_colors = {}
for repo in repos['nodes']:
    if repo['name'].lower() == login.lower():
        continue
    for item in repo['languages']['edges']:
        languages[item['node']['name']] += item['size']
        color = item['node']['color'] or '#8b949e'
        assert re.fullmatch(r'#[A-Fa-f0-9]{6}', color)
        language_colors[item['node']['name']] = color
stats = {
    'stars': sum(r['stargazerCount'] for r in repos['nodes']),
    'commits': sum(r['contributions']['totalCount'] for r in public_commits),
    'pullRequests': data['prs']['issueCount'],
    'issues': data['issues']['issueCount'],
    'contributedRepositories': len(public_commits),
}
snapshot = {'login':login,'asOf':now.isoformat(),'period':{'from':contributions['startedAt'],'to':contributions['endedAt']},'stats':stats,'languageBytes':dict(languages),'languageScope':'Non-fork public repositories, excluding the profile repository. GitHub Linguist code bytes.','visibility':'Public data only; private repositories are excluded.'}
(out/'profile-data.json').write_text(json.dumps(snapshot,indent=2)+'\n',encoding='utf-8')
font = 'Segoe UI,Arial,sans-serif'
mono = 'Consolas,Menlo,monospace'
def text(x,y,value,size,color,weight=400,anchor='start',family=font,extra=''):
    return '<text x="%s" y="%s" font-size="%s" fill="%s" font-weight="%s" text-anchor="%s" font-family="%s" %s>%s</text>'%(x,y,size,color,weight,anchor,family,extra,escape(str(value)))
def save(name,width,height,body,css='',title='Halo Moon'):
    content='<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s" role="img" aria-labelledby="title"><title id="title">%s</title>'%(width,height,width,height,escape(title))
    content+=('<style>'+css+'</style>' if css else '')+body+'</svg>\n'
    (out/name).write_bytes(content.encode('utf-8'))
themes={
    'dark':{'bg':'#0D1117','edge':'#303D4B','fg':'#E6EDF3','muted':'#9BAEC0','accent':'#79C9F3','sky1':'#061525','sky2':'#142E45','mist':'#AED9ED','moon':'#E5F5FF'},
    'light':{'bg':'#FFFFFF','edge':'#D0D7DE','fg':'#1F2937','muted':'#52667B','accent':'#0969DA','sky1':'#DCEAF4','sky2':'#F3F7FC','mist':'#709CB8','moon':'#FFFFFF'},
}
intro=profile['introLines']
assert len(intro)==2 and all(len(line)<=32 for line in intro)
for theme,c in themes.items():
    for mobile in (False,True):
        width,height=(440,244) if mobile else (880,230)
        x=26 if mobile else 38
        moon_x=width-54 if mobile else width-93
        moon_y=51 if mobile else 68
        body='<defs><linearGradient id="sky" x1="0" y1="0" x2="1" y2="1"><stop stop-color="'+c['sky1']+'"/><stop offset="1" stop-color="'+c['sky2']+'"/></linearGradient><clipPath id="bounds"><rect width="'+str(width)+'" height="'+str(height)+'" rx="9"/></clipPath></defs>'
        body+='<rect x=".5" y=".5" width="'+str(width-1)+'" height="'+str(height-1)+'" rx="9" fill="url(#sky)" stroke="'+c['edge']+'"/>'
        body+='<g clip-path="url(#bounds)"><g class="moon">'
        for r,opacity in [(48,'.035'),(38,'.06'),(27,'.1'),(20,'.93')]:
            body+='<circle cx="'+str(moon_x)+'" cy="'+str(moon_y)+'" r="'+str(r)+'" fill="'+c['moon']+'" opacity="'+opacity+'"/>'
        body+='</g>'
        for sx,sy,r in [(width*.58,29,1),(width*.69,95,1.2),(width*.92,113,.8),(width*.48,60,.7),(width*.76,24,.8)]:
            body+='<circle cx="'+str(sx)+'" cy="'+str(sy)+'" r="'+str(r)+'" fill="'+c['moon']+'" opacity=".45"/>'
        for index,offset in [(1,0),(2,26)]:
            y=height-43+offset
            body+='<path class="mist mist'+str(index)+'" d="M-100 '+str(y)+' Q100 '+str(y-46)+' 300 '+str(y)+' T700 '+str(y)+' T1100 '+str(y)+' V'+str(height+60)+' H-100Z" fill="'+c['mist']+'" opacity="'+('.07' if index==1 else '.1')+'"/>'
        body+='</g>'
        body+=text(x,31,login.upper(),10,c['muted'],500,family=mono)
        body+=text(x,83 if mobile else 87,"Hi, I'm "+profile['name'],29 if mobile else 39,c['fg'],650)
        css='@keyframes drift{to{transform:translateX(32px)}}@keyframes glow{to{opacity:.72}}.mist1{animation:drift 18s ease-in-out infinite alternate}.mist2{animation:drift 25s ease-in-out infinite alternate-reverse}.moon{animation:glow 7s ease-in-out infinite alternate}'
        size=21 if mobile else 25
        unit=12 if mobile else 14.5
        for index,line in enumerate(intro):
            y=(129 if mobile else 135)+index*37
            length=len(line)*unit
            duration=1.8 if index==0 else 2.2
            delay=0 if index==0 else 1.8
            body+='<g transform="translate('+str(x)+','+str(y)+')"><g class="typed line'+str(index)+'">'+text(0,0,line,size,c['accent'],500,family=mono,extra='textLength="'+str(length)+'" lengthAdjust="spacingAndGlyphs"')+'</g><rect class="caret caret'+str(index)+'" x="0" y="-'+str(size-3)+'" width="2" height="'+str(size+2)+'" fill="'+c['accent']+'"/></g>'
            css+='@keyframes type'+str(index)+'{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0)}}@keyframes cursor'+str(index)+'{0%{transform:translateX(0);opacity:1}99.9%{opacity:1}100%{transform:translateX('+str(length)+'px);opacity:0}}.line'+str(index)+'{animation:type'+str(index)+' '+str(duration)+'s steps('+str(len(line))+',end) '+str(delay)+'s both}.caret'+str(index)+'{opacity:0;animation:cursor'+str(index)+' '+str(duration)+'s steps('+str(len(line))+',end) '+str(delay)+'s forwards}'
        body+=text(width-24,height-18,'halomoon.cn',11,c['muted'],400,'end',mono)
        css+='@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.caret{display:none}}'
        suffix=('-mobile' if mobile else '')+'-'+theme+'.svg'
        save('intro-animated'+suffix,width,height,body,css,title='Halo Moon — Embedded Linux, MCU, FreeRTOS, Machine Vision')
        save('intro-static'+suffix,width,height,body,'.caret{display:none}',title='Halo Moon — Embedded Linux, MCU, FreeRTOS, Machine Vision')
    frame='<rect x=".5" y=".5" width="419" height="251" rx="7" fill="'+c['bg']+'" stroke="'+c['edge']+'"/>'
    body=frame+text(22,34,'GitHub activity',20,c['accent'],600)+text(22,54,'Public data · '+now.strftime('%Y-%m-%d'),11,c['muted'])
    rows=[('Stars earned',stats['stars']),('Commits · last 365 days',stats['commits']),('Pull requests',stats['pullRequests']),('Issues opened',stats['issues']),('Contributed repos · 365 days',stats['contributedRepositories'])]
    for i,(label,value) in enumerate(rows):
        body+=text(22,85+i*29,label,14,c['muted'],500)+text(393,85+i*29,format(value,','),17,c['fg'],600,'end')
    body+=text(22,233,'Commits and repositories: past 365 days.',10,c['muted'])
    save('stats-'+theme+'.svg',420,252,body,title=login+' public GitHub activity')
    body=frame+text(22,34,'Most used languages',20,c['accent'],600)+text(22,54,'Original public repositories · code size',11,c['muted'])
    total=sum(languages.values())
    entries=languages.most_common()
    if len(entries)>6:entries=entries[:5]+[('Other',sum(v for _,v in entries[5:]))]
    left=22
    body+='<defs><clipPath id="bar"><rect x="22" y="73" width="376" height="10" rx="5"/></clipPath></defs><g clip-path="url(#bar)">'
    for lang,count in entries:
        amount=376*count/total
        color=language_colors.get(lang,'#8B949E')
        body+='<rect x="'+str(left)+'" y="73" width="'+str(amount)+'" height="10" fill="'+color+'"/>'
        left+=amount
    body+='</g>'
    for i,(lang,count) in enumerate(entries):
        x=27+(i%2)*193;y=113+(i//2)*32
        body+='<circle cx="'+str(x)+'" cy="'+str(y-4)+'" r="4" fill="'+language_colors.get(lang,'#8B949E')+'"/>'
        body+=text(x+11,y,lang+' '+format(100*count/total,'.1f')+'%',13,c['fg'])
    if not entries:body+=text(22,118,'No public language data yet.',14,c['muted'])
    body+=text(22,218,'Forks and this profile repository excluded.',10,c['muted'])+text(22,234,'Updated '+now.strftime('%Y-%m-%d')+' UTC',10,c['muted'])
    save('languages-'+theme+'.svg',420,252,body,title='Language share by GitHub Linguist code bytes')
print(json.dumps({'account':login,'stats':stats,'languages':dict(languages),'assets':len(list(out.glob('*.svg'))),'publicOnly':True}))
