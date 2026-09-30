import xml.etree.ElementTree as ET

with open('ui_dump_full.txt', 'rb') as f:
    data = f.read()
text = data.decode('utf-16')

tree = ET.fromstring(text)

# Print ALL node texts and resource-ids (including empty)
def print_nodes(node, depth=0):
    t = node.get('text', '') or ''
    rid = node.get('resource-id', '') or ''
    cls = node.get('class', '') or ''
    bounds = node.get('bounds', '') or ''
    print(f'{"  " * depth}text: {repr(t[:30])} | id: {rid[:40]} | cls: {cls[:30]} | bounds: {bounds}')
    for child in node:
        print_nodes(child, depth+1)

print_nodes(tree)