"""Remove active/external SVG content before any recovered vector is published."""
from xml.etree import ElementTree as ET
import re

ALLOWED={'svg','g','path','rect','circle','ellipse','polygon','polyline','line','text','tspan','defs','use','clipPath','mask','linearGradient','radialGradient','stop','symbol','title','desc','pattern'}
STANDARD_SVG11_DOCTYPE=re.compile(
    br'<!\s*DOCTYPE\s+svg\s+PUBLIC\s+([\'\"])-//W3C//DTD SVG 1\.1//EN\1\s+'
    br'([\'\"])http://www\.w3\.org/Graphics/SVG/1\.1/DTD/svg11\.dtd\2\s*>',re.I)

def sanitize_svg(body: bytes) -> bytes:
    # Many original SVG 1.1 assets carry this external W3C declaration. Strip
    # only the known declaration; never resolve it, and continue rejecting all
    # entity declarations and nonstandard doctypes below.
    body=STANDARD_SVG11_DOCTYPE.sub(b'',body)
    if re.search(br'<!\s*(DOCTYPE|ENTITY)',body,re.I):
        raise ValueError('SVG document declarations are not allowed')
    try: root=ET.fromstring(body)
    except ET.ParseError as e: raise ValueError('Invalid SVG') from e
    if root.tag.split('}')[-1]!='svg': raise ValueError('Not an SVG')
    def clean(node):
        for child in list(node):
            if child.tag.split('}')[-1] not in ALLOWED: node.remove(child)
            else: clean(child)
        for key,value in list(node.attrib.items()):
            name=key.split('}')[-1].lower()
            unsafe=(name.startswith('on') or name in ('style','src','base') or
                    (name=='href' and not value.startswith('#')) or
                    ('url(' in value.lower() and not re.fullmatch(r'url\(\s*[\'"]?#[\w.-]+[\'"]?\s*\)',value,re.I)))
            if unsafe: del node.attrib[key]
    clean(root)
    ET.register_namespace('','http://www.w3.org/2000/svg')
    return ET.tostring(root,encoding='utf-8')
