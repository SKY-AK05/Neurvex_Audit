with open('app/api/routes.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('router.post("/submit"')
print(text[idx+2000:idx+5500])
