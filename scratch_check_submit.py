with open('app/api/routes.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find("router.post('/submit'")
if idx == -1:
    idx = text.find('router.post("/submit"')
if idx == -1:
    idx = text.find('submit')

print("Found at:", idx)
print(text[idx:idx+2500])
