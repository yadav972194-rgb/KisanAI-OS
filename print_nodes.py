import xml.etree.ElementTree as ET

with open('ui_dump_full.txt', 'rb') as f:
    data = f.read()
text = data.decode('utf-16')

tree = ET.fromstring(text)

# Print all node texts and resource-ids
def print_nodes(node, depth=0):
    t = node.get('text', '') or ''
    rid = node.get('resource-id', '') or ''
    cls = node.get('class', '') or ''
    bounds = node.get('bounds', '') or ''
    if t.strip():
        print(f'{"  " * depth}text: {t[:60]} | id: {rid[:60]} | cls: {cls[:30]} | bounds: {bounds}')
    for child in node:
        print_nodes(child, depth+1)

print_nodes(tree)