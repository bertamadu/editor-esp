"""editor-esp: editor de reels en català, per paraules.

Ús (la primera vegada: ./prepara.sh, que instal·la tot el que cal):
  python tallat.py comprova                           (revisa que l'ordinador tingui tot el que cal)
  python tallat.py transcriu VIDEO --projecte CARPETA [--srt FITXER.srt] [--model large-v3]
  python tallat.py revisa --projecte CARPETA          (obre la pàgina de revisió)
  python tallat.py neteja --projecte CARPETA [--pausa 0.35]
  python tallat.py estat --projecte CARPETA
  python tallat.py guio --projecte CARPETA            (text per paràgrafs perquè l'assistent proposi reels)
  python tallat.py reels --projecte CARPETA           (valida reels.json i en mostra la durada)
  python tallat.py reel ID --projecte CARPETA         (crea el projecte d'un reel proposat)
  python tallat.py realinea --projecte CARPETA         (torna a calcular el temps de cada paraula)
  python tallat.py afegeix TIPUS --paraula ID --projecte CARPETA [--text "…"] [--treu A-B]   (instrucció a mà)
  python tallat.py broll ID_INSTRUCCIO FITXER --projecte CARPETA [--durada 1.5]
  python tallat.py exporta --projecte CARPETA [--qualitat esborrany|1080|4k]
  python tallat.py editors --projecte CARPETA [--amb-subtitols] [--trossos]   (Premiere, Final Cut, DaVinci / CapCut)
  python tallat.py gust                                (les regles del teu gust)
  python tallat.py gust afegeix SECCIO "TEXT" [--ajust subtitols.mida=0.09]
  python tallat.py gust treu NUMERO
  python tallat.py marca [--projecte CARPETA] [CLAU=VALOR …]   (la teva marca: colors, lletres, crida a l'acció)
  python tallat.py grafics --projecte CARPETA [--json]          (les frases, la marca i el pla de gràfics, amb notes)
  python tallat.py grafics proposa PLA.json --projecte CARPETA  (desa el pla de gràfics que proposa l'assistent)
  python tallat.py grafics canvia PLA.json --projecte CARPETA   (només els gràfics del fitxer: les notes ateses)
  python tallat.py grafics fotogrames --projecte CARPETA        (el fotograma de cada gràfic, per triar-ne el lloc)
  python tallat.py grafics captura URL [--grafic g3] --projecte CARPETA  (la captura d'una web, per al gràfic «web»)
  python tallat.py notes --projecte CARPETA [--espera [--minuts 9]]      (les notes de la pàgina per a l'assistent)
  python tallat.py notes --projecte CARPETA --respon NÚMERO "TEXT" [--pregunta | --al-xat]

La carpeta del projecte ha de ser fora del repositori (els vídeos i el que dius no es publiquen).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import webbrowser
from pathlib import Path

from motor import comprova, edicio, editors, entorn, exporta, grafics, gust, instruccions, marca, muntatge, notes, transcripcio
from motor.projecte import EXPORTS, ORIGINAL, PROXY, TRANSCRIPCIO, Projecte, arrel_de, minuts


def _carrega(args) -> Projecte:
    carpeta = Path(args.projecte).expanduser().resolve()
    # En un reel sense enllaços (Windows), la transcripció és a la gravació sencera.
    if not (arrel_de(carpeta) / TRANSCRIPCIO).exists():
        sys.exit(f"Esta carpeta todavía no tiene ninguna transcripción: {carpeta}\n"
                 "Primero haz: python tallat.py transcriu VIDEO --projecte CARPETA")
    projecte = Projecte(carpeta)
    for a in projecte.avisos:
        print("Aviso:", a)
    return projecte


def _barra(text: str):
    ultim = [-10]

    def progres(pct: int):
        if pct >= ultim[0] + 10:
            print(f"  {text}… {pct} %", flush=True)
            ultim[0] = pct
    return progres


def guarda_anteriors(carpeta: Path) -> Path | None:
    """Abans de canviar la transcripció, guarda l'edició d'abans en una carpeta a part.

    L'edició, les instruccions i els reels apunten a paraules que amb la transcripció nova poden
    ser unes altres. No s'esborren: van a «anteriors-…», amb una còpia de la transcripció vella i
    dels recursos, i amb la mateixa estructura, de manera que els reels hi continuen funcionant."""
    moure = [nom for nom in ("edicio.json", "edicio.txt", instruccions.FITXER, muntatge.CARPETA_REELS)
             if (carpeta / nom).exists() or (carpeta / nom).is_symlink()]
    if not moure or not (carpeta / TRANSCRIPCIO).exists():
        return None
    desti = carpeta / f"anteriors-{time.strftime('%Y%m%d-%H%M%S')}"
    desti.mkdir()
    shutil.copy2(carpeta / TRANSCRIPCIO, desti / TRANSCRIPCIO)
    if (carpeta / ORIGINAL).exists():
        shutil.copy2(carpeta / ORIGINAL, desti / ORIGINAL)
    for nom in ("broll", "stickers"):  # els recursos, enllaçats (no ocupen el doble)
        if (carpeta / nom).is_dir():
            shutil.copytree(carpeta / nom, desti / nom, copy_function=_enllaca)
    for nom in (PROXY, "veu.npy", "veu.json"):  # el mateix vídeo: n'hi ha prou amb apuntar-hi
        if (carpeta / nom).exists():
            try:
                (desti / nom).symlink_to(Path("..") / nom)
            except OSError:  # Windows sense permís per fer enllaços
                # La còpia lleugera, el mateix fitxer amb un altre nom (no es reescriu mai: es reemplaça). El mapa
                # de veu, una còpia: veu.carrega el reescriu i, compartit, canviaria el de l'altra carpeta.
                (_enllaca if nom == PROXY else shutil.copy2)(carpeta / nom, desti / nom)
    for nom in moure:
        (carpeta / nom).rename(desti / nom)
    return desti


def _enllaca(origen, desti) -> None:
    try:
        os.link(origen, desti)
    except OSError:
        shutil.copy2(origen, desti)


def ordre_realinea(args) -> None:
    """Torna a calcular quan comença i acaba cada paraula (amb l'alineador d'ara), sense canviar el text
    ni res de l'edició: els talls, els subtítols i els gràfics hi tornen a caure al lloc."""
    projecte = _carrega(args)
    path = projecte.fitxer(TRANSCRIPCIO).resolve()  # en un reel, la de la gravació sencera
    dades = json.loads(path.read_text(encoding="utf-8"))
    paraules = dades["paraules"]
    frases: dict[int, list[dict]] = {}
    for p in paraules:
        frases.setdefault(p["frase"], []).append(p)
    segments = [{"start": ps[0]["inici"], "end": ps[-1]["final"], "text": " ".join(p["text"] for p in ps)}
                for _, ps in sorted(frases.items())]
    print(f"Calculando de nuevo el tiempo de {len(paraules)} palabras (puede tardar unos minutos; la primera vez descarga el modelo)…",
          flush=True)
    t0 = time.time()
    video = projecte.video
    if not video.exists():  # s'ha mogut l'original: la còpia lleugera té el mateix so i el mateix temps
        video = path.parent / PROXY
        print(f"No encuentro el vídeo original: uso la copia ligera ({video.name}).")
    if not paraules or not video.exists():
        sys.exit("No hay nada que alinear (ninguna palabra, o ni el vídeo ni la copia ligera).")
    noves = transcripcio.a_paraules(transcripcio.alinea(transcripcio.carrega_audio(video), segments))
    if [p["text"] for p in noves] != [p["text"] for p in paraules]:
        sys.exit("Las palabras no coinciden con las de la transcripción: no he cambiado nada.")
    canvis = [abs(n["inici"] - p["inici"]) for n, p in zip(noves, paraules)]
    copia = path.with_name(f"transcripcio-abans-{time.strftime('%Y%m%d-%H%M%S')}.json")
    shutil.copy2(path, copia)
    for p, n in zip(paraules, noves):
        p["inici"], p["final"], p["confianca"] = n["inici"], n["final"], n.get("confianca")
    font = re.sub(r"\s*\+ alineació.*$", "", str(dades.get("font", "")))
    dades["font"] = f"{font} + alineación de todo el texto" if font else "alineación de todo el texto"
    path.write_text(json.dumps(dades, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Hecho en {minuts(time.time() - t0)}. {sum(c > 0.25 for c in canvis)} palabras se han movido más de un cuarto de "
          f"segundo (la que más, {max(canvis):.1f} s). La de antes está en {copia.name}.")
    print("Si tienes la página de revisión abierta, ciérrala y vuelve a abrirla.")


def ordre_compara_temps(args) -> None:
    """Quant s'assemblen els temps de les paraules del projecte i els d'un SRT fet per una altra eina
    (Descript). Amb un SRT d'una paraula per subtítol es comparen totes; amb subtítols de frases, només
    l'inici de la primera paraula i el final de l'última de cada subtítol. On no coincideixen, val la pena
    escoltar-ho: és la manera de saber quin dels dos encerta (vegeu transcripcio.compara_temps)."""
    carpeta = Path(args.projecte).expanduser().resolve()
    path = arrel_de(carpeta) / TRANSCRIPCIO  # en un reel sense enllaços, la de la gravació sencera
    if not path.exists():
        sys.exit(f"No encuentro la transcripción: {path}")
    paraules = json.loads(path.read_text(encoding="utf-8"))["paraules"]
    r = transcripcio.compara_temps(paraules, transcripcio.llegeix_srt(Path(args.srt).expanduser()))
    if not r["n"]:
        sys.exit("No he encontrado palabras comunes entre la transcripción y el SRT.")
    print(f"{r['n']} bordes comparados. Diferencia mediana: {r['mediana'] * 1000:.0f} ms.")
    print(f"  más de una décima: {r['mes_01']} ({r['mes_01'] / r['n']:.0%}) · más de un cuarto de segundo: {r['mes_025']}"
          f" · más de medio segundo: {r['mes_05']}")
    if r["grans"]:
        print("Dónde más difieren (escúchalo para saber cuál acierta):")
        for g in r["grans"]:
            print(f"  {minuts_i_segons(g['nostre'])}  «{g['text']}»: editor-esp {g['nostre']:.2f} s, SRT {g['srt']:.2f} s")


def minuts_i_segons(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:05.2f}"


def ordre_transcriu(args) -> None:
    video = Path(args.video).expanduser().resolve()
    carpeta = Path(args.projecte).expanduser().resolve()
    if not video.exists():
        sys.exit(f"No encuentro el vídeo: {video}")
    if (carpeta / TRANSCRIPCIO).is_symlink() or (carpeta / muntatge.REEL).exists():
        # Un reel comparteix la transcripció amb la gravació sencera: refer-la aquí la canviaria per a tots.
        sys.exit("Este proyecto es un reel: comparte la transcripción con la grabación entera.\n"
                 "Si la tienes que rehacer, hazlo en la carpeta de la grabación (y vuelve a crear los reels).")
    if (carpeta / TRANSCRIPCIO).exists() and not args.forca:
        sys.exit(f"Este proyecto ya tiene una transcripción ({carpeta / TRANSCRIPCIO}).\n"
                 "Si la quieres rehacer y perder los cambios, añade --forca.")
    carpeta.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print("Cargando el audio…")
    audio = transcripcio.carrega_audio(video)
    if args.srt:
        frases = transcripcio.llegeix_srt(Path(args.srt).expanduser())
        font = "texto del SRT + alineación de todo el texto"
        print(f"Calculando el tiempo de cada palabra ({len(frases)} frases)…")
    else:
        print(f"Transcribiendo con WhisperX ({args.model}). En un Mac Intel puede tardar más que el vídeo…")
        frases = transcripcio.transcriu(audio, args.model)
        font = f"WhisperX {args.model}"
        print("Calculando el tiempo de cada palabra…")
    paraules = transcripcio.a_paraules(transcripcio.alinea(audio, frases))

    dades = {"versio": 1, "video": str(video), "font": font, **exporta.info_video(video), "paraules": paraules}
    anteriors = guarda_anteriors(carpeta)
    if anteriors:
        print(f"He guardado la edición de antes (con las instrucciones y los reels) en {anteriors.name}.")
    (carpeta / TRANSCRIPCIO).write_text(json.dumps(dades, ensure_ascii=False, indent=1), encoding="utf-8")
    (carpeta / ORIGINAL).write_text(edicio.text_editable(paraules), encoding="utf-8")

    projecte = Projecte(carpeta)
    if not args.sense_neteja:
        projecte.neteja()
    trobades = projecte.detecta_instruccions()
    projecte.desa()
    print(f"\nTranscripción hecha en {minuts(time.time() - t0)}: {len(paraules)} palabras.")
    print("\n".join(projecte.resum()))
    _mostra_instruccions(trobades)

    print("\nPreparando la copia ligera para la página de revisión…")
    exporta.fes_proxy(video, carpeta / PROXY, progres=_barra("copia"))
    print(f"\nTodo listo. Abre la página de revisión con:\n  python tallat.py revisa --projecte \"{carpeta}\"")


def ordre_revisa(args) -> None:
    from motor.servidor import crea_servidor

    projecte = _carrega(args)
    proxy = projecte.proxy
    if not projecte.video.exists():  # s'ha mogut o esborrat l'original: la pàgina funciona amb la còpia lleugera
        if not proxy.exists():
            sys.exit(f"No encuentro el vídeo original ({projecte.video}) ni la copia ligera. "
                     "Vuelve a ponerlo donde estaba o dentro de la carpeta del proyecto.")
        print(f"No encuentro el vídeo original ({projecte.video}): la página usa la copia ligera. "
              "Para exportar el vídeo final, vuelve a ponerlo donde estaba o dentro de la carpeta del proyecto.")
    elif not proxy.exists():
        print("Preparando la copia ligera del vídeo (solo la primera vez)…")
        projecte.prepara_proxy(progres=_barra("copia"))
    elif projecte.prepara_proxy(progres=_barra("copia")):  # el vídeo és més nou, o enquadrat d'una altra manera
        print("\nHe preparado la copia ligera del vídeo.")

    for port in range(args.port, args.port + 20):
        try:
            servidor = crea_servidor(projecte, port)
            break
        except OSError:
            continue
    else:
        sys.exit("No encuentro ningún puerto libre para abrir la página.")

    adreca = f"http://127.0.0.1:{servidor.server_port}/"
    print(f"Página de revisión de «{projecte.nom}»: {adreca}", flush=True)  # també si no és un terminal
    print("Deja esta ventana abierta mientras revisas. Para cerrar: Control + C.")
    if not args.sense_navegador:
        webbrowser.open(adreca)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nPágina cerrada. Los cambios ya están guardados.")


def ordre_neteja(args) -> None:
    projecte = _carrega(args)
    projecte.neteja()
    if args.pausa is not None:
        projecte.estat["pausa_maxima"] = args.pausa if args.pausa > 0 else None
    projecte.desa()
    print("\n".join(projecte.resum()))


def ordre_estat(args) -> None:
    projecte = _carrega(args)
    projecte.desa()  # actualitza revisio.txt
    print("\n".join(projecte.resum()))


NOMS_INSTRUCCIO = {"talla": "vuelve a empezar", "zoom": "zoom", "broll": "b-roll / imatges",
                   "sticker": "sticker", "altre": "altres"}


def _mostra_instruccions(llista: list[dict]) -> None:
    if not llista:
        return
    print(f"\nInstrucciones de voz: {len(llista)} (decídelas en la página de revisión)")
    for i in llista:
        dubte = " · sin «Claude»: no se ha quitado nada, parece una orden" if i.get("sense_paraula") else \
            " · no se sabe dónde acaba: no se ha quitado nada" if i.get("dubtosa") else ""
        print(f"  · {minuts(i['inici'])} · {NOMS_INSTRUCCIO.get(i['tipus'], i['tipus'])}: «{i['text']}»{dubte}")


def ordre_instruccions(args) -> None:
    projecte = _carrega(args)
    trobades = projecte.detecta_instruccions()
    projecte.desa()
    _mostra_instruccions(trobades) if trobades else print("No he encontrado ninguna instrucción «Claude, …».")


def ordre_afegeix(args) -> None:
    projecte = _carrega(args)
    n = len(projecte.dades["paraules"])
    if not 0 <= args.paraula < n:
        sys.exit(f"La palabra tiene que ser un número entre 0 y {n - 1} (míralos en el guion: tallat.py guio).")
    treu = None
    if args.treu:
        try:
            a, b = (int(x) for x in args.treu.replace("–", "-").split("-"))
        except ValueError:
            sys.exit("--treu quiere dos palabras: la primera y la última de la instrucción (p. ej. --treu 40-51).")
        if not (0 <= a <= b < n):
            sys.exit(f"--treu: las palabras tienen que estar entre 0 y {n - 1}, y la primera antes que la última.")
        treu = (a, b)
    ins = projecte.afegeix_instruccio(args.tipus, args.paraula, args.text or "", treu)
    p = projecte.dades["paraules"][args.paraula]
    print(f"Instrucción {ins['id']} ({args.tipus}) en «{p['text']}» ({minuts(p['inici'])})."
          + (f" He quitado del vídeo las palabras {treu[0]}–{treu[1]} (donde la decías)." if treu else ""))


def ordre_broll(args) -> None:
    projecte = _carrega(args)
    fitxer = Path(args.fitxer).expanduser()
    try:
        ins = projecte.assigna_recurs(args.instruccio, fitxer, args.durada)
    except KeyError:
        ids = ", ".join(i["id"] for i in projecte.instruccions()) or "cap"
        sys.exit(f"No encuentro la instrucción «{args.instruccio}». Instrucciones: {ids}")
    nom = "Sticker" if ins["tipus"] == "sticker" else "B-roll"
    print(f"{nom} preparado para {ins['id']} ({ins['durada']} s): {projecte.carpeta_instruccions() / ins['fitxer']}")


def ordre_guio(args) -> None:
    projecte = _carrega(args)
    path = projecte.carpeta / muntatge.GUIO
    path.write_text(muntatge.guio(projecte.dades["paraules"]), encoding="utf-8")
    print(f"Guion escrito: {path}")


def ordre_reels(args) -> None:
    projecte = _carrega(args)
    reels, errors = muntatge.llegeix_reels(projecte.carpeta, projecte.dades["paraules"])
    for e in errors:
        print("Error:", e)
    if not reels:
        print(f"No hay ningún reel propuesto en {projecte.carpeta / muntatge.REELS}")
        return
    for r in reels:
        print(f"· {r['id']}: «{r['titol']}» · {minuts(muntatge.durada_estimada(projecte, r))}")
        print(f"    ganxo: {r['ganxo']}")


def ordre_reel(args) -> None:
    projecte = _carrega(args)
    reels, errors = muntatge.llegeix_reels(projecte.carpeta, projecte.dades["paraules"])
    reel = next((r for r in reels if r["id"] == args.id), None)
    if reel is None:
        sys.exit(f"No encuentro el reel «{args.id}». Reels: {', '.join(r['id'] for r in reels) or 'ninguno'}")
    carpeta = muntatge.crea_reel(projecte, reel)
    print("\n".join(Projecte(carpeta).resum()))
    print(f"\nProyecto del reel: {carpeta}")


def ordre_exporta(args) -> None:
    projecte = _carrega(args)
    trams = projecte.trams()
    sortida = projecte.sortida(args.qualitat)
    print(f"Exportando {len(trams)} trozos ({minuts(sum(b - a for a, b in trams))}) en calidad «{args.qualitat}»…")
    t0 = time.time()
    if args.sense_subtitols:
        projecte.estat["subtitols"] = False
    capa = projecte.capa_subtitols(trams, args.qualitat, avis=print)
    exporta.exporta(projecte.font(args.qualitat), trams, sortida, args.qualitat, progres=_barra("exportant"), capa=capa,
                    zooms=projecte.zooms_per_tram(trams), brolls=projecte.brolls(trams),
                    blocs=projecte.blocs(trams), encaix=projecte.encaix, **projecte.opcions_so(trams))
    projecte.desa_talls(sortida, trams)
    avis = exporta.comprova_durades(sortida, sum(b - a for a, b in trams), projecte.dades["fps"])
    if avis:
        print(f"\nAviso: {avis}")
    copia = None
    try:
        copia = exporta.copia_a_carpeta(sortida)
    except OSError as e:
        print(f"\nNo lo he podido copiar a tu carpeta ({e.strerror or e}): está en la del proyecto.")
    print(f"\nHecho en {minuts(time.time() - t0)}:\n  {copia or sortida}")


def ordre_comprova(args) -> None:
    print("Comprobando editor-esp…")
    resultats = comprova.comprovacions()
    print(comprova.informe(resultats))
    if any(estat == "error" for estat, _, _ in resultats):
        sys.exit(1)


def ordre_editors(args) -> None:
    projecte = _carrega(args)
    try:
        if args.trossos:
            carpeta = editors.exporta_trossos(projecte, progres=_barra("exportando los trozos"))
        else:
            carpeta = editors.exporta_editors(projecte, amb_capa=args.amb_subtitols, avis=print,
                                              progres=_barra("haciendo el fondo difuminado"))
    except ValueError as e:
        sys.exit(str(e))
    print(f"A punt: {carpeta}")
    print("Hay un LEEME.txt con los pasos para abrirlo en el editor.")


def ordre_gust(args) -> None:
    try:
        if args.accio == "afegeix":
            regla = gust.afegeix(args.seccio, args.text, args.ajust)
            ajust = regla.get("ajust")
            print(f"Regla {regla['id']} guardada." + (f" Ajuste aplicado: {ajust['clau']} = {ajust['valor']}" if ajust else ""))
        elif args.accio == "treu":
            regla, desfet = gust.treu(args.numero)
            print(f"Regla {regla['id']} quitada." + (" La opción ha vuelto a como estaba antes." if desfet else ""))
        else:
            print(gust.text(gust.llegeix()))
    except KeyError:
        sys.exit(f"No hay ninguna regla con el número {args.numero}.")
    except ValueError as e:
        sys.exit(str(e))


def ordre_moment(args) -> None:
    """Què hi ha en un segon del vídeo: per arreglar el que la persona diu al xat («al segon 12…»)."""
    projecte = _carrega(args)
    trams, on, d_on = projecte.trams(), "el montaje de ahora", "del montaje de ahora (En directo)"
    if args.esborrany:  # el temps de l'últim esborrany, que pot ser d'abans dels darrers canvis
        talls = sorted((projecte.carpeta / EXPORTS).glob("*_esborrany_*.talls.json"), key=lambda f: f.stat().st_mtime)
        if not talls:
            sys.exit("Este proyecto todavía no tiene ningún borrador.")
        trams = [tuple(t) for t in json.loads(talls[-1].read_text(encoding="utf-8"))]
        on = f"el borrador {talls[-1].name.removesuffix('.talls.json')}"
        d_on = f"de {on}"
    original = projecte.al_original(args.segons, trams)
    if original is None:
        sys.exit(f"{on[0].upper()}{on[1:]} dura {sum(b - a for a, b in trams):.1f} s: el segundo {args.segons:g} no está.")
    print(f"Segundo {args.segons:g} {d_on} = segundo {original:.2f} de la grabación.")
    a_prop = [p for p in projecte.paraules() if p["final"] >= original - 2.5 and p["inici"] <= original + 2.5]
    marca_p = lambda p: (("»" if p["inici"] <= original <= p["final"] + 0.15 else "")
                         + (f"{p['id']}:{p.get('correccio', p['text'])}" if p["conservada"] else f"[{p['id']}:{p['text']}]"))
    print("Palabras de alrededor (» la que suena; [entre corchetes] las quitadas):")
    print("  " + " ".join(marca_p(p) for p in a_prop))
    ara = projecte.trams()  # i què hi ha ara en aquell moment
    m = projecte.al_muntatge(original, ara)
    if m is None:
        print("Ahora este momento ya no sale en el vídeo (se ha quitado).")
        return
    titol = projecte.titol(ara)
    if titol and titol["inici"] <= m < titol["final"]:
        print(f"Sale el título gancho: «{titol['text'].replace(chr(10), ' / ')}».")
    for g in projecte.grafics(ara):
        if g["inici"] <= m < g["final"]:
            print(f"Sale el gráfico {g['id']} ({g['tipus']}, {g['estil']}): "
                  f"«{g['text'] or ' / '.join(p['text'] for p in g['punts'])}».")
    for nom, recursos in (("B-roll", projecte.brolls(ara)), ("Sticker", projecte.stickers(ara))):
        for r in recursos:
            if r["inici"] <= m < r["inici"] + r["durada"]:
                print(f"Sale el {nom.lower()} {r['id']} ({Path(r['fitxer']).name}, {r['durada']:g} s).")


def ordre_titol(args) -> None:
    projecte = _carrega(args)
    if args.treu or args.text is not None:
        if args.treu:
            projecte.estat["titol"] = None
        else:  # les línies, separades amb «|» (o amb salts de línia de debò)
            text = "\n".join(l.strip() for l in args.text.replace("|", "\n").split("\n"))
            projecte.estat["titol"] = edicio.titol_net({"text": text, "durada": args.durada})
            if projecte.estat["titol"] is None:
                sys.exit("El título no puede estar vacío.")
        projecte.estat["revisio"] = projecte.estat.get("revisio", 0) + 1  # la pàgina oberta s'hi posa al dia
        projecte.desa()
    titol = edicio.titol_net(projecte.estat.get("titol"))
    if not titol:
        print("Este vídeo no tiene título gancho.")
        return
    estil = projecte.estil()["titol"]
    print("Título gancho (las partes *entre asteriscos* salen destacadas):")
    print("\n".join(f"  {l}" for l in titol["text"].split("\n")))
    print(f"Duración: {titol['durada'] or estil['durada']} s · estilo del kit: {estil['animacio']}, {estil['alineacio']}"
          + (" · oculta los subtítulos mientras sale" if estil.get("amaga_subtitols") else ""))


def _segons(t: float) -> str:
    return f"{t:.1f}".replace(".", ",") + " s"


def ordre_grafics(args) -> None:
    """El pla de gràfics: el que necessita l'assistent per fer-lo (les frases i la marca) i el que hi ha
    (amb les notes de la persona). `proposa` hi desa un pla nou i `canvia` només toca els gràfics que
    esmenta (per atendre les notes); motor/grafics.py diu com es fusionen."""
    projecte = _carrega(args)
    if args.accio == "captura":
        if not args.fitxer:
            sys.exit("Falta la dirección: tallat.py grafics captura https://… --projecte …")
        print(f"Haciendo la captura de {args.fitxer}…", flush=True)
        try:
            with tempfile.TemporaryDirectory() as temporal:
                nom = projecte.importa_imatge(grafics.captura_web(args.fitxer, Path(temporal) / "captura.png"))
        except (RuntimeError, ValueError, subprocess.TimeoutExpired) as e:
            sys.exit(f"No he podido hacer la captura: {e}")
        if args.grafic:
            g = next((x for x in projecte.estat.get("grafics") or [] if x["id"] == args.grafic), None)
            if g is None or g["tipus"] != "web":
                sys.exit(f"No hay ningún gráfico web «{args.grafic}» en el plan (la captura está en {projecte.carpeta_imatges / nom}).")
            g["imatge"] = nom
            g["text"] = g["text"] or grafics.adreca_curta(args.fitxer)
            projecte.estat["revisio"] = projecte.estat.get("revisio", 0) + 1
            projecte.desa()
            print(f"Hecho: la captura ya está en el gráfico {args.grafic}.")
        else:
            print(f"Hecho. En el plan, pon \"imatge\": \"{nom}\" (y \"text\": \"{grafics.adreca_curta(args.fitxer)}\").")
        print(f"Para verla: {projecte.carpeta_imatges / nom}")
        return
    if args.accio == "fotogrames":
        trams = projecte.trams()
        situats = projecte.grafics(trams)
        if not situats:
            sys.exit("Este vídeo todavía no tiene ningún gráfico que salga en el vídeo.")
        proxy = projecte.proxy
        quadres = [{"t": projecte.al_original(g["inici"] + min(1.0, (g["final"] - g["inici"]) / 2), trams),
                    "limits": g["limits"]} for g in situats]
        desti = grafics.full_de_fotogrames(proxy if proxy.exists() else projecte.video, quadres,
                                           projecte.carpeta / "grafics-fotogrames.png")
        print(f"Fotogramas: {desti}")
        print(f"Uno por gráfico, en filas de {grafics.COLUMNES}, de izquierda a derecha y de arriba abajo:")
        print("  " + "  ".join(f"{g['id']} ({_segons(g['inici'])}, {g['posicio']})" for g in situats))
        print("Oscurecido: donde no puede ir ningún gráfico (lo que tapa Instagram y los subtítulos). "
              "El recuadro amarillo: donde puede ir (dalt, mig o baix, o un número de 0 a 1).")
        return
    if args.accio:
        if not args.fitxer:
            sys.exit(f"Falta el archivo con el plan: tallat.py grafics {args.accio} PLA.json --projecte …")
        try:
            text = sys.stdin.read() if args.fitxer == "-" else Path(args.fitxer).expanduser().read_text(encoding="utf-8")
            pla = json.loads(text)
        except (OSError, json.JSONDecodeError) as e:
            sys.exit(f"No puedo leer el plan: {e}")
        pla = pla.get("grafics") if isinstance(pla, dict) else pla
        try:
            pla = projecte.importa_imatges(pla)  # les imatges que són camins de fitxers, al projecte
            manera = "de-nou" if args.de_nou else args.accio
            actuals = projecte.estat.get("grafics") or []
            # Cada pla que hi desa Claude és una ronda del tauler (menys els retocs dels que acaba de proposar).
            ronda = grafics.ronda_del_pla(actuals, pla, projecte.estat.get("ronda", 0), manera)
            projecte.estat["grafics"] = grafics.fusiona(actuals, pla,
                                                        len(projecte.dades["paraules"]), manera, ronda)
        except ValueError as e:
            sys.exit(str(e))
        if ronda > projecte.estat.get("ronda", 0):  # també si només n'ha tret o no n'ha canviat cap: Claude ha respost
            projecte.estat["ronda"] = ronda
            # Els «Potser» i les notes de les altres peces (zooms, b-roll, sons) ja s'han atès en aquesta ronda.
            projecte.estat["vots"] = {}
        projecte.estat["revisio"] = projecte.estat.get("revisio", 0) + 1  # la pàgina oberta s'hi posa al dia
        projecte.desa()
    trams = projecte.trams()
    marca_kit = projecte.estil().get("marca") or {}
    pla = projecte.estat.get("grafics") or []
    situats = {g["id"]: g for g in projecte.grafics(trams, amb_alternatives=True)}
    frases = projecte.frases(trams)
    if args.json:
        print(json.dumps({"marca": {k: marca_kit.get(k) for k in ("compte", "public", "energia", "grafics", "crida",
                                                                  "colors_prohibits")},
                          "durada": round(sum(b - a for a, b in trams), 2), "frases": frases,
                          "grafics": [{**g, **({"inici": situats[g["id"]]["inici"], "final": situats[g["id"]]["final"]}
                                               if g["id"] in situats else {})} for g in pla],
                          "altres_peces": _altres_peces(projecte)},
                         ensure_ascii=False, indent=1))
        return
    energia = marca_kit.get("energia") or ["net"]
    energia = ", ".join(energia if isinstance(energia, list) else [energia])
    quants = marca_kit.get("grafics") or "normal"
    print(f"Marca: estilo de los gráficos «{energia}» · cuántos: «{quants}» ({grafics.DENSITAT.get(quants, '')})"
          + (f" · llamada: «{marca_kit['crida']}»" if marca_kit.get("crida") else " · sin llamada en la marca")
          + (f" · cuenta: «{marca_kit['compte']}»" if marca_kit.get("compte") else ""))
    print(f"Vídeo de {_segons(sum(b - a for a, b in trams))}. Frases (dónde empieza · palabras · texto):")
    for f in frases:
        print(f"  {_segons(f['inici']):>8}  {f['paraula']}–{f['fins']}  {f['text']}")
    if not pla:
        print("Todavía no hay ningún plan de gráficos. Para guardar uno: tallat.py grafics proposa PLA.json --projecte …")
        _mostra_altres_peces(projecte)
        return
    notes = sum(1 for g in pla if g["estat"] == "canvia")
    ronda = projecte.estat.get("ronda", 0)
    print(f"Plan de gráficos ({len(pla)}" + (f"; {notes} por cambiar" if notes else "") + (f"; ronda {ronda}" if ronda else "")
          + "). Voto de la persona en el tablero: SÍ, QUIZÁ, NO o «por mirar»:")
    vots = {"si": "SÍ", "potser": "QUIZÁ", "no": "NO"}
    for g in pla:
        s = situats.get(g["id"])
        on = (_segons(s["inici"]) if s else "—" if g["estat"] == "tret"
              else "sin texto" if g["tipus"] == "crida" and not g["text"] else "fuera del vídeo")
        text = g["text"] or ("(la llamada de la marca)" if g["tipus"] == "crida" else "")
        text = " · ".join(x for x in (g.get("de"), g.get("xifra"), text) if x)
        punts = " / ".join(("→ " if p.get("costat") == "enviat" else "") + p["text"] for p in g["punts"])
        punts = f"{g['forma']}, {g['costat']}" if g["tipus"] == "anotacio" else punts
        estat = {"canvia": "CAMBIA", "mantingut": "mantingut", "tret": "tret"}.get(g["estat"], "proposat")
        vot = vots.get(g.get("vot")) or {"mantingut": "SÍ", "tret": "NO"}.get(g["estat"], "por mirar")
        extra = "".join(x for x in (f" · grupo {g['grup']}" if g.get("grup") else "",
                                    " (alternativa: no sale hasta que la elija)" if s and s.get("alternativa") else "",
                                    " · lo puso la persona" if g.get("origen") == "teu" else "") if x)
        print(f"  {g['id']:>4}  {g['tipus']:<11} {on:>14}  palabra {g['paraula'] if g['paraula'] is not None else 'final'}"
              f"  {g.get('estil') or '(marca)'}  {estat} · {vot}{extra}  «{text}»" + (f" [{punts}]" if punts else ""))
        if g["nota"]:
            print(f"        nota: «{g['nota']}»")
    _mostra_altres_peces(projecte)


def _altres_peces(projecte) -> dict:
    """Els «Potser» i les notes de les peces que no són gràfics (b-roll, stickers, zooms i sons), per a Claude."""
    return {k: v for k, v in (projecte.estat.get("vots") or {}).items() if v["vot"] == "potser" or v["nota"]}


def _mostra_altres_peces(projecte) -> None:
    altres = _altres_peces(projecte)
    if not altres:
        return
    vots = {"si": "SÍ", "potser": "QUIZÁ", "no": "NO"}
    print("Las otras piezas del tablero con un QUIZÁ o una nota (b-roll, stickers, zooms y sonidos):")
    paraules = projecte.dades["paraules"]
    for clau, v in altres.items():
        on = ""
        if v.get("paraula") is not None and v["paraula"] < len(paraules):
            k = v["paraula"]
            on = f"  palabra {k}, en «{' '.join(w['text'].strip() for w in paraules[k:k + 6])}»"
        print(f"  {v.get('nom') or clau}{on}  {vots[v['vot']]}" + (f"  nota: «{v['nota']}»" if v["nota"] else ""))


NOMS_MARCA = {"compte": "La cuenta", "public": "Quién lo mira", "referencia": "Reel de referencia",
              "color_text": "Color del texto", "color_principal": "Color principal", "color_destacat": "Color destacado",
              "color_secundari": "Color secundario", "color_clar": "Color claro", "color_fosc": "Color oscuro",
              "colors_prohibits": "Nunca", "lletra_titols": "Letra de los títulos", "lletra_text": "Letra del texto",
              "lletra_accent": "Letra de acento", "lletra_ma": "Letra a mano",
              "majuscules_ma": "Letra a mano en mayúsculas", "energia": "Estilo de los gráficos", "grafics": "Cuántos gráficos",
              "crida": "Llamada a la acción"}


def _valor_cli(text: str):
    """Un valor escrit a l'ordre: número, sí/no, null o text."""
    t = text.strip()
    if t.lower() in ("sí", "si", "true"):
        return True
    if t.lower() in ("no", "false"):
        return False
    if t.lower() in ("null", "cap", ""):
        return None
    try:
        return int(t) if re.fullmatch(r"-?\d+", t) else float(t.replace(",", ".")) if re.fullmatch(r"-?\d+[.,]\d+", t) else t
    except ValueError:
        return t


def ordre_estil(args) -> None:
    """L'estil d'aquest vídeo: el del seu kit amb el que aquest vídeo hi ha canviat. Amb --tria, un dels estils de
    tot el vídeo; amb SECCIO.CLAU=VALOR, una opció només d'aquest vídeo; --a-tots ho passa al kit (tots els vídeos)
    i --treu torna a l'estil del kit."""
    projecte = _carrega(args)
    estils = marca.estils_video()
    propi = projecte.estat.get("estil") or {}
    if args.treu:
        propi = {}
    if args.tria:
        e = next((x for x in estils if x["id"] == args.tria), None)
        if e is None:
            sys.exit(f"No conozco el estilo «{args.tria}». Hay: {', '.join(x['id'] for x in estils)}")
        propi = {**{k: v for k, v in propi.items() if k == "so"},
                 "subtitols": dict(e["subtitols"]), "titol": dict(e["titol"]), "broll": dict(e["broll"]), "grafics": e["grafics"]}
    for parell in args.valors:
        clau, igual, valor = parell.partition("=")
        seccio, punt, opcio = clau.partition(".")
        if seccio == "grafics" and not punt and igual:
            propi["grafics"] = valor.strip()
            continue
        if not igual or not punt or seccio not in marca.SECCIONS_VIDEO:
            sys.exit(f"No entiendo «{parell}». Usa SECCIO.CLAU=VALOR, con una de estas secciones: "
                     f"{', '.join(marca.SECCIONS_VIDEO)} (o grafics=net|mac|scrapbook|editorial)")
        try:
            propi.setdefault(seccio, {}).update(marca.valida(seccio, {opcio: _valor_cli(valor)}))
        except ValueError as e:
            sys.exit(str(e))
    canviat = args.treu or args.tria or args.valors
    if canviat:
        projecte.estat["estil"] = marca.neteja_estil_video(propi)
    if args.a_tots:
        queda = marca.passa_al_kit(projecte.estat.get("estil") or {}, kit=projecte.kit())
        projecte.estat["estil"] = queda  # els colors i les lletres que la marca ja posa no poden ser de tots
        if queda:
            print("Los colores y las letras que este vídeo cambia se quedan solo en este vídeo (los de todos los vídeos "
                  "están en la marca: tallat.py marca).")
        canviat = True
    if canviat:
        projecte.estat["revisio"] = projecte.estat.get("revisio", 0) + 1  # la pàgina oberta s'hi posa al dia
        projecte.desa()
    propi = projecte.estat.get("estil") or {}
    nom = next((k["nom"] for k in marca.kits() if k["id"] == projecte.kit()), projecte.kit())
    igual = next((e["id"] for e in estils if all(propi.get(s) == e[s] for s in ("subtitols", "titol", "broll", "grafics"))), None)
    noms = ", ".join(f"{e['id']} ({e['nom']})" for e in estils)
    print(f"Estilos de todo el vídeo: {noms}")
    if not propi:
        print(f"Este vídeo usa el estilo del kit «{nom}» tal como es (el de todos los vídeos de este kit).")
        return
    print(f"Este vídeo parte del kit «{nom}»" + (f" con el estilo «{igual}»" if igual else "") + ". Cambia:")
    for seccio, valors in propi.items():
        print(f"  {seccio}: {json.dumps(valors, ensure_ascii=False)}")
    print("Para pasarlo a todos los vídeos de este kit: --a-tots. Para volver al del kit: --treu.")


def ordre_marca(args) -> None:
    """La marca d'un kit: la mostra i, amb CLAU=VALOR, la desa (i l'escampa pel kit)."""
    kit = Projecte(Path(args.projecte).expanduser().resolve()).kit() if args.projecte else marca.resol(args.kit)
    canvis, biblioteca = {}, marca.biblioteca_lletres()["lletres"]
    for parell in args.valors:
        clau, igual, valor = parell.partition("=")
        if not igual or clau not in NOMS_MARCA:
            sys.exit(f"No entiendo «{parell}». Usa CLAU=VALOR con una de estas claves: {', '.join(NOMS_MARCA)}")
        valor = valor.strip()
        if clau.startswith("lletra_") and valor:
            # Una lletra gratuïta (pel nom o per l'id): es baixa al kit, amb la cursiva si en té.
            lletra = next((l for l in biblioteca if valor.lower() in (l["id"], l["nom"].lower())), None)
            if lletra:
                try:
                    marca.baixa_lletra(lletra["id"], kit=kit, seccio="marca", clau=clau)
                except ConnectionError as e:
                    sys.exit(str(e))
                continue
        if clau == "energia":  # un o uns quants, separats amb comes
            canvis[clau] = [v.strip() for v in valor.split(",") if v.strip()]
            continue
        if clau == "majuscules_ma":  # sí o no
            if valor.lower() not in ("sí", "si", "no", "true", "false", "1", "0"):
                sys.exit("majuscules_ma tiene que ser sí o no")
            canvis[clau] = valor.lower() in ("sí", "si", "true", "1")
            continue
        canvis[clau] = None if valor.lower() in ("", "null", "cap") and (clau.startswith(("color_", "lletra_"))) else valor
    if canvis:
        try:
            marca.desa("marca", canvis, kit=kit)
        except ValueError as e:
            sys.exit(str(e))
    m = marca.carrega(kit=kit)["marca"]
    nom = next((k["nom"] for k in marca.kits() if k["id"] == kit), kit)
    if not any(m.get(c) for c in NOMS_MARCA if c.startswith(("compte", "color_", "lletra_"))):
        print(f"El kit «{nom}» todavía no tiene marca. Haz la entrevista de marca (ver SKILL.md).")
        return
    print(f"La marca del kit «{nom}» (los colores y las letras ya se han puesto en los subtítulos, el título y el b-roll):")
    for clau, etiqueta in NOMS_MARCA.items():
        if m.get(clau) not in (None, "", [], False):
            valor = m[clau]
            print(f"  {etiqueta}: {', '.join(valor) if isinstance(valor, list) else 'sí' if valor is True else valor}")


def _mmss(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


_trams_de: dict = {}  # carpeta → (projecte, trams): un sol cop per projecte encara que hi hagi moltes notes


def _al_video(nota: dict) -> float | None:
    """El segon del vídeo editat on cau la nota (el que la persona veia sota el vídeo), amb els talls d'ara."""
    if nota.get("inici") is None or not nota.get("projecte"):
        return None
    try:
        if nota["projecte"] not in _trams_de:
            projecte = Projecte(Path(nota["projecte"]))
            _trams_de[nota["projecte"]] = (projecte, projecte.trams())
        projecte, trams = _trams_de[nota["projecte"]]
        return projecte.al_muntatge(nota["inici"], trams)
    except (OSError, ValueError, KeyError):
        return None


def ordre_notes(args) -> None:
    """Les notes que la persona deixa a la pàgina per a l'assistent (es desen a la gravació sencera, també les
    dels reels). Sense opcions, les ensenya; amb --espera, espera les que envii i les agafa; amb --respon, hi respon."""
    carpeta = arrel_de(Path(args.projecte).expanduser().resolve())
    if not (carpeta / TRANSCRIPCIO).exists():
        sys.exit(f"No encuentro el proyecto: {carpeta}")
    if args.respon:
        id_, text = args.respon
        try:  # «3» o «3.2» (la nota 3, la segona vegada que se t'ha donat: la que diu --espera)
            num, _, cop = id_.partition(".")
            notes.respon(carpeta, int(num), text, pregunta=args.pregunta, cop=int(cop) if cop else None, al_xat=args.al_xat)
        except (KeyError, ValueError) as e:
            sys.exit(str(e).strip("'\""))
        print(f"Respuesta guardada en la nota {num}: la persona la ve en la página.")
        return
    if args.espera:
        segons = max(1.0, args.minuts * 60)
        print(f"Espero las notas de la página (como mucho {minuts(segons)}). Mientras tanto, la página dice «Conectado con Claude».",
              flush=True)
        preses = notes.espera(carpeta, segons)
        if not preses:
            print("Todavía no ha llegado ninguna nota. Vuelve a esperarlas cuando quieras.")
            return
        print("Ha llegado 1 nota:\n" if len(preses) == 1 else f"Han llegado {len(preses)} notas:\n")
        numeros = notes.numeros_pagina(notes.llegeix(carpeta)["notes"], _al_video)
        for nota in preses:
            print(notes.text_per_a_claude(nota, _mmss, _al_video(nota), carpeta, numeros.get(nota["id"])) + "\n")
        print("Hazlas y responde cada una con el número que dice «Para responderla» (la persona ve la respuesta en la página):")
        print(f'  tallat.py notes --projecte "{carpeta}" --respon NÚMERO "Hecho: …"   (si no lo tienes claro, añade --pregunta)')
        print("Después, vuelve a esperarlas con --espera.")
        return
    totes = notes.llegeix(carpeta)["notes"]
    if not totes:
        print("Todavía no hay ninguna nota.")
        return
    noms = {"esborrany": "por enviar", "enviada": "enviada", "treballant": "agafada", "feta": "feta", "pregunta": "pregunta"}
    numeros = notes.numeros_pagina(totes, _al_video)
    for nota in totes:
        print(f"[{noms.get(nota['estat'], nota['estat'])}] "
              f"{notes.text_per_a_claude(nota, _mmss, _al_video(nota), carpeta, numeros.get(nota['id']))}")


def ordre_encaix(args) -> None:
    projecte = _carrega(args)
    info = exporta.info_video(projecte.proxy if not projecte.video.exists() else projecte.video)
    horitzontal = info["amplada"] * 16 > info["alcada"] * 9 if projecte.video.exists() else None
    if args.encaix is None:
        print(f"Ahora: «{projecte.encaix}»." + ("" if horitzontal is not False else " (El vídeo ya es vertical: no cambia nada.)"))
        return
    projecte.estat["encaix"] = args.encaix
    projecte.estat["revisio"] = projecte.estat.get("revisio", 0) + 1  # la pàgina oberta s'hi posa al dia
    projecte.desa()
    if not projecte.video.exists():
        sys.exit("Guardado, pero no encuentro el vídeo original para rehacer la copia ligera: vuelve a ponerlo donde estaba.")
    if projecte.prepara_proxy(progres=_barra("copia")):
        print("\nHecho: he rehecho la copia ligera (si tienes la página abierta, se volverá a cargar).")
    print({"retalla": "Ahora el vídeo horizontal se recorta: se queda el centro.",
           "difumina": "Ahora el vídeo horizontal sale entero, con el mismo vídeo difuminado arriba y abajo."}[args.encaix])


def ordre_destaca(args) -> None:
    projecte = _carrega(args)
    destacades = projecte.estat.setdefault("destacades", {})
    if args.automatic:
        destacades.clear()
    total = len(projecte.dades["paraules"])
    for ids, valor in ((args.si or [], True), (args.no or [], False)):
        for id_ in ids:
            if not 0 <= id_ < total:
                sys.exit(f"No hay ninguna palabra con el número {id_} (hay de 0 a {total - 1}).")
            destacades[id_] = valor
    if args.si or args.no or args.automatic:
        projecte.estat["revisio"] = projecte.estat.get("revisio", 0) + 1  # la pàgina oberta s'hi posa al dia
        projecte.desa()
    claus = [(w["id"], w["text"]) for l in projecte.linies_subtitols() for w in l["paraules"] if w["clau"]]
    print(f"Palabras destacadas en los subtítulos ({len(claus)}):")
    print("  " + "  ".join(f"{i}:{text}" for i, text in claus))
    triades = sorted(destacades.items())
    if triades:
        print("Elegidas a mano (el resto las elige editor-esp): "
              + ", ".join(f"{i} {'sí' if v else 'no'}" for i, v in triades))
    if not projecte.estil_subtitols().get("clau_grans"):
        print("Aviso: el kit de este vídeo no hace más grandes las palabras destacadas. "
              "Se activa en la página: Viste → Subtítulos → Más opciones → Palabras destacadas.")


PESOS = {"thin": "100", "extralight": "200", "light": "300", "regular": "400", "book": "400", "normal": "400",
         "medium": "500", "semibold": "600", "bold": "700", "extrabold": "800", "black": "900", "heavy": "900"}


def _pes_de(nom: str) -> tuple[str, bool]:
    """El gruix i si és cursiva, pel nom del fitxer («LaMeva-Italic» → 400 cursiva; «…Var…» → variable)."""
    baix = nom.lower().replace(" ", "").replace("-", "").replace("_", "")
    cursiva = "italic" in baix or "oblique" in baix
    if "var" in baix:
        return "var", cursiva
    pes = next((v for k, v in sorted(PESOS.items(), key=lambda x: -len(x[0])) if k in baix), "400")
    return pes, cursiva


def ordre_kit(args) -> None:
    try:
        if args.accio == "nou":
            kit = marca.crea_kit(args.nom, args.copia_de)
            print(f"Kit «{args.nom}» creado (id: {kit}).")
        elif args.accio == "nom":
            marca.canvia_nom(args.kit, args.nom)
            print(f"El kit {args.kit} ahora se llama «{args.nom}».")
        elif args.accio == "per-defecte":
            marca.fes_per_defecte(args.kit)
            print(f"Los vídeos nuevos usarán el kit {args.kit}.")
        elif args.accio == "tria":
            projecte = _carrega(args)
            projecte.tria_kit(args.kit)
            print(f"«{projecte.nom}» usa el kit {args.kit}.")
        elif args.accio == "exporta":
            nom, contingut = marca.empaqueta_kit(args.kit)
            desti = Path(args.a).expanduser() / nom
            desti.write_bytes(contingut)
            print(f"Kit guardado en {desti}. Si lleva una fuente tuya, comprueba que la puedes compartir.")
        elif args.accio == "importa":
            kit = marca.importa_kit(Path(args.fitxer).expanduser().read_bytes())
            print(f"Kit importado (id: {kit}). Elígelo para un vídeo en la página o con «tallat.py kit tria».")
        elif args.accio == "esborra":
            desti = marca.esborra_kit(args.kit)
            print(f"Kit quitado de la lista. Si lo quieres recuperar, está en {desti}.")
        elif args.accio == "lletres":
            biblioteca = marca.biblioteca_lletres()
            for grup, nom in biblioteca["grups"].items():
                print(f"{nom}: " + ", ".join(f"{l['nom']} ({l['id']})" for l in biblioteca["lletres"] if l["grup"] == grup))
            print("\nPara poner una en un kit: tallat.py kit lletra ID [--kit KIT]. Se descarga la primera vez.")
        elif args.accio == "font":
            origen = Path(args.fitxer).expanduser()
            familia = args.familia or re.split(r"[-_ ]", origen.stem)[0]
            pes, cursiva = _pes_de(origen.stem) if args.pes is None else (args.pes, False)
            desti = marca.afegeix_font(origen.read_bytes(), origen.name, familia, pes, args.cursiva or cursiva, kit=args.kit)
            print(f"Letra «{familia}» añadida al kit {marca.resol(args.kit)} ({desti.name}). "
                  "Úsala con tallat.py marca (lletra_text=…, lletra_titols=…) o desde la página.")
        elif args.accio == "lletra":
            if not any(l["id"] == args.id for l in marca.biblioteca_lletres()["lletres"]):
                sys.exit(f"No conozco la letra «{args.id}». Mira cuáles hay con: tallat.py kit lletres")
            estil = marca.baixa_lletra(args.id, kit=args.kit)
            print(f"Los subtítulos del kit {marca.resol(args.kit)} usan «{estil['font']}».")
        else:
            for k in marca.kits():
                print(f"{'★' if k['per_defecte'] else ' '} {k['id']}: {k['nom']}")
            print(f"\n★ = el kit por defecto (el de los vídeos nuevos). Los kits están en {marca.KITS}.")
    except KeyError as e:
        sys.exit(f"No encuentro el kit «{e.args[0]}». Mira cuáles hay con: tallat.py kit")
    except (ValueError, OSError) as e:  # ConnectionError (no s'ha pogut baixar una lletra) és un OSError
        sys.exit(str(e))


def main() -> None:
    sys.stdout.reconfigure(line_buffering=True)  # que els missatges surtin al moment
    entorn.prepara()  # les eines que ha instal·lat prepara.sh (ffmpeg, Node), al davant del PATH
    p = argparse.ArgumentParser(prog="editor-esp", description="Editor de reels en castellano, por palabras (editor-esp, versión modificada de editor-esp).")
    sub = p.add_subparsers(dest="ordre", required=True)

    t = sub.add_parser("transcriu", help="Transcribe un vídeo con tiempo por palabra")
    t.add_argument("video")
    t.add_argument("--projecte", required=True, help="Carpeta donde se guarda el trabajo (fuera del repositorio)")
    t.add_argument("--srt", help="Texto ya transcrito (p. ej. exportado de Descript); solo se alinea el tiempo")
    t.add_argument("--model", default="large-v3", help="Modelo de WhisperX si no hay --srt")
    t.add_argument("--forca", action="store_true", help="Rehace la transcripción aunque ya haya una")
    t.add_argument("--sense-neteja", action="store_true", help="No quites las muletillas automáticamente")
    t.set_defaults(func=ordre_transcriu)

    ra = sub.add_parser("realinea", help="Vuelve a calcular cuándo empieza y acaba cada palabra (sin tocar la edición)")
    ra.add_argument("--projecte", required=True)
    ra.set_defaults(func=ordre_realinea)

    ct = sub.add_parser("compara-temps", help="Compara el tiempo de cada palabra con el de un SRT (p. ej. de Descript)")
    ct.add_argument("--projecte", required=True)
    ct.add_argument("--srt", required=True)
    ct.set_defaults(func=ordre_compara_temps)

    r = sub.add_parser("revisa", help="Abre la página de revisión en el navegador")
    r.add_argument("--projecte", required=True)
    r.add_argument("--port", type=int, default=8766)
    r.add_argument("--sense-navegador", action="store_true", help="No abras el navegador automáticamente")
    r.set_defaults(func=ordre_revisa)

    n = sub.add_parser("neteja", help="Quita muletillas y palabras a medio decir, y acorta silencios")
    n.add_argument("--projecte", required=True)
    n.add_argument("--pausa", type=float, help="Silencio máximo en segundos (0 = no acortar)")
    n.set_defaults(func=ordre_neteja)

    e = sub.add_parser("estat", help="Muestra qué se ha quitado y cuánto durará")
    e.add_argument("--projecte", required=True)
    e.set_defaults(func=ordre_estat)

    ins = sub.add_parser("instruccions", help="Detecta las instrucciones de voz «Claude, …»")
    ins.add_argument("--projecte", required=True)
    ins.set_defaults(func=ordre_instruccions)

    af = sub.add_parser("afegeix", help="Añade a mano una instrucción (b-roll, sticker, zoom) en una palabra")
    af.add_argument("tipus", choices=["broll", "sticker", "zoom"])
    af.add_argument("--paraula", type=int, required=True, help="Número de palabra (el del guion)")
    af.add_argument("--text", help="Descripción (p. ej. «una lavadora»)")
    af.add_argument("--treu", metavar="A-B", help="Las palabras donde se decía la instrucción, para quitarlas del vídeo (p. ej. 40-51)")
    af.add_argument("--projecte", required=True)
    af.set_defaults(func=ordre_afegeix)

    br = sub.add_parser("broll", aliases=["sticker"],
                        help="Asigna un archivo a una instrucción de b-roll (vídeo o imagen) o de sticker (PNG)")
    br.add_argument("instruccio", help="Id de la instrucción (p. ej. i133 o m290-1)")
    br.add_argument("fitxer")
    br.add_argument("--durada", type=float, help="Segundos (por defecto, los del estilo)")
    br.add_argument("--projecte", required=True)
    br.set_defaults(func=ordre_broll)

    g = sub.add_parser("guio", help="Escribe el guion por párrafos para el primer montaje")
    g.add_argument("--projecte", required=True)
    g.set_defaults(func=ordre_guio)

    rl = sub.add_parser("reels", help="Valida los reels propuestos y muestra su duración")
    rl.add_argument("--projecte", required=True)
    rl.set_defaults(func=ordre_reels)

    r1 = sub.add_parser("reel", help="Crea el proyecto de uno de los reels propuestos")
    r1.add_argument("id")
    r1.add_argument("--projecte", required=True)
    r1.set_defaults(func=ordre_reel)

    x = sub.add_parser("exporta", help="Exporta el vídeo cortado a MP4 vertical")
    x.add_argument("--projecte", required=True)
    x.add_argument("--qualitat", choices=list(exporta.QUALITATS), default="esborrany")
    x.add_argument("--sense-subtitols", action="store_true", help="Exporta sin subtítulos")
    x.set_defaults(func=ordre_exporta)

    co = sub.add_parser("comprova", help="Revisa que el ordenador tenga todo lo que necesita editor-esp")
    co.set_defaults(func=ordre_comprova)

    ed = sub.add_parser("editors", help="Prepara el montaje para acabarlo en Premiere, Final Cut, DaVinci o CapCut")
    ed.add_argument("--projecte", required=True)
    ed.add_argument("--amb-subtitols", action="store_true", help="Incluye los subtítulos, el título y los gráficos animados (capa transparente)")
    ed.add_argument("--trossos", action="store_true", help="Cada trozo como un clip aparte (para CapCut o iMovie)")
    ed.set_defaults(func=ordre_editors)

    gu = sub.add_parser("gust", help="Las reglas de tu gusto (correcciones que sirven para los vídeos siguientes)")
    gs = gu.add_subparsers(dest="accio")
    ga = gs.add_parser("afegeix", help="Añade una regla")
    ga.add_argument("seccio", choices=list(gust.SECCIONS))
    ga.add_argument("text", help="La regla, en palabras de la persona")
    ga.add_argument("--ajust", help="Opción que cambia, p. ej. subtitols.mida=0.09 o farciment.deixa=vale")
    gt = gs.add_parser("treu", help="Quita una regla (y deshace su ajuste)")
    gt.add_argument("numero", type=int)
    gu.set_defaults(func=ordre_gust)

    ki = sub.add_parser("kit", help="Los kits de estilo: lístalos, crea, elige uno para un vídeo, expórtalos o impórtalos")
    ks = ki.add_subparsers(dest="accio")
    kn = ks.add_parser("nou", help="Crea un kit (copia de otro con --copia-de; si no, el estilo neutro)")
    kn.add_argument("nom")
    kn.add_argument("--copia-de", help="El id del kit que se copia")
    km = ks.add_parser("nom", help="Cambia el nombre de un kit")
    km.add_argument("kit")
    km.add_argument("nom")
    kd = ks.add_parser("per-defecte", help="El kit de los vídeos nuevos (y el que cambian las reglas del gusto)")
    kd.add_argument("kit")
    kt = ks.add_parser("tria", help="Elige el kit de un vídeo (o de un reel)")
    kt.add_argument("kit")
    kt.add_argument("--projecte", required=True)
    ke = ks.add_parser("exporta", help="Guarda el kit en un .zip para pasárselo a alguien")
    ke.add_argument("kit")
    ke.add_argument("--a", default=".", help="Carpeta donde se guarda (por defecto, la actual)")
    kim = ks.add_parser("importa", help="Añade un kit de un .zip")
    kim.add_argument("fitxer")
    kb = ks.add_parser("esborra", help="Quita un kit de la lista (se guarda en ~/.tallat-es/kits-esborrats)")
    kb.add_argument("kit")
    ks.add_parser("lletres", help="Las letras gratuitas que se pueden poner en un kit")
    kf = ks.add_parser("font", help="Añade al kit una letra tuya (un archivo .ttf, .otf, .woff o .woff2)")
    kf.add_argument("fitxer")
    kf.add_argument("--familia", help="El nombre de la letra (si no, el principio del nombre del archivo)")
    kf.add_argument("--pes", help="El grosor (400, 700…) o «var» si es variable (si no, por el nombre del archivo)")
    kf.add_argument("--cursiva", action="store_true", help="Es la versión cursiva")
    kf.add_argument("--kit", help="El kit (si no, el de por defecto)")
    kl = ks.add_parser("lletra", help="Pone una letra gratuita en los subtítulos de un kit (la descarga la primera vez)")
    kl.add_argument("id", help="El id de la letra (tallat.py kit lletres)")
    kl.add_argument("--kit", help="El kit (si no, el de por defecto)")
    ki.set_defaults(func=ordre_kit)

    mo = sub.add_parser("moment", help="Qué hay en un segundo del vídeo (palabras, título, b-roll, stickers)")
    mo.add_argument("segons", type=float)
    mo.add_argument("--projecte", required=True)
    mo.add_argument("--esborrany", action="store_true", help="El segundo es del último borrador, no del montaje de ahora")
    mo.set_defaults(func=ordre_moment)

    ti = sub.add_parser("titol", help="El título gancho: un texto diseñado en los primeros segundos")
    ti.add_argument("--projecte", required=True)
    ti.add_argument("text", nargs="?", help="Las líneas separadas con «|»; lo que va *entre asteriscos* sale destacado")
    ti.add_argument("--durada", type=float, help="Segundos (si no, los del kit)")
    ti.add_argument("--treu", action="store_true", help="Quita el título")
    ti.set_defaults(func=ordre_titol)

    es = sub.add_parser("estil", help="El estilo de este vídeo (--tria un estilo de todo el vídeo, SECCIO.CLAU=VALOR, --a-tots, --treu)")
    es.add_argument("--projecte", required=True)
    es.add_argument("--tria", help="Uno de los estilos de todo el vídeo (net, revista, pop, suau, impacte, apilat)")
    es.add_argument("--a-tots", action="store_true", help="Pasa el estilo de este vídeo a su kit (para todos los vídeos)")
    es.add_argument("--treu", action="store_true", help="Quita los cambios de este vídeo: vuelve al estilo del kit")
    es.add_argument("valors", nargs="*", metavar="SECCIO.CLAU=VALOR", help="p. ej. subtitols.mida=0.09 titol.posicio_y=0.2 grafics=editorial")
    es.set_defaults(func=ordre_estil)
    ma = sub.add_parser("marca", help="La marca de un kit: colores, letras y cómo son tus vídeos (CLAU=VALOR la guarda)")
    on = ma.add_mutually_exclusive_group()
    on.add_argument("--projecte", help="El kit de este vídeo")
    on.add_argument("--kit", help="Un kit por su id (si no, el de por defecto)")
    ma.add_argument("valors", nargs="*", metavar="CLAU=VALOR",
                    help="p. ej. color_destacat=#FF7DB8 lletra_accent=Fraunces crida=\"comenta GUIA\"")
    ma.set_defaults(func=ordre_marca)

    gr = sub.add_parser("grafics", help="El plan de gráficos: frases, marca, gráficos y notas (proposa o canvia: lo guarda)")
    gr.add_argument("accio", nargs="?", choices=["proposa", "canvia", "fotogrames", "captura"],
                    help="proposa: un plan nuevo (sustituye los propuestos); canvia: solo los gráficos que hay en FITXER; "
                         "fotogrames: una imagen con el momento de cada gráfico, para ver dónde quedan; "
                         "captura: hace la captura de la web URL (para el gráfico «web»)")
    gr.add_argument("fitxer", nargs="?", help="El plan en JSON (una lista de gráficos), o «-» para leerlo de la entrada; "
                                              "con «captura», la dirección de la web")
    gr.add_argument("--grafic", help="Con «captura»: el gráfico web donde va la captura")
    gr.add_argument("--projecte", required=True)
    gr.add_argument("--de-nou", action="store_true", help="El plan nuevo sustituye todos los de antes (también los mantenidos)")
    gr.add_argument("--json", action="store_true", help="Lo muestra en JSON")
    gr.set_defaults(func=ordre_grafics)

    en = sub.add_parser("encaix", help="Cómo entra en vertical un vídeo horizontal: recortado o entero con el fondo difuminado")
    en.add_argument("encaix", nargs="?", choices=exporta.ENCAIXOS, help="retalla (el centro) o difumina (entero)")
    en.add_argument("--projecte", required=True)
    en.set_defaults(func=ordre_encaix)

    de = sub.add_parser("destaca", help="Las palabras destacadas de los subtítulos (más grandes y de otro color)")
    de.add_argument("--projecte", required=True)
    de.add_argument("--si", type=int, nargs="+", metavar="ID", help="Palabras que tienen que salir destacadas")
    de.add_argument("--no", type=int, nargs="+", metavar="ID", help="Palabras que no tienen que salir destacadas")
    de.add_argument("--automatic", action="store_true", help="Olvida las elegidas a mano: las elige todas editor-esp")
    de.set_defaults(func=ordre_destaca)

    no = sub.add_parser("notes", help="Las notas que la persona deja en la página para el asistente")
    no.add_argument("--projecte", required=True)
    no.add_argument("--espera", action="store_true", help="Espera las notas que envíe la persona (y las recoge)")
    no.add_argument("--minuts", type=float, default=9, help="Con --espera: como mucho cuánto tiempo (por defecto, 9)")
    no.add_argument("--respon", nargs=2, metavar=("NÚMERO", "TEXT"), help="Responde una nota (el número que dice --espera, p. ej. 3.1)")
    no.add_argument("--pregunta", action="store_true", help="Con --respon: es una pregunta, que la persona tiene que contestar")
    no.add_argument("--al-xat", action="store_true",
                    help="Con --respon: la pregunta (un permiso) se responde en el chat; la página se lo dice")
    no.set_defaults(func=ordre_notes)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
