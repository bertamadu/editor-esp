"""Comprova que l'ordinador té tot el que necessita tallat (`tallat.py comprova`).

Cada comprovació diu «ok», «avís» (funcionarà, però hi ha alguna cosa a saber) o «error» (cal
arreglar-ho), amb una explicació curta i què fer. Gairebé sempre, el que cal fer és tornar a
executar ./prepara.sh.
"""
from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from motor import entorn

ARREGLA = ("ejecuta prepara.ps1 (desde la carpeta de tallat-es)" if entorn.WINDOWS
           else "ejecuta ./prepara.sh (desde la carpeta de tallat-es)")
MARQUES = {"ok": "✓", "avis": "!", "error": "✗"}


def _versio(paquet: str) -> str | None:
    try:
        return importlib.metadata.version(paquet)
    except importlib.metadata.PackageNotFoundError:
        return None


def _executa(ordre: list[str], temps: int = 60) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(ordre, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=temps)
    except (OSError, subprocess.TimeoutExpired):
        return None


def _python() -> list[tuple]:
    v = sys.version_info
    estat = "ok" if v[:2] == (3, 11) else "avis"
    detall = f"{platform.python_version()}" + ("" if estat == "ok" else " · tallat-es está probado con la 3.11")
    resultat = [(estat, "Python", detall)]
    falten = [p for p in ("whisperx", "torch", "torchaudio", "transformers", "numpy") if not _versio(p)]
    if falten:
        return resultat + [("error", "WhisperX", f"faltan paquetes ({', '.join(falten)}) → {ARREGLA}")]
    if int(_versio("numpy").split(".")[0]) >= 2:
        resultat.append(("error", "numpy", f"hace falta la versión 1 (hay la {_versio('numpy')}) → {ARREGLA}"))
    # S'importa a part: a Mac Intel, si dues còpies d'OpenMP xoquen, el programa peta.
    arrel = str(Path(__file__).resolve().parent.parent)
    prova = _executa([sys.executable, "-c", f"import sys; sys.path.insert(0, {arrel!r}); from motor import entorn; "
                      "entorn.llista_de_lletres(); import ctranslate2, torch, whisperx"], temps=300)
    if prova is None or prova.returncode != 0:
        omp = prova is not None and (prova.returncode < 0 or "OMP" in prova.stderr)
        motiu = "dos copias de OpenMP chocan (Mac Intel)" if omp else "no arranca"
        return resultat + [("error", "WhisperX", f"{motiu} → {ARREGLA}")]
    return resultat + [("ok", "WhisperX", f"{_versio('whisperx')} · torch {_versio('torch')}")]


def _ffmpeg() -> list[tuple]:
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        falta = " i ".join(n for n, p in (("ffmpeg", ffmpeg), ("ffprobe", ffprobe)) if not p)
        return [("error", "ffmpeg", f"no encuentro {falta} → {ARREGLA}")]
    versio = (_executa([ffmpeg, "-hide_banner", "-version"]) or subprocess.CompletedProcess([], 1, "", "")).stdout
    versio = (versio.splitlines() or ["?"])[0].replace("ffmpeg version ", "")
    codificadors = (_executa([ffmpeg, "-hide_banner", "-encoders"]) or subprocess.CompletedProcess([], 1, "", "")).stdout
    filtres = (_executa([ffmpeg, "-hide_banner", "-filters"]) or subprocess.CompletedProcess([], 1, "", "")).stdout
    necessaris = ("h264_videotoolbox", "libx264", "aac") if entorn.MAC else ("libx264", "aac")  # vegeu exporta.codec_video
    falten = [c for c in necessaris if not re.search(rf"\s{c}\s", codificadors)]
    falten += [f for f in ("lut3d", "zoompan", "overlay", "concat") if not re.search(rf"\s{f}\s", filtres)]
    if falten:
        return [("error", "ffmpeg", f"{versio} no lleva {', '.join(falten)} → {ARREGLA}")]
    propi = Path(ffmpeg).parent in entorn.carpetes_eines()
    return [("ok", "ffmpeg", f"{versio.split(' ')[0]}" + (" (de tallat-es)" if propi else f" ({ffmpeg})"))]


def _carpetes_npx() -> list[Path]:
    """On guarda npx els paquets que baixa: ~/.npm/_npx al Mac, %LOCALAPPDATA%\\npm-cache\\_npx a Windows
    (o on digui la configuració de npm)."""
    carpetes = [Path.home() / ".npm" / "_npx"]
    if os.environ.get("LOCALAPPDATA"):
        carpetes.append(Path(os.environ["LOCALAPPDATA"]) / "npm-cache" / "_npx")
    if os.environ.get("npm_config_cache"):
        carpetes.append(Path(os.environ["npm_config_cache"]) / "_npx")
    return carpetes


def _node() -> list[tuple]:
    node, npx = shutil.which("node"), shutil.which("npx")
    if not node or not npx:
        return [("error", "Node.js", f"no lo encuentro (hace falta para HyperFrames) → {ARREGLA}")]
    versio = ((_executa([node, "--version"]) or subprocess.CompletedProcess([], 1, "", "")).stdout or "").strip()
    major = int(re.sub(r"\D", "", versio.split(".")[0]) or 0)
    if major < 18:
        return [("error", "Node.js", f"{versio} es demasiado antiguo (hace falta el 18 o más nuevo) → {ARREGLA}")]
    resultat = [("ok", "Node.js", versio)]
    paquets = [p for carpeta in _carpetes_npx() for p in carpeta.glob("*/node_modules/hyperframes/package.json")]
    versions = set()
    for p in paquets:
        try:
            versions.add(json.loads(p.read_text(encoding="utf-8")).get("version"))
        except (OSError, json.JSONDecodeError):
            continue
    if entorn.VERSIO_HYPERFRAMES not in versions:
        return resultat + [("avis", "HyperFrames", "se descargará la primera vez que hagas un borrador (unos segundos)")]
    cami = _executa([npx, "--yes", f"hyperframes@{entorn.VERSIO_HYPERFRAMES}", "browser", "path"], temps=90)
    navegador = cami.stdout.strip().splitlines()[-1] if cami and cami.returncode == 0 and cami.stdout.strip() else ""
    if not navegador or not Path(navegador).exists():
        return resultat + [("avis", "HyperFrames", f"{entorn.VERSIO_HYPERFRAMES}; el navegador se descargará la primera vez (unos 100 MB)")]
    return resultat + [("ok", "HyperFrames", f"{entorn.VERSIO_HYPERFRAMES} con su navegador")]


def _models() -> list[tuple]:
    hub = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
    tenim = lambda nom: any((hub / f"models--{nom}" / "snapshots").glob("*/*"))  # noqa: E731
    resultat = []
    if tenim("jonatasgrosman--wav2vec2-large-xlsr-53-spanish"):
        resultat.append(("ok", "Modelo de voz en castellano", "wav2vec2 xlsr-53 spanish"))
    else:
        resultat.append(("avis", "Modelo de voz en castellano", f"se descargará la primera vez que transcribas (1,2 GB); o {ARREGLA}"))
    if tenim("Systran--faster-whisper-large-v3"):
        resultat.append(("ok", "Modelo de transcripción", "large-v3"))
    else:
        resultat.append(("avis", "Modelo de transcripción", "solo hace falta si no usas Descript; se descargará la primera vez (3 GB)"))
    return resultat


def _disc_i_carpeta() -> list[tuple]:
    resultat = []
    lliure = shutil.disk_usage(Path.home()).free / 1e9
    estat = "error" if lliure < 5 else ("avis" if lliure < 15 else "ok")
    resultat.append((estat, "Espacio en el disco", f"{lliure:.0f} GB libres" + ("" if estat == "ok" else " · los vídeos en 4K ocupan mucho")))
    try:
        entorn.TALLAT.mkdir(parents=True, exist_ok=True)
        prova = entorn.TALLAT / ".prova-escriptura"
        prova.write_text("ok", encoding="utf-8")
        prova.unlink()
        resultat.append(("ok", "Carpeta ~/.tallat-es", "se puede escribir"))
    except OSError as e:
        resultat.append(("error", "Carpeta ~/.tallat-es", f"no se puede escribir ({e.strerror})"))
    return resultat


def comprovacions() -> list[tuple[str, str, str]]:
    """[(estat, nom, detall)] amb estat «ok», «avis» o «error»."""
    entorn.prepara()
    return _python() + _ffmpeg() + _node() + _models() + _disc_i_carpeta()


def informe(resultats: list[tuple[str, str, str]]) -> str:
    amplada = max(len(nom) for _, nom, _ in resultats)
    linies = [f"  {MARQUES[estat]} {nom.ljust(amplada)}  {detall}" for estat, nom, detall in resultats]
    errors = sum(1 for estat, _, _ in resultats if estat == "error")
    if errors:
        linies.append(f"\nHay {errors} {'cosa' if errors == 1 else 'cosas'} por arreglar. {ARREGLA[0].upper() + ARREGLA[1:]}.")
    else:
        linies.append("\nTodo listo para usar tallat-es.")
    return "\n".join(linies)
