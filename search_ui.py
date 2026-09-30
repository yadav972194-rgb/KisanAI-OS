import xml.etree.ElementTree as ET
import re

with open('ui_dump_full.txt', 'rb') as f:
    data = f.read()
text = data.decode('utf-16')

tree = ET.fromstring(text)

def find_nodes(node, pattern, results=None):
    if results is None:
        results = []
    t = node.get('text', '') or ''
    rid = node.get('resource-id', '') or ''
    if t and pattern.search(t):
        results.append((t, rid, node.get('class', ''), node.get('bounds', '')))
    for child in node:
        find_nodes(child, pattern, results)
    return results

pattern = re.compile('farm|create|location|country|district|tehsil|village|select|dropdown', re.I)
matches = find_nodes(tree, pattern)

print(f'Found {len(matches)} matches:')
for m in matches:
    print(f'  text: {m[0][:80] if m[0] else ""} | id: {m[1][:80] if m[1] else ""} | class: {m[2][:40]} | bounds: {m[3]}')