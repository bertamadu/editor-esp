# tallat-es

Editor de reels **en castellano** que funciona dentro de Claude Code: transcribe el vídeo, quita las muletillas, propone reels, pone subtítulos, b-roll y stickers, y exporta en vertical (9:16). Todo en tu ordenador.

Es una **versión modificada** de [tallat](https://github.com/ivetanoro/tallat), de Ivet Anoro (licencia AGPL v3 o posterior). Qué ha cambiado: ver [AVISO.md](AVISO.md).

## Instalar (como conector local de Claude Code)

En la pestaña **Code** de la app de Claude, escribe:

```
/plugin marketplace add ~/code/tallat-es
/plugin install tallat-es@tallat-es
```

Después abre una sesión nueva y escribe **«instala tallat-es»**: Claude descarga lo que hace falta (unos 2-3 GB, 10-20 minutos, todo en `~/.tallat-es`).

## Usar

Escribe, por ejemplo: **«Edita este vídeo con tallat-es: ~/Downloads/mi-video.mov»**. Claude transcribe, te abre la página de revisión (Edita · Viste · Revisa) y te guía paso a paso.

## Dónde está cada cosa

- `~/.tallat-es/`: tus estilos (`kits/`), tus reglas (`gust.json`), tu lista de muletillas (`farciment.txt`), tus sonidos y las herramientas instaladas.
- La carpeta de cada proyecto: el vídeo, la transcripción, la edición y los exports. Siempre fuera de esta carpeta.

## Licencia

GNU AGPL v3 o posterior (archivo `LICENSE`). Original: © Ivet Anoro. Modificaciones de esta copia: ver `AVISO.md`.
