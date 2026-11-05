# editor-esp · instrucciones para el asistente

Este archivo lo leen Codex y otros asistentes que abren esta carpeta. Claude Code usa las mismas instrucciones como conector.

**Si la persona quiere editar un vídeo, instalar editor-esp («instala editor-esp»), comprobarlo o hacer cualquier cosa con editor-esp:** lee entero `skills/editor-esp/SKILL.md` y síguelo. Las órdenes se ejecutan desde esta carpeta, con `.venv/bin/python tallat.py …` (en Windows, `.venv\Scripts\python.exe tallat.py …`). Si `.venv` no está, primero hace falta `./prepara.sh` (en Windows, `powershell -ExecutionPolicy Bypass -File prepara.ps1`).

**Permisos.** Las órdenes de editor-esp necesitan internet (instalar, dibujar los subtítulos) y escribir fuera de esta carpeta: en `~/.tallat-es` y en la carpeta de cada proyecto, donde están los vídeos de la persona. Si trabajas en un entorno protegido (sandbox), pide permiso para ejecutarlas fuera, explicándole por qué en una frase.

**La página de revisión** (`tallat.py revisa`) tiene que quedar encendida mientras la persona trabaja: lánzala en segundo plano (por ejemplo, `nohup .venv/bin/python tallat.py revisa --projecte CARPETA > ~/.tallat-es/revisa.log 2>&1 &`; en Windows, en PowerShell y con la carpeta del proyecto entre comillas dobles dentro de las simples para que los espacios no la partan: `Start-Process -WindowStyle Hidden -WorkingDirectory . -FilePath .venv\Scripts\python.exe -ArgumentList 'tallat.py revisa --sense-navegador --projecte "C:\ruta\de la carpeta"' -RedirectStandardOutput $env:USERPROFILE\.tallat-es\revisa.log -RedirectStandardError $env:USERPROFILE\.tallat-es\revisa-errors.log`), comprueba que responde en http://127.0.0.1:8766/ y dale esta dirección.

Habla siempre en castellano sencillo: la mayoría de personas que usan editor-esp no son programadoras. Antes de mover o borrar nada suyo, pregúntalo. Antes de gastar créditos de una IA de pago, di qué modelo usarás y espera a que lo confirme.

**Si la persona quiere cambiar el código de editor-esp**, sigue las reglas del proyecto ([CLAUDE.md](CLAUDE.md)). Las pruebas: `.venv/bin/python -m unittest discover -s proves -t .`
