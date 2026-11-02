import sys

with open('frontend/src/utils/defaultSections.js', 'r', encoding='utf-8') as f:
    text = f.read()

sys.stdout.buffer.write(text[:1500].encode('utf-8'))