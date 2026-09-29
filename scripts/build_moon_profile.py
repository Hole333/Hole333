import json,re
from pathlib import Path
from xml.sax.saxutils import escape
root=Path(__file__).resolve().parents[1];out=root/'assets/moon';out.mkdir(parents=True,exist_ok=True)
profile=json.loads((root/'profile.json').read_text(encoding='utf-8'))
font="'Segoe UI','Microsoft YaHei','Noto Sans CJK SC',Arial,sans-serif"
def text(x,y,value,size=14,color='#E1F3FF',weight=400,anchor='start'):
    return '<text x="'+str(x)+'" y="'+str(y)+'" text-anchor="'+anchor+'" font-family="'+font+'" font-size="'+str(size)+'" font-weight="'+str(weight)+'" fill="'+color+'">'+escape(value)+'</text>'
def save(name,width,height,body,title):
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="'+str(width)+'" height="'+str(height)+'" viewBox="0 0 '+str(width)+' '+str(height)+'" role="img" aria-labelledby="title"><title id="title">'+escape(title)+'</title>'+body+'</svg>\n'
    (out/name).write_bytes(svg.encode())
for key,label in [('blog','个人博客'),('notes','学习笔记'),('repos','全部仓库')]:
    body='<rect x=".5" y=".5" width="127" height="33" rx="7" fill="#052033" stroke="#345467"/>'+text(64,23,label,14,'#E1F3FF',500,'middle')
    save(key+'.svg',128,34,body,label)
for p in profile['projects']:
    assert re.fullmatch(r'[A-Za-z0-9_.-]+',p['repo']) and p['repo'] not in ('.','..')
    body='<rect x="1" y="1" width="418" height="130" rx="9" fill="#052033" stroke="#294A5D"/>'
    body+=text(24,29,p['repo'],11,'#8DB2C7')+text(24,64,p['label'],21,'#F5FBFF',600)+text(24,99,p['description'],14,'#B8D2E1')
    body+='<path d="m382 49 7 7-7 7m-6-7h13" fill="none" stroke="#B6EDFF" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
    save(p['repo']+'.svg',420,132,body,p['label'])
print('Built nine static moon-palette navigation and project graphics; no statistics or template components.')
