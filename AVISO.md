# Aviso: versión modificada

**editor-esp** es una versión modificada de [tallat](https://github.com/ivetanoro/tallat) 0.9.0, de **Ivet Anoro**, publicado con la licencia **GNU AGPL v3 o posterior** (ver `LICENSE`). Esta copia sigue la misma licencia.

Cambios respecto al original (noviembre de 2026):
- Transcripción y alineación de palabras en castellano (`es`): WhisperX en castellano y, para el tiempo de cada palabra, el modelo `jonatasgrosman/wav2vec2-large-xlsr-53-spanish` (Apache 2.0) en lugar del modelo catalán de Softcatalà.
- Interfaz de la página de revisión, mensajes, ayuda, configuración e instrucciones para Claude (`skills/editor-esp/SKILL.md`) traducidos al castellano.
- Listas de muletillas, palabras puente, emojis e instrucciones de voz («Claude, vuelvo a empezar»…) adaptadas al castellano.
- **Línea de tiempo** en la página de revisión (en Edita), como la de CapCut: alargar o acortar trozos por fotogramas, partir (S), quitar trozos, silencios o pedazos (⌫), volumen por trozo y de toda la voz, y mover los gráficos en el tiempo.
- Carpeta propia (`~/.tallat-es`) y puerto propio (8766), para que pueda convivir con tallat en catalán.
- Nombre propio (`editor-esp`).
