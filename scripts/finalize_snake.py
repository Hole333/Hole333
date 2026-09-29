import argparse
import copy
from pathlib import Path
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument('directory')
args = parser.parse_args()
directory = Path(args.directory)
ns = 'http://www.w3.org/2000/svg'
ET.register_namespace('', ns)
for theme in ('light', 'dark'):
    path = directory / ('snake-' + theme + '.svg')
    root = ET.fromstring(path.read_bytes())
    assert root.tag == '{' + ns + '}svg'
    assert not any(el.tag.split('}')[-1] in ('script', 'foreignObject', 'image') for el in root.iter())
    for el in list(root):
        if el.tag == '{' + ns + '}style' and 'prefers-reduced-motion' in (el.text or ''):
            root.remove(el)
    reduced = ET.SubElement(root, '{' + ns + '}style')
    reduced.text = '@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}'
    path.write_bytes(ET.tostring(root, encoding='utf-8', xml_declaration=True))
    static = copy.deepcopy(root)
    style = ET.SubElement(static, '{' + ns + '}style')
    style.text = '*{animation:none!important;transition:none!important}'
    (directory / ('activity-static-' + theme + '.svg')).write_bytes(ET.tostring(static, encoding='utf-8', xml_declaration=True))
print('Verified contribution SVGs and reduced-motion variants.')
