#!/usr/bin/env python3
"""Собирает docs/index.html из ulyana.html (артефакт хранит только тело страницы).

Один аргумент — базовый адрес сайта, нужен для абсолютных og:image / og:url.
    python3 build-site.py https://ulyana.example.com
Без аргумента ссылки останутся относительными: превью в мессенджерах
может не подтянуть картинку, всё остальное работает.
"""
import io, re, sys

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else ""
TITLE = "Сто комплиментов Ульяне"
DESC  = "101 комплимент для Ульяны, Ули, Ульяши, любимой и солнышка."
ICON  = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
         '<rect width="32" height="32" rx="7" fill="%23050505"/>'
         '<circle cx="16" cy="16" r="9" fill="%23ff7a9c" opacity="0.28"/>'
         '<circle cx="16" cy="16" r="5" fill="%23ff7a9c"/></svg>')

src = io.open("ulyana.html", encoding="utf-8").read()
m = re.match(r'\s*<title>.*?</title>\s*\n((?:\s*<link[^>]*fonts\.googleapis[^>]*>\s*\n)+)',
             src, flags=re.S)
if not m:
    sys.exit("не нашёл <title>/<link> в ulyana.html — проверь начало файла")
FONTS = m.group(1).strip()  # все подряд идущие подключения шрифтов из исходника, не дублируем
body = src[m.end():]

# страховка: слоты обращения должны быть корректными, иначе на сайте вылезет «{имя: …}»
forms_m  = re.search(r'const FORMS = \[(.*?)\];', body)
dative_m = re.search(r'const DATIVE = \{(.*?)\};', body)
lines_m  = re.search(r'const LINES = `\n(.*?)\n`\.trim', body, re.S)
if not (forms_m and dative_m and lines_m):
    sys.exit("не нашёл FORMS, DATIVE или LINES в ulyana.html")
FORMS = re.findall(r'"([^"]+)"', forms_m.group(1))
errors = []
if set(re.findall(r'"([^"]+)":', dative_m.group(1))) != set(FORMS):
    errors.append("DATIVE и FORMS перечисляют разные формы")
for n, line in enumerate(lines_m.group(1).split("\n"), 1):
    slots = re.findall(r'\{([^}]*)\}', line)
    for sl in slots:
        if not re.fullmatch(r'имя(:.*)?', sl):
            errors.append(f"строка {n}: непонятный слот {{{sl}}}")
    named = [sl for sl in slots if sl.startswith("имя")]
    if len(named) > 1:
        errors.append(f"строка {n}: больше одного слота")
    for sl in named:
        if ":" in sl:
            only = [f.strip() for f in sl.split(":", 1)[1].split(",") if f.strip()]
            unknown = [f for f in only if f not in FORMS]
            if unknown:
                errors.append(f"строка {n}: неизвестные формы {unknown}")
            if len(only) < 2:
                errors.append(f"строка {n}: в ограничении меньше двух форм")
if errors:
    sys.exit("ошибки в слотах обращения:\n  " + "\n  ".join(errors))

img = f"{BASE}/og.png" if BASE else "og.png"
url = f"{BASE}/" if BASE else ""

head = f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<meta name="theme-color" content="#050505">

<meta property="og:type" content="website">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="ru_RU">
{f'<meta property="og:url" content="{url}">' if url else "<!-- og:url появится, когда будет известен адрес -->"}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="{img}">

<link rel="icon" href='data:image/svg+xml,{ICON}'>
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{FONTS}
</head>
<body>
'''

out = head + body.strip() + "\n</body>\n</html>\n"

# страховка: подключение шрифтов должно попасть в сборку ровно одно и то же
src_fonts = set(re.findall(r'family=([^&"\']+)', FONTS))
out_fonts = set(re.findall(r'family=([^&"\']+)', out))
if src_fonts != out_fonts:
    sys.exit(f"шрифты разошлись: в исходнике {src_fonts}, в сборке {out_fonts}")

io.open("docs/index.html", "w", encoding="utf-8").write(out)
print(f"docs/index.html собран" + (f" для {BASE}" if BASE else " с относительными ссылками"))
