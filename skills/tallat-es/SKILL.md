---
name: tallat-es
description: Editor de reels en castellano, por palabras (versión en castellano de tallat). Úsala cuando alguien quiera editar un vídeo de cabeza parlante (talking head) en castellano con tallat-es, quitar las muletillas, hacer el primer montaje de una grabación larga (proponer reels), revisarlo en la página de revisión o exportarlo en vertical 9:16. Para vídeos en catalán, usa tallat.
---

# tallat-es

Todo en castellano, con palabras sencillas: la mayoría de personas que lo usan no son programadoras.

Esta es la versión en castellano (modificada) de **tallat**, de Ivet Anoro (AGPL-3.0-or-later). Si la persona tiene también tallat en catalán, esta es la de los vídeos en castellano.

Estas instrucciones sirven para cualquier asistente que pueda usar el terminal (Claude Code, Codex…): donde dice «el asistente», eres tú.

**Nombres internos en catalán.** Las órdenes (`transcriu`, `revisa`, `exporta`…), las claves de los JSON y los valores (`pocs`, `molts`, `dalt`, `baix`, `talla`, `si`, `potser`…) siguen en catalán, como en tallat: escríbelos tal cual. A la persona, háblale siempre en castellano y con los nombres que ve en la página.

## Cómo hablas con la persona

La mayoría no son programadoras y quieren que sea fácil. **Guíala paso a paso:**
- **Mensajes cortos.** Como mucho 4-6 líneas. Si tienes más cosas que decir, di la más importante y pregunta si quiere el resto.
- **Un paso cada vez.** Di qué has hecho, qué tiene que hacer ella ahora (una sola cosa) y qué vendrá después.
- **Negritas** para lo que tiene que hacer o mirar («Haz clic en **Exporta**», «en **Viste**, toca **Subtítulos**»), y **listas** cuando hay más de una cosa. Nada de párrafos largos.
- **Nada de tecnicismos:** ni órdenes, ni nombres de archivos internos, ni código, si no los pide. «He cortado los silencios largos», no «he ejecutado neteja con pausa 0,35».
- **Cuando elija,** dale 2-4 opciones concretas (con botones si el asistente los tiene) y recomienda una.
- **Palabras:** a la persona, dile **tu estilo** (los colores, las letras y cómo son sus vídeos), nunca «marca» ni «kit»: la mayoría no tienen una marca, tienen un estilo. Si tiene varios, «tus estilos».
- **En los trabajos largos** (transcribir, exportar), avisa antes de cuánto tardará y ve diciéndole cómo va. Cuando acabe, dile claramente que ha acabado y dónde está el resultado.

**Dónde funciona:** en el ordenador de la persona (un Mac o un Windows; en Windows, todavía en pruebas), desde la pestaña Code de la app de Claude o desde Codex. Si te encuentras en un entorno que no es su ordenador (un contenedor en la nube, sin `~/.tallat-es` ni su `$HOME`, con internet limitado, o el chat normal o Cowork), no improvises la edición por tu cuenta: dile que abra tallat-es en la pestaña **Code** de la app de Claude en su Mac (o con Codex) y que escriba «instala tallat-es».

## Instalación (la primera vez)

Cuando la persona diga «instala tallat-es», o una orden falle porque falta una herramienta (ffmpeg, WhisperX, Node…):
1. Explícale en una frase qué pasará: se descargan unos 2-3 GB (ffmpeg, Node, Python, WhisperX, el navegador de HyperFrames y el modelo de voz en castellano), tarda 10-20 minutos, todo va a su carpeta de usuario (`~/.tallat-es`) y nunca pide la contraseña. Si ya usa tallat en catalán, sus estilos se copian solos.
2. Si no usa Descript para transcribir, añade `--amb-whisper` (descarga 3 GB más, el modelo de transcripción).
3. Ejecuta `./prepara.sh` desde la carpeta de tallat-es (en **Windows**: `powershell -ExecutionPolicy Bypass -File prepara.ps1`, y `-AmbWhisper` en lugar de `--amb-whisper`). Es largo: hazlo en una pestaña del terminal donde la persona lo vea, o en segundo plano, y ve diciéndole cómo va. Se puede volver a ejecutar sin miedo: solo hace lo que falta.
4. Al acabar, el instalador mismo ejecuta `tallat.py comprova`. Si hay alguna ✗, lee el mensaje, vuelve a ejecutar el instalador y, si sigue, explícale qué pasa con palabras sencillas.

**Actualizar:** tallat-es es una copia personal (un conector local). Si cambia la carpeta, `/plugin marketplace update tallat-es` y después una sesión nueva. Después, si `.venv` no está, el instalador solo rehace el enlace.

`tallat.py comprova` revisa en cualquier momento que todo esté (✓ bien, ! aviso, ✗ hay que arreglar). Descript es opcional: se conecta desde la configuración de conectores del asistente (en Claude, la de claude.ai).

## Órdenes

Desde la carpeta de tallat-es: la que contiene `tallat.py`, dos carpetas por encima de este `SKILL.md` (si se ha instalado como conector, es la carpeta del conector; en Claude Code, `${CLAUDE_PLUGIN_ROOT}`), con el entorno `.venv`. Si `.venv` no está (la primera vez, o después de actualizar el conector), ejecuta el instalador: si ya está todo instalado, solo rehace el enlace y tarda unos segundos. **En Windows**, en todas las órdenes de aquí abajo, en lugar de `.venv/bin/python` escribe `.venv/Scripts/python.exe` (con barras «/» funciona tanto en PowerShell como en el Git Bash de Claude Code).

```bash
.venv/bin/python tallat.py transcriu VIDEO --projecte CARPETA [--srt ARCHIVO.srt]
.venv/bin/python tallat.py revisa --projecte CARPETA
.venv/bin/python tallat.py guio --projecte CARPETA
.venv/bin/python tallat.py reels --projecte CARPETA
.venv/bin/python tallat.py reel ID --projecte CARPETA
.venv/bin/python tallat.py exporta --projecte CARPETA [--qualitat esborrany|1080|4k] [--sense-subtitols]
.venv/bin/python tallat.py editors --projecte CARPETA [--amb-subtitols] [--trossos]
.venv/bin/python tallat.py gust [afegeix SECCIO "TEXTO" [--ajust clau=valor] | treu NUMERO]
.venv/bin/python tallat.py moment SEGUNDOS --projecte CARPETA [--esborrany]
.venv/bin/python tallat.py kit [nou NOMBRE [--copia-de ID] | nom ID NOMBRE | per-defecte ID | tria ID --projecte CARPETA | exporta ID [--a CARPETA] | importa ARCHIVO.zip | esborra ID | lletres | lletra ID [--kit KIT]]
.venv/bin/python tallat.py destaca --projecte CARPETA [--si ID…] [--no ID…] [--automatic]
.venv/bin/python tallat.py titol --projecte CARPETA ["LÍNEA | *DESTACADO* | LÍNEA"] [--durada S] [--treu]
.venv/bin/python tallat.py marca [--projecte CARPETA | --kit ID] [CLAU=VALOR …]
.venv/bin/python tallat.py grafics --projecte CARPETA [--json]
.venv/bin/python tallat.py grafics proposa|canvia PLAN.json --projecte CARPETA [--de-nou]
.venv/bin/python tallat.py grafics fotogrames --projecte CARPETA
.venv/bin/python tallat.py notes --projecte CARPETA [--espera [--minuts 60] | --respon NÚMERO "TEXTO" [--pregunta | --al-xat]]
```

La carpeta del proyecto tiene que estar **fuera del repositorio** (los vídeos y lo que dice la persona no se publican nunca). La página de revisión de tallat-es usa el puerto 8766 (la de tallat en catalán, el 8765): se pueden tener las dos abiertas.

## Tu estilo (la entrevista de marca)

La marca dice cómo son los vídeos de la persona: sus colores y letras (cada uno con un trabajo) y cuántos gráficos quiere. Vive en el kit (sección `marca`), y al guardarla los colores y las letras se reparten solos: el **texto** en el texto de los subtítulos y del título, el **oscuro** (en lugar del negro) en los contornos y las sombras, el **destacado** en la palabra que suena y en las destacadas (subtítulos y título; si no hay, el del texto), el **principal** en los bordes del b-roll y en los gráficos (etiquetas, listas, la llamada), el **secundario** y el **claro** en los gráficos (notas, cintas, tarjetas), la letra de **texto** en los subtítulos, la de **títulos** en el título gancho, la de **acento** en las palabras destacadas, en cursiva, y la de **mano** en las notas y anotaciones de los gráficos y en el estilo scrapbook (si no hay, la de acento). Los estilos hechos de la página respetan sus colores.

**Primero, en la página.** Los colores y las letras se hacen en la página de revisión, en 2 pasos visuales (en **Viste**, la fila **Colores y letras**; también se ofrece solo en el panel Subtítulos). **No la pongas antes del primer vídeo:** que la persona empiece a editar enseguida. Cuando llegue a los subtítulos o a los gráficos, o si dice «quiero mis colores», dile que toque **Colores y letras** en la página (en **Viste**).

**En la página ya no están** la llamada a la acción, el estilo de los gráficos (cada uno lo elige en cada gráfico, en Viste), la letra a mano ni los colores o estilos que no quiere nunca (sobraban). No los preguntes. Si la persona te habla de ellos (una llamada que usa siempre, su letra a mano hecha fuente), guárdalo desde el chat (`crida=…`, `lletra_ma=…`, `energia=…`): se usa igual.

**La entrevista en el chat es opcional.** Hazla si la persona la pide («hagamos mi estilo», «quiero mis colores») o si quiere que la ayudes a decidir. Si ya tiene los colores y las letras de la página, sáltate estas preguntas. **No le preguntes de qué va su cuenta ni quién la mira:** puede parecer que te metes, y el tema ya lo sabes por lo que dice en los vídeos. Si te lo cuenta ella, apúntalo (`compte`, `public`) y úsalo para los títulos y los gráficos.

**Cómo:** en el chat, **una pregunta cada vez** (si en una respuesta ha contestado varias, no las vuelvas a hacer: resume lo que has entendido y pasa a la siguiente que falte), con palabras sencillas y 2-4 opciones concretas cuando se pueda (más «otra cosa»). Si dice «no lo sé», propónle tú una opción a partir de lo que ya te ha dicho y sigue. Las preguntas:
1. **Enséñame un reel que te habría gustado hacer** (un enlace o una captura). Es la pregunta más importante: míralo (si es un enlace, ábrelo en el navegador; si no lo puedes ver, pide una captura) y saca los colores, cómo son los subtítulos, los gráficos y el ritmo. Pregúntale qué le gusta.
2. Tus colores (códigos como #FF7DB8 o en palabras: «rosa suave y negro»). ¿Cuál va en el texto encima del vídeo? ¿Cuál es el principal, y cuál destaca las palabras clave (o ninguno: van del color del texto)? ¿Uno claro para fondos y uno oscuro para sombras? (Si la persona tiene una guía de marca, pídesela: o te la pega o te dice explícitamente dónde leerla.)
3. Letras: para los títulos, para el texto y una de acento para la palabra emotiva (una con cursiva queda muy bien). Si tiene propias (archivos .ttf, .otf…), añádelas al kit con `tallat.py kit font ARCHIVO --kit ID [--familia NOMBRE]` (el grosor y la cursiva se deducen del nombre del archivo) y recuérdale que, si pasa el kit a alguien, tiene que mirar si la licencia lo permite. Si no tiene, propónle 2-3 combinaciones de la biblioteca gratuita (`tallat.py kit lletres`; las que tienen cursiva: Inter, Inter Tight, Archivo, Montserrat, Poppins, DM Sans, Fraunces, Playfair Display, DM Serif Display, Instrument Serif). Por ejemplo: DM Sans + Fraunces + Instrument Serif (editorial), Poppins + Poppins + Playfair Display (limpio y cálido), Archivo + Anton + Instrument Serif (impacto).
4. Los subtítulos: ¿de una palabra, frases cortas o la frase entera? ¿Con las palabras clave más grandes? ¿En minúsculas? (Elige el estilo hecho que encaje y ponlo con la página o en el `kit.json`.)
5. Cuántos gráficos: pocos (uno cada 8-12 s, sobre todo tú a cámara), normal (cada 4-6 s) o muchos (cada 2-4 s).
6. Efectos de sonido: ninguno, pocos o muchos.
7. El ritmo de los cortes: natural, ágil o rápido (`talls.pausa_maxima` 0,5 / 0,35 / 0,25).

**Al acabar:** enséñale un resumen corto y pregunta «¿cambiarías algo?». Después:
- Guárdalo: `tallat.py marca --projecte X referencia="…" color_text=#… color_principal=#… color_destacat=#… color_secundari=#… color_clar=#… color_fosc=#… lletra_titols=… lletra_text=… lletra_accent=… grafics=pocs|normal|molts`. Las letras de la biblioteca se pueden decir por el nombre o por el id y se descargan solas (con la cursiva).
- Si quiere un kit nuevo para la marca, créalo antes (`tallat.py kit nou "Mi marca"` y `kit tria`).
- El resto (subtítulos, sonido, ritmo), en sus apartados del kit. Cada «no quiero nunca…» que diga, como regla del gusto (`tallat.py gust afegeix`).
- Ábrele la página (`tallat.py revisa`) para que lo vea: en **Viste**, la fila **Colores y letras** lo enseña y lo deja retocar.

**Después:** cuando hagas el montaje o propongas títulos y gráficos, lee la marca (`tallat.py marca --projecte X`) y úsala: la cuenta y el público para el tono y la cantidad para los gráficos (y, si tiene, su llamada a la acción al final). Si la marca y tu gusto no coinciden, manda la marca.

## Transcribir

- **Con Descript** (mejor texto, conserva las muletillas): importa el audio a la cuenta de la persona con el conector de Descript (proyecto privado, idioma `es`), exporta la transcripción en SRT, guárdala en la carpeta del proyecto y ejecuta `transcriu --srt`. WhisperX solo calcula el tiempo de cada palabra.
- **Sin Descript**: `transcriu` sin `--srt` usa WhisperX entero (en castellano). Es más lento y borra parte de las muletillas; avísalo.
- **El tiempo de cada palabra** lo calcula un modelo de voz en castellano (wav2vec2-large-xlsr-53-spanish, el que ya instala `prepara.sh`; gratuito y sin internet): todo el texto contra todo el sonido, y los bordes de las palabras se recortan a los silencios reales. Es lo que hace que los cortes caigan en su sitio y que los subtítulos vayan a tiempo. No se fía de los tiempos del SRT. Cada palabra se guarda con su confianza; los números y los símbolos no se pueden escuchar y en la página salen subrayados con puntos (tiempo aproximado).
- **Para comparar los tiempos con los de Descript** (p. ej. si la persona dice que un corte suena mal): `tallat.py compara-temps --projecte X --srt archivo.srt`. Dice cuánto se parecen y dónde difieren más; escucha esos puntos para saber cuál acierta. Con un SRT de una palabra por subtítulo se comparan todas las palabras.
- **Si los cortes suenan mal o los subtítulos van a destiempo en un proyecto hecho antes**: `tallat.py realinea --projecte X`. No toca el texto ni la edición; guarda la transcripción de antes al lado. Después, hay que volver a abrir la página de revisión.

## Primer montaje (proponer reels de una grabación larga)

1. Ejecuta `guio` y lee `guio.txt`. Cada línea es un párrafo: `[P número · inicio–final · palabras primera–última] texto`.
2. Si hay que elegir palabras sueltas, consulta los ids en `transcripcio.json` (`paraules[i].id`, `text`).
3. Escribe `reels.json` en la carpeta del proyecto:

```json
{
  "reels": [
    {
      "id": "nombre-corto",
      "titol": "Título en castellano",
      "ganxo": "La frase exacta con la que empieza",
      "per_que": "Una o dos frases: por qué funciona solo y qué tomas has elegido",
      "paraules": [[0, 9], [446, 461], [463, 481]]
    }
  ]
}
```

   - `paraules` son trozos de ids **incluidos los extremos**, **en el orden en que tienen que sonar**. Puedes cambiar el orden de la grabación si el reel lo pide.
4. Ejecuta `reels` para validarlo y ver su duración. Corrige los errores que salgan.
   - En la página de revisión, la persona también puede cambiar el orden de los párrafos arrastrándolos por el asa ⠿ (se guarda en `edicio.json` → `ordre`, igual que el de un reel).
5. La persona los ve en la página de revisión (en el desplegable de la columna izquierda) y elige uno, que se abre ya montado. También se puede crear con `reel ID`.

### Criterios para elegir

- **Se aguanta solo**: se entiende sin haber visto nada más. Si un reel necesita contexto, pon la frase que lo explica o descártalo.
- **Gancho en los primeros 3 segundos**: una pregunta, una afirmación sorprendente o una escena concreta. Si la persona ya ha grabado un gancho, úsalo.
- **Cierra bien**: acaba con una frase de cierre (un remate, un consejo, una conclusión), no a media idea.
- **La mejor toma**: cuando una frase se repite, elige la toma más limpia: sin palabras a medio decir, fluida y, en caso de duda, la última completa. No juntes dos de la misma frase.
- **Ni una palabra inventada**: solo se puede usar lo que se ha dicho; no reescribas el texto.
- **Duración**: normalmente entre 15 y 60 segundos. Si una grabación da para un reel largo y uno corto, propón los dos.
- **Entre 1 y 5 reels** por grabación. Mejor pocos y buenos.
- Deja las muletillas («eh», «mmm», «este») dentro de los trozos: la limpieza automática ya las quita y la persona las puede recuperar.

## Muletillas

- Se quitan solos los sonidos de duda («eh», «ehm», «mmm»…). Se **proponen** (la persona decide en **Edita → Por revisar**) las palabras que a veces son muletilla y a veces no: «este», «o sea», «en plan», «tipo», «vale», «pues», «a ver», «sabes»; y, solo si van seguidas de coma, «bueno,», «entonces,», «nada,», «claro,».
- La lista de la persona está en `~/.tallat-es/farciment.txt` (se crea la primera vez). Para cambiarla, usa las reglas del gusto (`farciment.treu=X`, `farciment.proposa=X`, `farciment.deixa=X`).

## Instrucciones de voz («Claude, …» o «tallat, …»)

- `transcriu` las detecta sola; `instruccions` las vuelve a detectar en un proyecto que ya existe.
- Solo cuentan si la palabra abre una frase (después de un punto o de una pausa). El transcriptor a veces escribe «Cloud», «Clod» o «Clau»: también cuentan.
- «tallat, …» y «Codex, …» también sirven (no todo el mundo usa Claude), pero solo si lo que viene después es una orden conocida (vuelvo a empezar, zoom, b-roll, sticker).
- La instrucción acaba en el primer final de frase o en un silencio de un segundo. Si no se encuentra el final (más de 25 palabras), queda marcada como `dubtosa` y no se quita nada del vídeo: mírala con la persona.
- Las palabras de la instrucción se quitan del vídeo (motivo «instruccio») y quedan en `instruccions.json` para decidir en la página:
  - **talla** («vuelvo a empezar», «corta desde aquí», «repito», «otra toma»): la toma buena empieza aquí. Si al aceptarla se encuentra el primer intento de la frase que viene después, se quita.
  - **zoom** («zoom», «acércate», «primer plano»): se acerca el trozo que empieza justo después de la instrucción.
  - **broll**, **sticker** (también «pegatina»), **altre**: quedan apuntadas para las fases siguientes.
- **Sin «Claude»**: si la persona se olvida de decirlo (o el transcriptor no lo entiende), tallat-es también encuentra las frases cortas que empiezan con una orden clara («sticker de…», «b-roll…», «cortamos…», «vuelvo a empezar», «haz zoom»). Quedan **dudosas** (`sense_paraula`): no se quita nada del vídeo hasta que la persona las acepta en la página (entonces se quitan sus palabras; si lo deshace, vuelven). Repásalas con ella: «He encontrado 2 frases que parecen instrucciones, pero no has dicho "Claude". Míralas en **Edita → Instrucciones de voz**».
- **Consejo para la próxima grabación**: la primera vez que trabajéis con instrucciones de voz (o si hay dudosas), dile en una línea: «Cuando grabes, empieza cada instrucción con **"Claude,"** y haz una pequeña pausa antes: por ejemplo, *"Claude, sticker de un corazón."*».
- Si una instrucción no se ha detectado y la añades a mano, quita también las palabras donde la decía: `tallat.py afegeix sticker --paraula ID --text "…" --treu A-B` (A y B, la primera y la última palabra de la instrucción; se pueden recuperar en la página).
- Al proponer reels, no incluyas las palabras de las instrucciones ni marcas como «Sigo» que solo sirven para la grabación.

## B-roll y stickers

tallat-es no depende de ninguna IA: solo necesita un archivo para cada instrucción aceptada.

- **Archivos propios**: en la página de revisión, cada instrucción de b-roll o de sticker aceptada tiene «Sube un archivo…» (o se puede arrastrar) y, si hay, un desplegable con la biblioteca (`~/.tallat-es/broll/`, `~/.tallat-es/stickers/`). Los stickers de la biblioteca se asignan solos si el nombre del archivo sale en la instrucción («sticker de un corazón» → `corazon.png`).
- **Generados con IA (opcional)**: si la persona tiene conectada al asistente una IA de imagen o vídeo (Krea, Higgsfield, OpenArt, Adobe Firefly…), ofrécele generarlos. Antes de generar, dile qué modelo usarás y que gastará créditos de su cuenta, y espera a que lo confirme.
  - B-roll: vídeo vertical 9:16, el más corto que permita el modelo (tallat-es coge 1-1,5 s); o una imagen (tallat-es hace un zoom lento). Escribe la descripción en inglés, concreta y visual, sin texto ni caras de personas reales.
  - Stickers: imagen PNG con el fondo transparente (si la IA no sabe hacerlo, quita el fondo con otra herramienta o pídeselo a la persona).
  - Descarga el archivo a la carpeta del proyecto y regístralo: `tallat.py broll ID ARCHIVO` o `tallat.py sticker ID ARCHIVO`.
- Para añadir uno en un momento sin instrucción de voz: `tallat.py afegeix broll|sticker|zoom --paraula ID --text "…"` (con `--treu A-B` si la persona lo dijo en voz alta y hay que quitar sus palabras).
- En la página, en **Viste**, cada b-roll, sticker y zoom es una tarjeta del tablero (ver «El tablero»): con **No**, se va. El b-roll y el sticker puestos desde la página (**+ Añade**, encima del tablero) son una instrucción a mano con `"pagina": true` (no salen en **Por revisar**; si los quita, se borran con sus archivos); el zoom, en el estado (`zooms`), acerca todo el trozo donde cae, de un corte al siguiente.
- **No generes caras de personas reales** (famosos, conocidos): propón un plano que evoque la referencia o pide imágenes propias.

### Cómo sale el b-roll en la pantalla

- Se elige en la página: **Viste** → **Cómo sale el b-roll** (en **Todo el vídeo**). Maneras hechas (`config/estils_broll.json`): **Pantalla completa** (tapa la imagen, corte seco, como siempre), **Tarjeta** (una tarjeta grande redondeada; la persona se ve alrededor), **Ventana** (pequeña en la esquina, con borde del color del kit), **Foto** (borde blanco grueso e inclinada), **Pantalla partida** (el b-roll en la mitad de arriba y la persona en la de abajo) y **Tres tarjetas** (los b-rolls seguidos, a menos de un segundo el uno del otro, entran de uno en uno en hasta tres tarjetas una al lado de la otra y se quedan hasta que acaba el último).
- Se guarda en el kit, sección `broll`: `disposicio` (`pantalla`, `targeta`, `partida`, `carrusel`), `mida` y `posicio_x`/`posicio_y` (de la tarjeta), `proporcio` (9:16, 3:4, 4:5, 1:1, 16:9), `radi` (esquinas), `vora` y `vora_color` (null: el color destacado de los subtítulos), `ombra`, `rotacio` y `animacio` (pop, puja, llisca, fos o cap).
- Dónde va cada tarjeta se calcula en un solo sitio (`motor/targetes.py`): la vista previa y el vídeo final son iguales. En el proyecto para Premiere o Final Cut, el b-roll en tarjeta va más pequeño, recortado y en su sitio, pero sin las esquinas redondeadas, el borde ni la sombra.
- Si la persona usa **Tres tarjetas**, dile que funciona con b-rolls seguidos (uno detrás de otro); si solo hay uno, sale una sola tarjeta en medio.

## El estilo del vídeo

- **Estilo** quiere decir una sola cosa: cómo se ve todo el vídeo. En **Viste** → **Estilo**, una ventana grande con seis estilos (`config/estils_video.json`: Limpio, Revista, Pop, Suave, Impacto y Apilado; los ids, `net`, `revista`, `pop`, `suau`, `impacte`, `apilat`), dibujados encima de un fotograma del vídeo: un toque cambia a la vez los subtítulos, el título gancho, el estilo de los gráficos y el b-roll. No llevan colores ni letras: son siempre los de la persona (**Colores y letras**, la marca del kit). Al elegir uno, los gráficos que tenían un estilo propio pasan al del estilo nuevo.
- **Cada vídeo tiene su estilo.** El kit dice cómo son todos los vídeos de ese estilo; lo que la persona cambia en la página (el estilo, los subtítulos, el título, el b-roll y el sonido) es solo de este vídeo: se guarda en el estado (`edicio.json`, clave `estil`) y se deshace con ⌘Z. **Úsalo en todos los vídeos** lo pasa al kit; **Vuelve al de los demás** lo quita. Los colores y las letras sí son del kit (valen para todos los vídeos).
- **En el chat:** `tallat.py estil --projecte X` dice qué cambia este vídeo; `--tria revista` pone uno de los estilos; `subtitols.mida=0.09 titol.posicio_y=0.2 grafics=editorial` cambia opciones solo de este vídeo; `--a-tots` lo pasa al kit; `--treu` vuelve al del kit. **Si la persona te pide un cambio de estilo para este vídeo, hazlo con `tallat.py estil`**, no en el `kit.json`: si el vídeo ya tiene esa opción cambiada, el cambio del kit no se vería. Edita el kit solo cuando te diga «en todos los vídeos».
- **Subtítulos** y **Título gancho** se retocan a la derecha de Viste, al tocar su fila: mientras tanto, en lugar del tablero está el vídeo grande (**‹ Tablero** vuelve): los subtítulos con cuántas palabras a la vez, cómo destaca la palabra que dices, el tamaño y dónde salen; el título, el texto, cuánto dura, el tamaño y dónde sale. **Más ajustes…** abre el panel entero (a la izquierda), con todo lo demás.
- **Vídeo horizontal:** si la grabación es más ancha que un vertical, en **Viste** → **Todo el vídeo** está **Vídeo horizontal**: **Recortado** (por defecto: se queda el centro) o **Fondo difuminado** (sale entero en medio, con el mismo vídeo grande y difuminado arriba y abajo). En el chat, `tallat.py encaix difumina --projecte X` (o `retalla`; sin nada, dice lo que hay). La primera vez se hace la copia ligera de ese encuadre (unos segundos o unos minutos, según el vídeo; cada encuadre tiene la suya y los reels de una grabación las comparten) y la página cambia sola; mientras tanto, el borrador sale del original. Va al vídeo final, al borrador, a los trozos para CapCut y al proyecto para Premiere o Final Cut: allí el vídeo va entero y el fondo difuminado se hace aparte (`recursos/fons-difuminat.mp4`, solo el trozo de la grabación que usa el montaje, con 2 s de más a cada lado) y va en la pista de debajo, cortado igual; si la persona alarga o acorta un corte en el editor, tiene que hacer lo mismo en el fondo (lo dice el LEEME). Si la persona graba en horizontal y enseña cosas a los lados, propónle el fondo difuminado.

## Estilo de los subtítulos

- Se elige en la página de revisión: **Viste** → **Estilo** (todo el vídeo) y, para retocarlos, **Subtítulos** (a la derecha; **Más ajustes…**, el panel entero). La página tiene tres estaciones, arriba a la izquierda: **Edita** (el texto; en la columna de la izquierda, bajo el nombre, un desplegable para elegir el vídeo entero o uno de los reels, **Por revisar** —las instrucciones de voz y las palabras que tallat-es propone quitar— y **Ritmo**: Original, Pausado, Normal o Ágil, lo cortos que quedan los silencios), **Viste** (cómo se ve: a la izquierda, **Todo el vídeo** —el **Estilo** de todo el vídeo, los **Subtítulos**, el **Título gancho**, los **Colores y letras**, **Cómo sale el b-roll** y **La voz y los efectos**—; en medio, el **tablero** con todas las piezas, que la persona vota; ver «El tablero») y **Revisa**. Los vídeos exportados están en **Exporta**. Hay 18 estilos predefinidos (Clásico, Limpio, Una palabra, Frase, Caja, Karaoke, Impacto, Elegante, Cortina, Revista, Neón, Degradado, Emojis, y los diseñados: Apilado, Esparcido, Escalón, Titular, Rótulo) y se puede ajustar todo: cuántas palabras salen, si aparecen de una en una o todas de golpe, la animación (pop, fundido, impacto, cortina, grosor o ninguna), cómo se destaca la palabra que suena (color, caja, karaoke o más grande), el aspecto (normal, neón o degradado), una píldora de fondo, emojis, la letra, el tamaño, la posición y los colores.
- **Disposición** (`disposicio`): `linia` (cada línea sustituye a la anterior), `apilat` (las líneas de una frase se apilan una debajo de otra hasta que la frase acaba o hay `linies_max`) o `escampat` (como un collage: las palabras de la frase salen en filas cortas en sitios, tamaños e inclinaciones diferentes; las destacadas, solas y grandes; las cortas, más pequeñas. La misma frase hace siempre el mismo collage, y la alineación no cuenta). **Alineación** (`alineacio`): `centre`, `esquerra`, `dreta` o `esglao` (por turnos a la izquierda y a la derecha; las líneas que solo tienen palabras destacadas, en medio, como un título). `espaiat` (entre letras; negativo = juntas, como en los títulos de revista) e `interlineat` (entre líneas).
- **Palabras destacadas** (`clau_grans`): salen `clau_mida` veces más grandes y con `clau_color` (null: el color del destacado), con la letra `clau_font` (null: la misma; la marca pone la de acento) y en cursiva con `clau_cursiva`; con `clau_sola`, cada una va sola en su línea (con `apilat` hace el look de título: «es tan / AMBICIOSO / o / EMPRENDEDOR»). tallat-es elige solas algunas (los números y la palabra larga más importante de cada línea). La persona las puede cambiar en la página (marca la palabra y ⌘B, o **Destaca** en la barrita que sale encima de las palabras marcadas; allí mismo están **Corrige** y **Quita**), y tú con `tallat.py destaca --projecte X --si ID… --no ID…` (sin opciones, te dice cuáles salen ahora, con su número). Cuando la persona quiera subtítulos diseñados, revísalas: una por idea, las que llevan el peso del mensaje (sustantivos, cifras, adjetivos fuertes), nunca palabras puente. La página abierta se pone al día sola en unos segundos.
- **Letras**: las del Mac, 18 gratuitas (Inter, Inter Tight, Archivo, Anton, Bebas Neue, Montserrat, Poppins, Fraunces, Playfair Display, Caveat…; `tallat.py kit lletres`) que se descargan dentro del kit la primera vez que se eligen (`tallat.py kit lletra ID`, o en la página), y las que sube la persona. Todas las letras que no son del Mac viven en la carpeta `fonts/` del kit y viajan con él.
- La vista previa y el vídeo final usan el mismo código de animación (`pagina/subtitols.js`): lo que se ve en la página es lo que sale.
- Las opciones son las de la sección `subtitols` del kit (cada una tiene una nota que la explica). Un cambio para este vídeo, con `tallat.py estil --projecte X subtitols.CLAU=VALOR` (ver «El estilo del vídeo»); en el `kit.json`, solo si es para todos los vídeos. Los estilos predefinidos están en `config/estils_subtitols.json`; los emojis, en `config/emojis.json` (la persona puede añadir en `~/.tallat-es/emojis.json`).

## Título gancho

- Un texto diseñado que sale los primeros segundos del vídeo (como los rótulos de los reels: «#3 cambios / *ser creadora* / nivel fácil»). Cada línea es una línea; lo que va `*entre asteriscos*` sale destacado (más grande y del color destacado). El texto es de cada vídeo (en el estado: se deshace con ⌘Z); el estilo, el del kit (sección `titol`) con lo que cambie este vídeo (`tallat.py estil … titol.CLAU=VALOR`): letra (null: la de los subtítulos), tamaño, `clau_mida`, colores, contorno, sombra, `alineacio` (también `esglao`: las líneas a un lado y al otro y las solo destacadas, en medio), posición, `animacio` (puja, pop, fos, cortina, `maquina` —letra a letra con cursor— o cap), `fons` (cap, `enfosquit` —el vídeo se oscurece— o `pindola` —una caja detrás de cada línea), `corba` (de -1 a 1: 0 recta, positivo en arco como un arcoíris, negativo como una sonrisa) y `corba_linies` (`primera`, `totes` o `darrera`; las líneas curvadas no llevan caja), `durada` y `amaga_subtitols`. Estilos hechos: Escalón, Rótulo, Máquina, Revista, Caja y Arco (`config/estils_titol.json`).
- En la página: **Viste** → **Título gancho** (a la derecha: el texto, cuánto dura, el tamaño y dónde sale; **Más ajustes…** para el resto). En el chat: `tallat.py titol`.
- Cuando hagas el primer montaje o la persona pida un título, propónle uno y enséñaselo antes de ponerlo: 2-4 líneas cortas, en su voz, con una sola parte destacada (la idea que hace quedarse a mirar), sin palabras vacías ni promesas que el vídeo no cumple. Si el título repite lo que se dice, recomienda «sin subtítulos mientras sale el título».

## Plan de gráficos

Gráficos que propones tú, frase a frase, y que la persona vota en el **tablero** de **Viste** (ver «El tablero»). Los propuestos ya salen en la vista previa y en el vídeo; los quitados (los que ha dicho **No**), no. Se guardan en el estado del vídeo (`grafics`), atados a palabras (si se mueven los cortes, siguen su frase), y se dibujan con `pagina/grafics.js`, el mismo código en la vista previa y en el vídeo final.

**Tipos** (el valor de `tipus` va en catalán; los de texto no necesitan ningún archivo; la web y las fotos, imágenes):
- `frase`: una frase clave en grande (como mucho 140 letras; mejor menos de 60). Lo que va `*entre asteriscos*` sale con la letra de acento y el color destacado. Mientras sale, los subtítulos se ocultan (`amaga_subtitols: false` si no lo quieres).
- `marcador` (rotulador): como la frase, pero la parte `*entre asteriscos*` (o toda, si no hay) se marca con un rotulador fluorescente que se dibuja de izquierda a derecha. Para la idea más importante del vídeo: no pongas más de uno o dos. Oculta los subtítulos.
- `etiqueta`: una o dos palabras en una etiqueta pequeña, para marcar la estructura («mito», «paso 1», «el truco», «error»).
- `ratllat` (tachado): lo que se dice primero se tacha y debajo sale lo que va, más grande: para «no es X, es Y», para desmontar un mito o corregir una idea. Los dos `punts`: lo que se tacha y lo que va (pon en cada uno la `paraula` donde se dice: el segundo sale justo entonces); en `text`, si hace falta, lo que va arriba («no es…», como mucho 40 letras). Palabras cortas (una a tres cada punto). Oculta los subtítulos mientras sale.
- `llista` (lista): una tarjeta con un título corto (opcional, en `text`) y 2-5 `punts` que salen uno a uno: pon en cada punto la `paraula` donde se dice, y haz que la lista dure hasta el último (`fins`). Como la frase, oculta los subtítulos mientras sale.
- `crida` (llamada): la llamada a la acción, al final y una sola vez. Sin `paraula`, va a los últimos segundos; sin `text`, dice la de la marca.
- `segueix` (sígueme): la tarjeta de la cuenta de la persona con un botón «Seguir» que se pulsa solo (pasa a «Siguiendo»): el nombre de la cuenta en `de` (el que dice `tallat.py grafics`, «cuenta»; como mucho 30 letras) y, si se quiere, una línea de presentación en `text` («un vídeo nuevo cada semana»). Otra manera de hacer la llamada: no pongas las dos. Sin `paraula`, va a los últimos segundos.
- `notificacio`: una notificación del móvil que cae de arriba: quién la envía en `de` («mamá», «el banco», «Instagram»; como mucho 30 letras) y el mensaje en `text`. Para cuando la persona cuenta que alguien le dice o le escribe algo.
- `comentari`: el comentario de alguien en una tarjeta (como las de debajo de los vídeos, sin ser de ninguna red): quién lo ha escrito en `de` («marta», «@unaseguidora»; como mucho 30 letras) y lo que dice en `text` (como mucho 140 letras). Para cuando la persona responde un comentario o una pregunta que le han hecho («me preguntáis mucho…», «una de vosotras me dijo…»). Pon `fins` hasta la última palabra de la pregunta, para que se pueda leer. No te inventes el nombre de nadie: si la persona no lo dice, pon «alguien» o una descripción («una seguidora»).
- `publicacio`: una publicación citada en una tarjeta (como un post, sin ser de ninguna red): quién la ha escrito en `de` y lo que dice en `text` (como mucho 220 letras; `*entre asteriscos*`, destacado). Para cuando la persona reacciona a algo que alguien ha publicado o a una cita. No te inventes ni el nombre ni lo que dice: solo lo que cuenta la persona.
- `xat` (chat): una conversación en burbujas. Los mensajes van en `punts`, cada uno con `costat` (`rebut`, a la izquierda, o `enviat`, a la derecha; si no, por turnos) y la `paraula` donde se dice; antes de los recibidos salen los tres puntos de «escribiendo…». En `text`, el nombre de la otra persona (opcional). Oculta los subtítulos.
- `notes`: una nota del móvil que se escribe sola, letra a letra: el título en `text` (opcional) y las líneas en `punts` (como mucho 6, cortas), cada una con la `paraula` donde se dice. Para listas personales, confesiones o «cosas que he aprendido». Oculta los subtítulos.
- `numero`: una cifra grande que cuenta desde cero, con la `xifra` como se escribe («73 %», «10.000 €», «3 de cada 4»: cuenta el primer número) y un `text` corto debajo. Solo con cifras que la persona dice de verdad.
- `progres`: un porcentaje o una parte de un total en un círculo o una barra que se llena mientras el número cuenta: la `xifra` como se escribe («70 %», «3 de 5», «7/10», «3 de cada 4»), un `text` corto debajo («del camino», «ya hechos») y la `forma`: `cercle` (por defecto) o `barra`. Para un avance, una parte de un todo o un reto. Solo con cifras que la persona dice de verdad.
- `anotacio`: una nota escrita a mano (`text`, como mucho 40 letras) con una `forma` que se dibuja sola: `fletxa` (de la nota hacia el centro de la pantalla, hacia la persona), `cercle` (alrededor de la nota) o `subratllat`; `costat`: `esquerra` o `dreta`. Va con la letra a mano y el color secundario de la marca, sea cual sea el estilo. Para comentarios irónicos o aclaraciones («yo, hace 3 años», «spoiler: no»).
- `rec`: el marco de una cámara que graba (las cuatro esquinas, «● REC», la batería y el tiempo que corre), en toda la pantalla; en `text`, si se quiere, lo que va en la esquina de abajo («día 1», «domingo»). Para un trozo de vlog o un «grabándolo tal cual»: pon `fins` para que dure todo el trozo. No pongas más de uno por vídeo.
- `web`: una captura de pantalla dentro de una ventana de navegador, que baja poco a poco si la captura es larga. En `text`, la dirección que sale en la barra («miweb.com/curso»); en `imatge`, la captura. Para cuando la persona habla de una web, una herramienta o un producto en línea. Si te dice la dirección, haz la captura: `tallat.py grafics captura URL --grafic gN --projecte X` (con el gráfico ya guardado; sin `--grafic`, te dice el nombre de la imagen para ponerlo en el plan). Si la web pide iniciar sesión o sale un aviso de cookies, mejor que la persona suba su captura en la página.
- `ventall` (abanico): de 2 a 6 fotos abiertas en abanico que salen una a una. Cada foto es un punto: `{"imatge": "~/Desktop/foto.jpg", "text": "antes", "paraula": 52}` (`text`: un pie corto, opcional; la `paraula` donde se dice). En `text`, un título (opcional). Para «antes y después», un proceso, varios ejemplos. Usa solo fotos que la persona te haya dado.
- `abans` (antes y después): dos fotos (`punts`, cada una con `imatge` y, si se quiere, un `text`, que si no dice «antes» y «después»), una encima de la otra; una raya se mueve y descubre la segunda cuando se dice (la `paraula` del segundo punto). En `text`, un título (opcional). Para cambios, resultados y comparaciones. Usa solo fotos que la persona te haya dado.
- `carrusel`: de 3 a 6 fotos (`punts` con `imatge`) que giran en rueda, las de delante más grandes. En `text`, un título (opcional). Para enseñar muchas cosas de una vez (conjuntos, proyectos, sitios). Usa solo fotos que la persona te haya dado.
- La web, el abanico, el antes y después y el carrusel van con **bloque de color** por defecto (`"bloc": false` para quitarlo) y ocultan los subtítulos. Las imágenes pueden ser rutas de archivos del Mac: al guardar el plan, tallat-es las copia al proyecto. Si todavía no tienen, el gráfico no sale en el vídeo y al tocarlo en **Viste** sale **Sube la captura** o **Sube las fotos**: díselo a la persona.

**Estilos** (`estil`): `net` (limpio), `mac` (tarjetas y ventanas de interfaz), `scrapbook` (papel, cinta, letra a mano) o `editorial` (titulares, rayas, números). Si la marca dice algo (`energia`, solo se pone en el chat), usa esos; si no, elígelos tú según el vídeo y mézclalos con criterio (por ejemplo, mac para listas, scrapbook para frases emotivas, editorial para etiquetas; si la persona pide un estilo profesional, net). La persona lo cambia en cada gráfico, en Viste. Si no pones, va el primero de la marca (o net). **Sitio** (`posicio`): `dalt`, `mig`, `baix` o un número de 0 (arriba) a 1 (abajo), donde va el centro del gráfico (por defecto: frase y etiqueta arriba, lista y llamada abajo; si dos gráficos coinciden en el mismo sitio, tallat-es mueve uno). Nunca salen de la **zona segura de Instagram** (el 14 % de arriba y el 35 % de abajo quedan libres, y 120 px a cada lado, por los botones): tallat-es los hace caber solo. Tampoco tapan los subtítulos; los que los ocultan (`amaga_subtitols`) pueden ocupar su sitio. **Duración**: frase 2,8 s, rotulador 2,8, etiqueta 2,2, tachado 3, lista 4,5, llamada 3,5, notificación 3, comentario 3,5, chat 5, número 2,8, progreso 3, anotación 2,5, web 4, abanico 4,5, sígueme 3,5, publicación 4, notas 5, REC 4, antes y después 4,5, carrusel 5; con `fins` (una palabra), dura hasta que acaba esa palabra.

**Bloque de color** (`"bloc": true`): mientras sale el gráfico, el fondo se hace del color de la marca (el oscuro; el principal con `mac` y `scrapbook`), el vídeo se hace pequeño con una animación suave hasta una tarjeta abajo (se sigue viendo la cara) y el gráfico tiene todo el espacio de arriba. Por defecto va en medio de este espacio y oculta los subtítulos. Si dos gráficos con bloque van seguidos, el vídeo se queda pequeño. Va bien para las listas, la web, las fotos y los momentos «diapositiva», sobre todo cuando la cara llena el recuadro y no hay sitio libre; no abuses (uno o dos por vídeo) y, mientras dura, no pongas ningún otro gráfico. La persona lo activa o lo quita tocando el gráfico en el vídeo. Solo sale en los vídeos que exporta tallat-es, no en el proyecto para otros editores.

**Cuándo:** cuando la persona diga «propónme gráficos», «pon gráficos» o similar. Al acabar el primer montaje, ofréceselo (no lo impongas).

**Cómo:**
1. `tallat.py grafics --projecte X` te da la marca (el estilo y cuántos gráficos, la llamada), las frases del vídeo tal como suenan ahora (el segundo y el número de la primera y la última palabra) y el plan que hay. Lee también `tallat.py gust`.
2. Haz el plan:
   - Cuántos: los de la marca (`pocs`, uno cada 8-12 s; `normal`, cada 4-6 s; `molts`, cada 2-4 s).
   - Un gráfico por idea, donde ayude a entender o a quedarse: la frase que lleva el peso del mensaje (`frase`, o `marcador` para la más importante), la estructura (`etiqueta`), una lista personal (`notes`), una publicación a la que reacciona (`publicacio`), un trozo de vlog (`rec`), un cambio o una comparación con fotos (`abans`), muchas fotos de una vez (`carrusel`), el «no es X, es Y» (`ratllat`), las enumeraciones (`llista`), lo que alguien le dijo o escribió (`notificacio`, `xat`), el comentario o la pregunta que responde (`comentari`), las cifras (`numero`; si es una parte de un todo o un avance, `progres`), los comentarios de lado (`anotacio`), una web o una herramienta de la que habla (`web`), las fotos que te haya dado (`ventall`) y, solo si la persona tiene una llamada a la acción (`crida` en la marca) o te la pide, la llamada al final. Varía los tipos: no pongas tres iguales seguidos.
   - No tapes el título gancho (los primeros segundos) ni pongas dos gráficos en el mismo sitio a la vez.
   - **Dónde queda mejor:** después de guardarlo, haz `tallat.py grafics fotogrames --projecte X` y mira la imagen que te dice (un fotograma por gráfico, en orden; oscurecido, donde no puede ir nada; el recuadro amarillo, donde sí). Elige el sitio de cada uno según lo que hay en el fotograma: que no tape los ojos ni la boca, ni lo que se enseña (un objeto, una pantalla). Si la cara llena el recuadro, los pequeños (etiquetas, frases de una línea) arriba, sobre la frente, y los grandes (listas, tarjetas) abajo, en lugar de los subtítulos. Guarda los sitios con `grafics canvia`.
   - En la voz de la persona y con su gusto (minúsculas, sin palabras prohibidas, sin prometer nada que el vídeo no cumple). Acorta: un gráfico no es el subtítulo.
3. Escríbelo en un archivo JSON (fuera del repositorio de tallat-es, por ejemplo en la carpeta del proyecto) y guárdalo con `tallat.py grafics proposa PLAN.json --projecte X`. Es una lista:
   ```json
   [{"tipus": "etiqueta", "paraula": 3, "text": "3 cosas", "estil": "editorial", "motiu": "anuncia la estructura"},
    {"tipus": "llista", "paraula": 10, "fins": 36, "text": "antes de empezar", "estil": "mac",
     "punts": [{"text": "no hace falta tenerlo claro", "paraula": 14}, {"text": "constancia > talento", "paraula": 23}]},
    {"tipus": "frase", "paraula": 37, "fins": 41, "text": "no es pereza, es *cansancio*", "estil": "scrapbook"},
    {"tipus": "crida", "estil": "mac"}]
   ```
   `motiu` (opcional) es una frase corta que la persona ve en la tarjeta del gráfico, en el tablero: por qué va. Un plan nuevo sustituye los propuestos que había; los mantenidos, los que tienen una nota y los quitados se quedan (con `--de-nou`, todo de nuevo). Como la persona no tiene que marcar los que le gustan, **si ya hay un plan, no hagas uno nuevo entero sin preguntárselo**: para atender las notas o añadir, usa `canvia`.
   **Dos opciones para un momento:** si dudas entre dos gráficos para la misma frase, pon los dos con el mismo `grup` (un nombre corto: `"grup": "a1"`). En el tablero salen juntos y la persona elige uno; en el vídeo solo sale el primero hasta que elija. Como mucho uno o dos grupos por ronda.
4. Explícale en dos o tres frases qué has puesto y que los vote en **Viste** (la página se pone al día sola).

**Las notas:** la persona te pide los cambios con la nota de cada tarjeta del tablero (te van llegando con la ronda, ver «El tablero») o con notas de la página («En el gráfico «…»: …»), que te llegan como las demás (ver «Notas de la página»): búscalo con `tallat.py grafics --projecte X`. Los que tienen el estado `canvia` llevan la nota en el plan: cuando diga «mira las notas de los gráficos», `tallat.py grafics --projecte X`: los que dicen `CAMBIA` llevan la nota debajo. Si una nota habla del sitio («más abajo», «me tapa la cara»), mira su fotograma (`grafics fotogrames`) antes de elegir otro. Haz lo que pide cada nota y guarda solo esos gráficos, con el mismo `id` y enteros (tipus, paraula, text…), con `tallat.py grafics canvia NOTAS.json --projecte X`: el resto del plan no se toca. Un gráfico cambiado vuelve a «propuesto» y pierde la nota y el voto. Si una nota pide un gráfico que todavía no existe (una ventana de web, imágenes, el vídeo dentro de un marco…), dile que todavía no hay y propónle lo más parecido.

## El tablero (Viste)

En medio de **Viste**, todas las piezas del vídeo en el orden en que salen: los gráficos, los b-rolls, los stickers, los zooms y los sonidos puestos a mano. Cada una es una tarjeta con su trozo de vídeo como quedará (la que la persona señala se mueve, y con el altavoz suena). En cada una dice **Sí**, **Quizá** o **No**, y puede escribir una nota. Tus gráficos sin voto son «por mirar»; el resto de piezas son suyas (las ha puesto ella o las ha dicho en voz alta), y son **Sí** si no dice lo contrario. Las tarjetas dicen **Nueva** o **Cambiada** (los gráficos que has puesto o cambiado en la última ronda) y **Tuya** (las que ha puesto ella).

- Los votos de los gráficos van dentro de cada gráfico (`vot`: `si`, `potser` o `no`) y mandan sobre el estado: **No** → `tret`, **Quizá** (o **Sí** con una nota) → `canvia`, **Sí** → `mantingut`. Los de las otras piezas, en el estado (`vots`). `tallat.py grafics --projecte X` lo dice todo: el voto de cada gráfico (SÍ, QUIZÁ, NO o «por mirar») y, debajo, las otras piezas con un **QUIZÁ** o una nota.
- **+ Añade** (encima del tablero): la persona pone una pieza suya, un sticker o una imagen o un vídeo que ocupa la pantalla (b-roll), en la palabra que elige. Sale como **Tuya** y ya con el **Sí**: no la toques si no te lo pide. Cada sticker se puede arrastrar en su tarjeta: el sitio donde lo deja se guarda en el estado (`llocs_stickers`, el centro de 0 a 1) y es donde sale en el vídeo final; si no, va al del estilo (`stickers.x` y `stickers.y`, a un lado y al otro si hay más de uno).
- **Pide la siguiente ronda** (debajo del tablero) te envía una nota para todo el vídeo: «Siguiente ronda de propuestas.», con la nota para toda la ronda si ha puesto una. Si todavía no hay ninguna propuesta, el botón es **Pide propuestas a Claude** y la nota dice «Proponme gráficos para este vídeo.» (haz el plan de «Plan de gráficos»).
- **Cómo se hace una ronda:**
  1. `tallat.py grafics --projecte X` (y `tallat.py gust`).
  2. **SÍ**: no lo toques. **NO**: ni lo vuelvas a proponer ni propongas uno parecido en el mismo sitio. **QUIZÁ** con nota: haz lo que dice. **QUIZÁ** sin nota: no la convence; propónle una versión diferente (otro tipo, otro texto u otro sitio), o dos opciones con el mismo `grup`. **Por mirar**: déjalo, salvo que la nota de la ronda hable de él.
  3. La nota para toda la ronda («menos cosas al final», «más profesional») vale para todo: si hace falta, quita de los **por mirar** (no los pongas en la ronda) o añade hasta la cantidad de la marca.
  4. Las otras piezas con un **Quizá** o una nota (un zoom «más suave», un b-roll «más corto»): hazlo con las órdenes de cada una, o dile que todavía no se puede. Al guardar la ronda, sus votos y notas se limpian.
  5. Guárdala con `tallat.py grafics proposa RONDA.json --projecte X`. Van los **por mirar** que se quedan (iguales, con su `id`), los que cambias (con el mismo `id`, enteros) y los nuevos (sin `id`). Los **Sí**, los **No** y los **Quizá** que no pongas se quedan como están; los **por mirar** que no pongas se van. Cada vez que guardas un plan es una ronda nueva (el número sale encima del tablero); retocar con `canvia` los que acabas de proponer, antes de que los vote (el sitio, después de mirar los fotogramas), no lo es.
  6. Responde la nota con una frase: «Hecho: he cambiado 2 y he añadido 1.». La persona la ve debajo del tablero.

## Sonido

- **Viste** → **La voz y los efectos** (en **Todo el vídeo**), en la página; se guarda en el kit, sección `so`.
- **Limpieza de la voz** (`neteja`, sí por defecto): quita el zumbido grave y el ruido de fondo (`soroll`: `suau`, `mitja` o `fort`), da claridad, suaviza las «s», comprime un poco e iguala el volumen a -14 LUFS (el de las redes), en dos pasadas. Se aplica al borrador y al vídeo final; en la vista previa suena la voz original, pero la página deja escuchar diez segundos antes y después. Si la persona dice que la voz suena rara o «enlatada», baja el `soroll` a `suau` o apaga la limpieza.
- **Efectos de sonido** (`efectes`: `cap`, `pocs` —whoosh en el b-roll y en la frase clave, pop en los stickers y en la lista, campanita en el título y en la llamada, o teclado si el título es a máquina de escribir— o `molts` —también un pop en cada etiqueta y en cada punto de la lista y un tic en las palabras destacadas; `volum_efectes` de 0 a 1). Los fabrica tallat-es con código (`motor/so.py`): sin archivos de fuera ni licencias. Cada efecto de un vídeo se puede apagar en la lista de **La voz y los efectos** (queda en el estado, `sons_apagats`). Un sonido puesto en un momento concreto queda en el estado (`sons`: `[{"id": "s1", "so": "pop", "paraula": 120}]`), suena cuando se dice esa palabra, siempre (también con `cap`), y es una tarjeta del tablero. La persona puede poner sus sonidos en `~/.tallat-es/sons/` con el nombre del que sustituyen (whoosh, pop, tecla, brill o tic; WAV, MP3, M4A o AIFF).
- Todos los efectos se mezclan en una sola pista: la misma suena en la vista previa y va al vídeo final. En el proyecto para Premiere o Final Cut y en los trozos para CapCut va aparte (`efectes-de-so.wav`, para poner al principio); allí la voz no va limpia.

## Kits de estilo

- Un kit es un estilo con nombre: los subtítulos (con la letra propia, si tiene), el b-roll, los stickers y los cortes. La persona puede tener varios («Reels rápidos», «Vídeos tranquilos»…) y cada vídeo usa uno. Un reel usa el de su grabación, si no se le elige otro.
- Están en `~/.tallat-es/kits/<id>/kit.json`, con las fuentes en `fonts/`, fuera del repositorio. `~/.tallat-es/kits/kits.json` dice cuál es el **por defecto**: el de los vídeos nuevos, y el que cambian las reglas del gusto. Los valores que faltan en un kit se toman del estilo neutro (`config/brand.example.json`). La primera vez que se instala, si la persona ya tenía kits en tallat (catalán), se copian aquí.
- La primera vez, el estilo que la persona ya tenía (`~/.tallat-es/brand.json`) se convierte en el kit «Mi estilo». brand.json no se toca, pero ya no se usa.
- En la página de revisión, **Viste** → **Colores y letras** → **Estilos guardados**: la lista de kits (tocar uno lo usa en este vídeo y abre sus colores y letras; al pie, las acciones). La mayoría de gente tiene uno. Se puede elegir el kit del vídeo, duplicarlo, hacer uno nuevo con el estilo de tallat, cambiarle el nombre, hacerlo por defecto, exportarlo (un `.zip` para pasárselo a alguien) e importar. En el chat: `tallat.py kit` y sus órdenes. El id de un kit (el nombre de la carpeta) no cambia aunque se le cambie el nombre.
- Cuando la persona quiera un estilo «para un tipo de vídeo» o «para pasárselo a alguien», propónle un kit. Si un kit lleva una fuente propia y lo quiere pasar a alguien, recuérdale que compruebe que la fuente se puede compartir.
- «Quitar» un kit no lo borra: va a `~/.tallat-es/kits-esborrats/`. El kit por defecto no se puede quitar.

## Acabarlo en otro editor

Si la persona quiere retocar el vídeo en Premiere, Final Cut, DaVinci Resolve o CapCut: `tallat.py editors` (o, en la página, **Exporta** → «Para acabarlo en otro editor» → «Premiere, Final Cut o DaVinci»). Escribe en `exports/` una carpeta con el proyecto (`.fcpxml` para Final Cut y DaVinci, `.xml` para Premiere), los subtítulos en `.srt`, el b-roll y los stickers en `recursos/`, y un `LEEME.txt` con los pasos de cada editor. CapCut e iMovie no importan proyectos: para ellos, `tallat.py editors --trossos` (en la página, «CapCut o iMovie») saca cada trozo como un clip numerado (01.mp4, 02.mp4…) con el zoom aplicado, el b-roll y los stickers con el momento en el nombre, y el `.srt`; arrastrados todos a la vez a la línea de tiempo quedan en orden (se pueden acortar, no alargar). Con `--amb-subtitols` añade los subtítulos, el título gancho y los gráficos de tallat-es como capa transparente (tarda unos minutos); sin él, el título y los gráficos no están. Los cortes apuntan al vídeo original: que no lo mueva.

## Tu gusto (reglas para los vídeos siguientes)

- **Antes de decidir nada** (limpieza, primer montaje y reels, instrucciones, b-roll y stickers, gráficos, estilo), lee las reglas con `tallat.py gust` y síguelas. Las que llevan un ajuste ya se aplican solas.
- **Cuando la persona reacciona a un resultado** («demasiado lento», «los subtítulos son pequeños», «no me quites los vale»):
  1. Busca el comportamiento que hay detrás, no solo el caso concreto: «este b-roll es demasiado largo» quiere decir «b-roll más corto», no «quita este b-roll».
  2. Pregúntale (con opciones de respuesta si puedes; si no, con una pregunta corta) si es **para este vídeo** o **para siempre** (recomienda «para siempre»). Si ya lo ha dicho («siempre», «solo aquí»), no lo preguntes.
  3. Si es para siempre, guárdalo: `tallat.py gust afegeix SECCIO "la regla en palabras de la persona" [--ajust clau=valor]`. Si es solo para este vídeo, hazlo en el proyecto y ya.
- Secciones: `talls`, `subtitols`, `grafics`, `broll`, `stickers`, `so`, `reels`, `altres`.
- Los ajustes de estilo se hacen en el **kit por defecto**. Si el vídeo usa otro kit y la persona quiere el cambio también allí, hazlo en su `kit.json` (o en la página, con ese kit elegido).
- Ajustes (si hay uno que encaja, ponlo; si no, la regla solo con texto):

| Dice | `--ajust` |
|---|---|
| cortes demasiado lentos / demasiado rápidos | `talls.pausa_maxima=0.25` (más rápido) o `0.5` (más lento); para los proyectos nuevos |
| no me quites «X» / quita siempre «X» / solo propón «X» | `farciment.deixa=X` / `farciment.treu=X` / `farciment.proposa=X` |
| subtítulos más grandes / más pequeños | `subtitols.mida=0.09` (el tamaño actual está en el kit; el normal, 0,075) |
| más / menos palabras en la pantalla | `subtitols.paraules_per_linia=1` (una), `3`, `7` (frase) |
| subtítulos más arriba / más abajo | `subtitols.posicio_y=0.6` (0 arriba, 1 abajo) |
| color de la palabra destacada | `subtitols.color_actiu="#FF375F"` |
| b-roll más corto / más largo | `broll.durada=1.0` |
| sin efectos de sonido / más efectos | `so.efectes="cap"` / `"molts"` |
| el b-roll en tarjeta / a pantalla completa | `broll.disposicio="targeta"` / `"pantalla"` |
| stickers más pequeños / más grandes | `stickers.mida=0.25` |

- Para quitar una: `tallat.py gust treu NUMERO` (la opción vuelve a como estaba). Las reglas solo se llevan en el chat (en la página no están): si la persona pregunta cuáles tiene, enséñaselas en palabras sencillas.

## Exportar

- El borrador es para revisar. El vídeo final se hace en la página (**Exporta** → **Vídeo final**), que dice **en qué carpeta se guarda** y tiene **Cambia…** (la ventana del Mac o de Windows para elegir carpeta; tallat-es la recuerda). En el chat, `tallat.py exporta` hace lo mismo y guarda en la misma carpeta.
- Los vídeos siempre quedan también en la carpeta del proyecto (en **Exporta**, en **Tus vídeos**); en la carpeta elegida van como un enlace al mismo archivo (no ocupan más sitio en el mismo disco).
- Cuando acabe, dile el nombre del archivo y dónde está. En la página queda un aviso con **Muéstrala en el Finder** (en Windows, **en el Explorador**).
- Para Premiere: después de importar el `.xml`, hay que hacer **doble clic en la secuencia** (si se arrastra a una secuencia nueva, Premiere la convierte en un solo clip).

## Notas de la página

Debajo del vídeo, la persona te deja notas («aquí, un rótulo que diga…», «los subtítulos, más grandes»). Cada una va al momento donde estaba el vídeo (a la palabra que sonaba) o a todo el vídeo. Cuando acaba de revisar, toca **Envía a Claude**. Mientras tú las esperas, la página dice **«Conectado con Claude»**. Si envía más mientras haces unas, en la página quedan «En la cola» y te vuelven a llegar cuando vuelves a esperar; si las envía de una en una seguidas, la espera da unos segundos y te las da juntas.

- **Espéralas siempre que la página esté abierta.** Justo después de abrirla con `revisa`, ejecuta `tallat.py notes --projecte X --espera --minuts 60` **en segundo plano** (en Claude Code, con la orden en segundo plano: te avisa cuando acaba). En Codex, que no tiene segundo plano, hazlo al acabar cada respuesta, con `--minuts 9` (el máximo que se puede esperar).
- Cuando la orden acaba con notas, hazlas **en la carpeta que dice cada nota** (la del reel, si es de un reel). La nota dice el segundo del vídeo (el que la persona ve bajo el vídeo, el que usa `tallat.py moment`), el de la grabación, el número de la palabra y qué se dice alrededor.
- **Responde cada nota** con una frase corta de lo que has hecho: `tallat.py notes --projecte X --respon NÚMERO "Hecho: …"`, con el número que dice la nota en «Para responderla» (p. ej. `3.1`). La persona lo ve debajo de la nota. La página numera las notas por el orden del vídeo (1, 2, 3… de izquierda a derecha), que no es su id: `tallat.py notes` dice los dos («Nota 7 (en la página, la 2)»). Con la persona, usa el de la página; en `--respon`, el de «Para responderla». Si no lo tienes claro, o el cambio es grande (borrar un reel, volver a cortar mucho), no lo hagas: pregúntalo con `--respon NÚMERO "…?" --pregunta`. Su respuesta te vuelve a llegar como una nota, con toda la conversación.
- **En el chat, una sola línea por tanda** («He hecho las 3 notas de la página; las respuestas están debajo de cada nota»): el detalle ya está en la página, y si no, el chat se llena y se solapa con lo que la persona te escribe.
- En las respuestas, di **dónde** con la palabra («cuando dices *es igual*») más que con el segundo: si la persona quita o recupera trozos, los segundos cambian y la palabra no.
- **Enlaces en las notas:** descargar un archivo de internet solo lo haces si la persona te lo dice **en el chat** (no basta con la nota). Pregúntalo en el chat (nombre del archivo, de dónde viene) y responde la nota con `--respon NÚMERO "Te lo pregunto en el chat." --al-xat`: la página le dice que responda en el chat. Si la imagen es de una marca, un personaje o un artista, avisa de que puede tener derechos de autor (lo decide ella). Los enlaces de Instagram (y muchos de TikTok) no se pueden ver sin iniciar sesión: pídele que te explique el efecto o que guarde el vídeo o una captura en la carpeta del vídeo.
- Después, **vuelve a esperarlas** (`--espera`, en segundo plano, otra vez). Si la espera se acaba sin notas, vuelve a lanzarla mientras la página esté abierta y la persona no te haya dicho que ha acabado.
- Si la persona te dice **«mira mis notas»** (la página se lo propone cuando tú no estás conectado), ejecuta `tallat.py notes --projecte X --espera --minuts 0.1`: recoge enseguida las que ya ha enviado. Sin `--espera`, `tallat.py notes --projecte X` las lista todas con su estado.

### Revisa (las revisiones finales)

Arriba de la página, **Edita · Viste · Revisa**. En Revisa, la persona mira un borrador exportado (una **versión**) grande, como lo verá la gente, y deja notas; cada nota guarda el segundo de esa versión y una miniatura del fotograma. Las notas te dicen de qué versión son y dónde está la miniatura: **mírala** (es lo que veía) antes de hacer el cambio. La palabra y el segundo de la grabación ya salen de los cortes de esa versión, aunque después se haya editado.

- Cuando acabas **todas** las notas de una versión, **haz una nueva**: `tallat.py exporta --projecte X --qualitat esborrany`. La página la enseña sola como «Versión N+1», sin notas: la persona revisa la nueva, y las de la anterior se quedan en su versión. Díselo en el chat, en una línea, que ya la tiene.
- Si la persona todavía no tiene ningún borrador, Revisa le ofrece hacer uno.

## Revisar el borrador

- La persona mira el borrador (o el montaje En directo) y te dice qué quiere cambiar: en el chat, con el segundo que ve bajo el vídeo («en el segundo 12, el b-roll es demasiado largo»), o con una nota en la página (ver «Notas de la página»).
- Para saber qué hay en ese momento, `tallat.py moment SEGUNDOS --projecte X` (con `--esborrany` si habla del borrador: si ha cambiado cosas después, los tiempos no coinciden con el montaje de ahora). Te dice el segundo de la grabación, las palabras de alrededor con su número (» la que suena, [entre corchetes] las quitadas) y si sale el título, un gráfico del plan, un b-roll o un sticker. Si no está claro de qué vista habla, pregúntaselo.
- Haz el cambio y explícale qué has hecho. Si la corrección parece «para siempre» (el b-roll siempre es demasiado largo), sigue lo que dice «Tu gusto».

## Reglas

- No leas ni copies ninguna carpeta de marca personal salvo que la persona lo pida explícitamente.
- No borres ni muevas archivos de la persona sin que te lo confirme.
- No se renderiza nada en 4K hasta que la persona lo aprueba en la página (en **Exporta**).
