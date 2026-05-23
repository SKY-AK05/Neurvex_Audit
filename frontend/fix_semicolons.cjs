const fs = require('fs');
const path = require('path');

function walk(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat && stat.isDirectory()) results = results.concat(walk(fullPath));
    else if (file.endsWith('.vue')) results.push(fullPath);
  });
  return results;
}

const files = walk('./src');
let totalFixed = 0;

files.forEach(f => {
  let content = fs.readFileSync(f, 'utf8');
  const before = content;

  // Fix: var(--c-xxx)) <space> next-css-property: (same line, missing semicolon)
  content = content.replace(/(var\(--c-[a-z-]+\)) ([a-z-]+ *:)/g, '$1; $2');

  // Fix: var(--c-xxx)) at end of line (before \r\n or \n) with no semicolon
  content = content.replace(/(var\(--c-[a-z-]+\))\r?\n/g, '$1;\n');

  // Fix: var(--c-xxx)) } missing semicolon before closing brace
  content = content.replace(/(var\(--c-[a-z-]+\)) \}/g, '$1; }');
  content = content.replace(/(var\(--c-[a-z-]+\))\}/g, '$1; }');

  if (content !== before) {
    fs.writeFileSync(f, content);
    totalFixed++;
    console.log('Fixed: ' + path.basename(f));
  }
});
console.log('\nDone. Fixed ' + totalFixed + ' file(s).');
