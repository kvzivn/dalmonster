"""Losslessly pack embedded scene textures for the 25 MiB static hosting limit.

Requires Pillow. Geometry and decoded texture pixels are preserved exactly.
Run after rebuilding either source scene in Blender.
"""
from pathlib import Path
from PIL import Image
import io
import json
import struct

ROOT = Path(__file__).resolve().parents[1] / 'public' / 'assets'
for original, target in [('environment-final', 'environment-web'), ('architecture-weathered', 'architecture-web')]:
    source = (ROOT / f'{original}.glb').read_bytes()
    json_length = struct.unpack_from('<I', source, 12)[0]
    document = json.loads(source[20:20 + json_length])
    binary = source[28 + json_length:]
    replacements = {}
    converted = set()
    for index, image in enumerate(document.get('images', [])):
        view_index = image['bufferView']
        view = document['bufferViews'][view_index]
        start = view.get('byteOffset', 0)
        old = binary[start:start + view['byteLength']]
        pixels = Image.open(io.BytesIO(old)).convert('RGBA')
        output = io.BytesIO()
        pixels.save(output, 'WEBP', lossless=True, exact=True, method=6)
        encoded = output.getvalue()
        assert pixels.tobytes() == Image.open(io.BytesIO(encoded)).convert('RGBA').tobytes()
        if len(encoded) < len(old):
            replacements[view_index] = encoded
            image['mimeType'] = 'image/webp'
            converted.add(index)
    packed = bytearray()
    for index, view in enumerate(document['bufferViews']):
        start = view.get('byteOffset', 0)
        old = binary[start:start + view['byteLength']]
        data = replacements.get(index, old)
        packed.extend(b'\0' * (-len(packed) % 4))
        view['byteOffset'] = len(packed)
        view['byteLength'] = len(data)
        packed.extend(data)
        if index not in replacements:
            assert packed[view['byteOffset']:view['byteOffset'] + len(old)] == old
    for texture in document.get('textures', []):
        if texture.get('source') in converted:
            texture.setdefault('extensions', {})['EXT_texture_webp'] = {'source': texture.pop('source')}
    for field in ['extensionsUsed', 'extensionsRequired']:
        if converted and 'EXT_texture_webp' not in document.setdefault(field, []):
            document[field].append('EXT_texture_webp')
    document['buffers'][0]['byteLength'] = len(packed)
    packed.extend(b'\0' * (-len(packed) % 4))
    encoded_json = json.dumps(document, separators=(',', ':')).encode()
    encoded_json += b' ' * (-len(encoded_json) % 4)
    result = struct.pack('<III', 0x46546C67, 2, 28 + len(encoded_json) + len(packed))
    result += struct.pack('<II', len(encoded_json), 0x4E4F534A) + encoded_json
    result += struct.pack('<II', len(packed), 0x004E4942) + packed
    assert len(result) <= 25 * 1024 * 1024, f'{target} exceeds static hosting file limit'
    (ROOT / f'{target}.glb').write_bytes(result)
    print(f'{target}: {len(source):,} → {len(result):,} bytes; geometry and pixels unchanged')
