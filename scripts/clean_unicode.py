"""Clean unicode corruption from REB TXT files IN-PLACE."""
import re
from pathlib import Path

REB_DIR = Path(r'C:\Users\KAREGEYA JUSTIN\Documents\Codex\Rahura Ai Rina 1.0 - Copy (3) - Copy\data\reb_books')

REPLACE = {
    '\u2013': '-',      '\u2014': '-',      '\u2015': '-',
    '\u2018': "'",      '\u2019': "'",
    '\u201c': '"',      '\u201d': '"',      '\u201e': '"',
    '\u2026': '...',    '\u2022': '-',
    '\u2032': "'",      '\u2033': '"',
    '\u00a0': ' ',      '\u00ad': '',
    '\u00d7': 'x',      '\u00f7': '/',
    '\uf0b7': '-',      '\uf020': ' ',      '\uf0a7': '',
    '\ue001': '',
}

for txt in sorted(REB_DIR.glob('*.txt')):
    raw = txt.read_bytes()
    text = raw.decode('utf-8', errors='replace')
    for old, new in REPLACE.items():
        text = text.replace(old, new)
    text = re.sub(r'[\u0000-\u0008\u000b\u000c\u000e-\u001f\ufffd\u200b\ufeff]', '', text)
    txt.write_text(text, encoding='utf-8')
    print(f'{txt.name}: {len(raw)} -> {len(text.encode())} bytes')
print('Done.')
