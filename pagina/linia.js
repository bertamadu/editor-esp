// editor-esp · la línia de temps de la pàgina de revisió (com la d'un editor de vídeo: CapCut, Premiere).
//
// Els trossos del muntatge en una pista, amb els fotogrames i la forma d'ona, i a sobre les pistes dels gràfics,
// el b-roll i els stickers. Es poden allargar i escurçar els trossos (amb precisió de fotograma), partir-los,
// treure'n un, treure un silenci o un bocí marcat, i canviar-ne el volum.
//
// Tot el que es toca aquí es desa a l'estat del vídeo (edicio.json) en segons de la gravació, no del muntatge:
// talls_manuals, afegits_manuals, partits, volums i volum_veu (motor/edicio.py, ajusta_a_ma). Així el servidor
// en fa els trossos i la vista prèvia, l'esborrany i el vídeo final surten igual. Es desfà amb ⌘Z, com la resta
// (canvia). Fa servir el que hi ha a app.js: trams, acum, duradaFinal, estat, P, canvia, vesA…

const L = {
  obert: false, zoom: 0, pxs: 1,   // píxels per segon del muntatge
  ona: null, veu: null, pas: 0.01, // la forma d'ona i el mapa de veu (un valor cada `pas` segons de la gravació)
  mini: null, imatge: null,         // la tira de miniatures
  carregant: false,
  sel: null,                        // el que hi ha triat: {tipus: "tros" | "silenci" | "rang", k, a, b} (a, b: de la gravació)
  provisional: null,                // els trossos mentre s'arrossega una vora (encara no desats)
  arrossega: null,
};
const L_PAD = 14;                   // marge a cada costat de la pista
const L_REGLE = 18;                 // l'alçada del regle dels segons
const L_PISTA = 18;
const L_PISTES = [["grafic", "Gráficos"], ["broll", "B-roll"], ["sticker", "Stickers"]];
const L_VIDEO = 64;                 // l'alçada de la pista del vídeo (fotogrames a dalt, forma d'ona a baix)
const L_ONA = 24;
const L_MAX_PXS = 480;              // amb el zoom al màxim: uns 8 píxels per fotograma a 60 fps
const L_SILENCI_MINIM = 0.15;       // segons: els silencis més curts no es ratllen
const L_SOROLL = 0.1;               // dins d'un silenci, un so més curt (un clic) no compta (com motor/veu.py)

const fpsL = () => P?.fps || 30;
const aFotograma = (t) => Math.round(t * fpsL()) / fpsL();
const yVideo = () => L_REGLE + L_PISTES.length * L_PISTA + 6;
const alcadaLinia = () => yVideo() + L_VIDEO + 4;
const fmtDb = (db) => (db > 0 ? "+" : db < 0 ? "−" : "") + Math.abs(db) + " dB";

// --- Intervals (en segons de la gravació) ----------------------------------------------------

function ajuntaInterval(llista, a, b) {
  const tots = [...(llista || []).map((x) => [x[0], x[1]]), [a, b]].sort((x, y) => x[0] - y[0]);
  const sortida = [];
  for (const [x, y] of tots) {
    if (sortida.length && x <= sortida.at(-1)[1] + 1e-6) sortida.at(-1)[1] = Math.max(sortida.at(-1)[1], y);
    else sortida.push([x, y]);
  }
  return sortida;
}

function treuInterval(llista, a, b) {
  return (llista || []).flatMap(([x, y]) => (y <= a || x >= b ? [[x, y]]
    : [...(x < a ? [[x, a]] : []), ...(y > b ? [[b, y]] : [])]));
}

const teRetocs = () => !!(estat?.talls_manuals?.length || estat?.afegits_manuals?.length || estat?.partits?.length
  || estat?.volums?.length || estat?.volum_veu);

// --- Dades -----------------------------------------------------------------------------------

function base64ABytes(text) {
  const brut = atob(text || "");
  const bytes = new Uint8Array(brut.length);
  for (let i = 0; i < brut.length; i++) bytes[i] = brut.charCodeAt(i);
  return bytes;
}

async function carregaLinia() {
  if (L.ona || L.carregant) return;
  L.carregant = true;
  try {
    const r = await (await fetch("/api/linia")).json();
    if (r.error) throw new Error(r.error);
    L.pas = r.pas;
    L.ona = base64ABytes(r.ona);
    L.veu = base64ABytes(r.veu);
    if (r.miniatures) {
      L.mini = r.miniatures;
      const img = new Image();
      img.onload = () => { L.imatge = img; dibuixaLinia(); };
      img.src = r.miniatures.url;
    }
  } catch (e) {
    avis("No he podido dibujar el sonido en la línea de tiempo: " + e.message, 6000);
    L.ona = new Uint8Array(0);
    L.veu = new Uint8Array(0);
  } finally {
    L.carregant = false;
  }
  pintaLinia();
}

// Els silencis de debò (segons el mapa de veu) entre a i b de la gravació: [[inici, final]].
function silencisEntre(a, b) {
  if (!L.veu?.length) return [];
  const i0 = Math.max(0, Math.ceil(a / L.pas)), i1 = Math.min(L.veu.length, Math.floor(b / L.pas));
  const curt = Math.round(L_SOROLL / L.pas), minim = Math.round(L_SILENCI_MINIM / L.pas);
  const silenci = [];
  for (let i = i0; i < i1; i++) silenci.push(!L.veu[i]);
  // Un so molt curt enmig d'un silenci (un clic, una tecla) també és silenci.
  for (let i = 0; i < silenci.length;) {
    if (silenci[i]) { i++; continue; }
    let j = i;
    while (j < silenci.length && !silenci[j]) j++;
    if (i > 0 && j < silenci.length && j - i < curt) for (let x = i; x < j; x++) silenci[x] = true;
    i = j;
  }
  const sortida = [];
  for (let i = 0; i < silenci.length;) {
    if (!silenci[i]) { i++; continue; }
    let j = i;
    while (j < silenci.length && silenci[j]) j++;
    if (j - i >= minim) sortida.push([(i0 + i) * L.pas, (i0 + j) * L.pas]);
    i = j;
  }
  return sortida;
}

// --- Mides -----------------------------------------------------------------------------------

const llistaLinia = () => L.provisional || trams;
function inicisDe(llista) {
  const inicis = [];
  let t = 0;
  for (const [a, b] of llista) { inicis.push(t); t += b - a; }
  return { inicis, total: t };
}

function calculaPxs() {
  const amplada = Math.max(200, $("#l-scroll").clientWidth - 2 * L_PAD);
  const minim = amplada / Math.max(1, duradaFinal);
  L.pxs = minim >= L_MAX_PXS ? minim : minim * Math.pow(L_MAX_PXS / minim, L.zoom);
}

const xDe = (m) => L_PAD + m * L.pxs;
const mDe = (x) => (x - L_PAD) / L.pxs;

// El punt x de la pista (dins del contingut) en temps de la gravació, dins del tros k.
function originalDeX(x, k, llista = llistaLinia()) {
  const { inicis } = inicisDe(llista);
  const [a, b] = llista[k];
  return limita(a + (x - xDe(inicis[k])) / L.pxs, a, b);
}

// --- Pintar ----------------------------------------------------------------------------------

function pintaLinia() {
  const panell = $("#linia");
  if (!panell || !L.obert || !P) return;
  panell.classList.toggle("apagada", vista !== "directe");
  $("#l-esborrany").hidden = vista === "directe";
  if (!L.ona) { carregaLinia(); }
  calculaPxs();
  const llista = llistaLinia();
  const { inicis, total } = inicisDe(llista);
  const cont = $("#l-contingut");
  cont.style.width = `${Math.ceil(total * L.pxs + 2 * L_PAD)}px`;
  cont.style.height = `${alcadaLinia()}px`;

  // Les pistes de sobre: gràfics (i el títol), b-roll i stickers.
  const pistes = $("#l-pistes");
  pistes.textContent = "";
  pistes.style.top = `${L_REGLE}px`;
  L_PISTES.forEach(([tipus, nom], i) => {
    const pista = document.createElement("div");
    pista.className = "l-pista";
    pista.style.top = `${i * L_PISTA}px`;
    pista.dataset.tipus = tipus;
    const etiqueta = document.createElement("span");
    etiqueta.className = "l-nom-pista";
    etiqueta.textContent = nom;
    pista.append(etiqueta);
    for (const p of pecesDeLaPista(tipus)) {
      const el = document.createElement("button");
      el.className = `l-peca ${p.classe}`;
      el.style.left = `${xDe(p.inici)}px`;
      el.style.width = `${Math.max(4, (p.final - p.inici) * L.pxs)}px`;
      el.textContent = p.nom;
      el.title = p.titol;
      el.dataset.id = p.id;
      el.dataset.tipus = p.classe;
      pista.append(el);
    }
    pistes.append(pista);
  });

  // La pista del vídeo: un element per tros (les vores, els silencis i el que hi ha triat). Els fotogrames i la
  // forma d'ona es dibuixen al canvas (només la part que es veu).
  const video = $("#l-video");
  video.textContent = "";
  video.style.top = `${yVideo()}px`;
  video.style.height = `${L_VIDEO}px`;
  const general = estat.volum_veu || 0;
  llista.forEach((tram, k) => {
    const [a, b] = tram;
    const el = document.createElement("div");
    el.className = "l-tros";
    if (L.sel?.tipus === "tros" && L.sel.k === k) el.classList.add("triat");
    el.style.left = `${xDe(inicis[k])}px`;
    el.style.width = `${(b - a) * L.pxs}px`;
    el.style.height = `${L_VIDEO}px`;
    el.dataset.k = k;
    for (const [s0, s1] of silencisEntre(a, b)) {
      const s = document.createElement("div");
      s.className = "l-silenci";
      s.style.left = `${(s0 - a) * L.pxs}px`;
      s.style.width = `${(s1 - s0) * L.pxs}px`;
      s.dataset.a = s0;
      s.dataset.b = s1;
      s.title = `Silencio de ${fmtSegons(s1 - s0)}: tócalo para marcarlo`;
      el.append(s);
    }
    const propi = Math.round(((tram[4] || 0) - general) * 10) / 10;
    if (propi) {
      const v = document.createElement("span");
      v.className = "l-volum-tros";
      v.textContent = fmtDb(propi);
      el.append(v);
    }
    for (const costat of ["esq", "dre"]) {
      const vora = document.createElement("div");
      vora.className = `l-vora ${costat}`;
      vora.dataset.costat = costat;
      vora.title = costat === "esq" ? "Arrastra para cambiar dónde empieza" : "Arrastra para cambiar dónde acaba";
      el.append(vora);
    }
    video.append(el);
  });
  // El bocí marcat (un silenci o un tros arrossegant dins d'un tros).
  if (L.sel && L.sel.tipus !== "tros" && llista[L.sel.k]) {
    const m = document.createElement("div");
    m.className = "l-marca";
    m.style.left = `${xDe(inicis[L.sel.k] + L.sel.a - llista[L.sel.k][0])}px`;
    m.style.width = `${Math.max(2, (L.sel.b - L.sel.a) * L.pxs)}px`;
    m.style.height = `${L_VIDEO}px`;
    video.append(m);
  }
  pintaEinesLinia();
  dibuixaLinia();
  mouCapcalLinia();
}

function pecesDeLaPista(tipus) {
  if (tipus === "grafic") {
    const peces = graficsVisibles().map((g) => ({
      id: g.id, classe: "grafic", inici: g.inici, final: g.final, nom: NOMS_GRAFIC[g.tipus] || "Gráfico",
      titol: `${NOMS_GRAFIC[g.tipus] || "Gráfico"}: arrástralo para moverlo` }));
    if (titolMuntatge) {
      peces.push({ id: "titol", classe: "titol", inici: titolMuntatge.inici, final: titolMuntatge.final,
        nom: "Título", titol: "El título gancho" });
    }
    return peces;
  }
  const llista = tipus === "broll" ? brollsMuntatge : stickersMuntatge;
  return llista.map((x) => ({ id: x.id, classe: tipus, inici: x.inici, final: x.inici + x.durada,
    nom: tipus === "broll" ? "B-roll" : "Sticker", titol: tipus === "broll" ? "B-roll" : "Sticker" }));
}

function pintaEinesLinia() {
  const sel = L.sel;
  const treu = $("#l-treu");
  treu.disabled = !sel;
  treu.textContent = !sel ? "Quita" : sel.tipus === "tros" ? "Quita el trozo" : sel.tipus === "silenci" ? "Quita el silencio"
    : "Quita lo marcado";
  const tros = sel?.tipus === "tros" && trams[sel.k];
  $("#l-control-tros").hidden = !tros;
  if (tros) {
    const db = volumPropi(trams[sel.k]);
    $("#l-volum-tros").value = db;
    $("#l-volum-tros-text").textContent = fmtDb(db);
  }
  $("#l-volum-veu").value = estat.volum_veu || 0;
  $("#l-volum-veu-text").textContent = fmtDb(estat.volum_veu || 0);
  $("#l-oblida").hidden = !teRetocs();
}

function volumPropi(tram) {
  let millor = 0, solapa = 0;
  for (const [x, y, db] of estat.volums || []) {
    const s = Math.min(tram[1], y) - Math.max(tram[0], x);
    if (s > solapa) { millor = db; solapa = s; }
  }
  return millor;
}

// Els fotogrames, la forma d'ona i el regle, només de la part que es veu de la pista.
function dibuixaLinia() {
  if (!L.obert || !P) return;
  const scroll = $("#l-scroll"), canvas = $("#l-canvas");
  const w = scroll.clientWidth, h = alcadaLinia(), dpr = window.devicePixelRatio || 1;
  if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  const esq = scroll.scrollLeft, dre = esq + w;
  const estil = getComputedStyle(document.body);
  const colorText = estil.getPropertyValue("--text-3").trim() || "#888";
  const colorAccent = estil.getPropertyValue("--accent").trim() || "#0071e3";
  const llista = llistaLinia();
  const { inicis, total } = inicisDe(llista);

  // El regle: una marca cada tants segons com càpiguen.
  const passos = [1 / fpsL(), 0.1, 0.2, 0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300];
  const pas = passos.find((p) => p * L.pxs >= 70) || 600;
  ctx.fillStyle = colorText;
  ctx.strokeStyle = colorText;
  ctx.font = "10px system-ui, sans-serif";
  ctx.lineWidth = 1;
  for (let m = Math.max(0, Math.floor(mDe(esq) / pas) * pas); m <= Math.min(total, mDe(dre)) + pas; m += pas) {
    const x = xDe(m) - esq;
    ctx.beginPath();
    ctx.moveTo(Math.round(x) + 0.5, L_REGLE - 6);
    ctx.lineTo(Math.round(x) + 0.5, L_REGLE);
    ctx.stroke();
    const decimals = pas < 1 ? (pas < 0.1 ? 2 : 1) : 0;
    const mm = Math.floor(m / 60), ss = (m - mm * 60).toFixed(decimals).replace(".", ",");
    ctx.fillText(`${mm}:${(m - mm * 60) < 10 ? "0" : ""}${ss}`, x + 3, 10);
  }

  // Cada tros: fotogrames a dalt i la forma d'ona a baix.
  const y0 = yVideo(), altFoto = L_VIDEO - L_ONA, yOna = y0 + altFoto;
  llista.forEach(([a, b], k) => {
    const x0 = xDe(inicis[k]), x1 = x0 + (b - a) * L.pxs;
    if (x1 < esq || x0 > dre) return;
    ctx.save();
    ctx.beginPath();
    ctx.roundRect(x0 - esq + 1, y0, Math.max(1, x1 - x0 - 2), L_VIDEO, 6);
    ctx.clip();
    ctx.fillStyle = "rgba(120, 120, 128, 0.28)";
    ctx.fillRect(x0 - esq, y0, x1 - x0, L_VIDEO);
    if (L.imatge && L.mini) {
      const amp = altFoto * L.mini.amplada / L.mini.alcada;
      const n = Math.floor(L.imatge.naturalWidth / L.mini.amplada) * Math.floor(L.imatge.naturalHeight / L.mini.alcada);
      for (let i = Math.max(0, Math.floor((esq - x0) / amp)); x0 + i * amp < Math.min(x1, dre); i++) {
        const t = a + (i * amp) / L.pxs;
        const idx = Math.min(n - 1, Math.max(0, Math.floor(t / L.mini.pas)));
        const sx = (idx % L.mini.columnes) * L.mini.amplada, sy = Math.floor(idx / L.mini.columnes) * L.mini.alcada;
        ctx.drawImage(L.imatge, sx, sy, L.mini.amplada, L.mini.alcada, x0 + i * amp - esq, y0, amp, altFoto);
      }
    }
    ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
    ctx.fillRect(x0 - esq, yOna, x1 - x0, L_ONA);
    if (L.ona?.length) {
      const gris = "rgba(255, 255, 255, 0.45)";
      for (let x = Math.max(x0, esq); x < Math.min(x1, dre); x++) {
        const t0 = a + (x - x0) / L.pxs, t1 = t0 + 1 / L.pxs;
        const i0 = Math.floor(t0 / L.pas), i1 = Math.max(i0 + 1, Math.ceil(t1 / L.pas));
        let pic = 0, veu = false;
        for (let i = i0; i < i1 && i < L.ona.length; i++) { pic = Math.max(pic, L.ona[i]); veu ||= !!L.veu[i]; }
        const alt = Math.max(1, (pic / 255) * (L_ONA - 4));
        ctx.fillStyle = veu ? colorAccent : gris;
        ctx.fillRect(x - esq, yOna + (L_ONA - alt) / 2, 1, alt);
      }
    }
    ctx.restore();
  });
}

function mouCapcalLinia() {
  if (!L.obert || !trams.length) return;
  const m = L.arrossega?.tipus === "capcal" ? L.arrossega.m : tempsMuntatge();
  const x = xDe(Math.min(m, duradaFinal));
  const capcal = $("#l-capcal");
  capcal.style.transform = `translateX(${x}px)`;
  // Mentre sona, la pista segueix el cursor.
  const scroll = $("#l-scroll");
  if (sona() && !L.arrossega && (x < scroll.scrollLeft + 20 || x > scroll.scrollLeft + scroll.clientWidth - 40)) {
    scroll.scrollLeft = x - scroll.clientWidth * 0.25;
  }
}

// --- Retocs -----------------------------------------------------------------------------------

function retocaVora(k, costat, nou) {
  const [a, b] = trams[k];
  nou = aFotograma(nou);
  if (Math.abs(nou - (costat === "esq" ? a : b)) < 1e-4) return;
  canvia((e) => {
    if (costat === "dre" ? nou < b : nou > a) {   // escurçar: es treu (i el que s'hi havia afegit, també)
      const [x, y] = costat === "dre" ? [nou, b] : [a, nou];
      e.talls_manuals = ajuntaInterval(e.talls_manuals, x, y);
      e.afegits_manuals = treuInterval(e.afegits_manuals, x, y);
    } else {                                      // allargar: s'hi afegeix (i ja no es treu)
      const [x, y] = costat === "dre" ? [b, nou] : [nou, a];
      e.afegits_manuals = ajuntaInterval(e.afegits_manuals, x, y);
      e.talls_manuals = treuInterval(e.talls_manuals, x, y);
    }
  });
  L.sel = { tipus: "tros", k, a: costat === "esq" ? nou : a, b: costat === "dre" ? nou : b };
}

// Fins on es pot portar una vora: com a molt fins a un altre tros de la gravació (no se sentiria dos cops), i
// sempre ha de quedar com a mínim un fotograma.
function limitsVora(k, costat) {
  const [a, b] = trams[k];
  const altres = trams.filter((_, j) => j !== k);
  if (costat === "dre") {
    const seguent = Math.min(P.durada, ...altres.map(([x]) => x).filter((x) => x >= b - 1e-4));
    return [a + 1 / fpsL(), seguent];
  }
  const anterior = Math.max(0, ...altres.map(([, y]) => y).filter((y) => y <= a + 1e-4));
  return [anterior, b - 1 / fpsL()];
}

function treuSeleccioLinia() {
  const sel = L.sel;
  if (!sel || !trams[sel.k]) return;
  let [x, y] = [sel.a, sel.b];
  if (sel.tipus === "silenci") {  // es deixa una mica d'aire a cada costat, com quan s'escurcen els silencis
    const aire = Math.min(0.05, (y - x) / 4);
    [x, y] = [x + aire, y - aire];
  }
  x = aFotograma(x);
  y = aFotograma(y);
  if (y - x < 1 / fpsL() - 1e-6) { avis("Es demasiado corto: marca al menos un fotograma."); return; }
  // Un tros sencer: se'n treuen les paraules, com si es tragués al text (i el text diu el mateix que el vídeo).
  const paraules = sel.tipus !== "tros" ? [] : P.paraules.filter((p) => !esFora(p.id)
    && (p.inici + p.final) / 2 >= sel.a && (p.inici + p.final) / 2 <= sel.b).map((p) => p.id);
  if (paraules.length) {
    canvia((e) => {
      for (const id of paraules) {
        delete e.propostes[String(id)];
        e.esborrades[String(id)] = "usuari";
        e.mantingudes = e.mantingudes.filter((q) => q !== id);
      }
      e.afegits_manuals = treuInterval(e.afegits_manuals, x, y);
    });
    avis("Trozo quitado (sus palabras también salen quitadas en el texto)", 3000);
    L.sel = null;
    return;
  }
  canvia((e) => {
    e.talls_manuals = ajuntaInterval(e.talls_manuals, x, y);
    e.afegits_manuals = treuInterval(e.afegits_manuals, x, y);
  });
  avis(sel.tipus === "tros" ? "Trozo quitado" : sel.tipus === "silenci" ? "Silencio quitado" : "Quitado", 2000);
  L.sel = null;
}

function parteixAlCursor() {
  if (vista !== "directe" || !trams.length) return;
  const m = tempsMuntatge();
  const k = trosDe(m);
  const [a, b] = trams[k];
  const t = aFotograma(a + (m - acum[k]));
  if (t - a < 1 / fpsL() - 1e-6 || b - t < 1 / fpsL() - 1e-6) { avis("Pon el cursor dentro de un trozo para partirlo."); return; }
  canvia((e) => { e.partits = [...new Set([...(e.partits || []), t])].sort((p, q) => p - q); });
  L.sel = null;
  avis("Trozo partido", 2000);
}

function canviaVolumTros(k, db) {
  const [a, b] = trams[k];
  canvia((e) => {
    const altres = (e.volums || []).filter(([x, y]) => Math.min(b, y) - Math.max(a, x) <= 0);
    e.volums = db ? [...altres, [a, b, db]] : altres;
  });
}

// Mou un gràfic fins a la paraula que sona més a prop del moment m del muntatge.
function mouGrafic(id, m) {
  const g = graficDe(id);
  if (!g) return;
  let millor = null, dist = Infinity;
  for (const p of P.paraules) {
    if (esFora(p.id)) continue;
    const k = indexTram(p.inici);
    if (k >= trams.length || p.inici < trams[k][0] - 0.05) continue;
    const mp = acum[k] + Math.max(0, p.inici - trams[k][0]);
    if (Math.abs(mp - m) < dist) { dist = Math.abs(mp - m); millor = p.id; }
  }
  if (millor == null || millor === g.paraula) return;
  canvia((e) => {
    const x = e.grafics.find((q) => q.id === id);
    if (!x) return;
    if (x.fins != null) x.fins += millor - x.paraula;
    x.paraula = millor;
  });
}

// --- Ratolí i teclat ---------------------------------------------------------------------------

function xDelPunter(e) {
  const scroll = $("#l-scroll");
  return e.clientX - scroll.getBoundingClientRect().left + scroll.scrollLeft;
}

function trosDeX(x) {
  const { inicis } = inicisDe(trams);
  for (let k = 0; k < trams.length; k++) {
    if (x >= xDe(inicis[k]) && x < xDe(inicis[k] + trams[k][1] - trams[k][0])) return k;
  }
  return -1;
}

function etiquetaLinia(x, text) {
  let el = $("#l-contingut .l-etiqueta");
  if (!el) { el = document.createElement("div"); el.className = "l-etiqueta"; $("#l-contingut").append(el); }
  el.style.left = `${x}px`;
  el.style.top = `${yVideo() - 2}px`;
  el.textContent = text;
}

function instalaLinia() {
  const scroll = $("#l-scroll");
  const obre = (obert) => {
    L.obert = obert;
    $("#linia").hidden = !obert;
    $("#commuta-linia").setAttribute("aria-pressed", String(obert));
    desa("tallat.linia", obert);
    if (obert) requestAnimationFrame(() => { pintaLinia(); scroll.focus({ preventScroll: true }); });
  };
  $("#commuta-linia").addEventListener("click", () => obre(!L.obert));
  $("#l-tanca").addEventListener("click", () => obre(false));
  $("#l-parteix").addEventListener("click", parteixAlCursor);
  $("#l-treu").addEventListener("click", treuSeleccioLinia);
  $("#l-oblida").addEventListener("click", () => {
    canvia((e) => { e.talls_manuals = []; e.afegits_manuals = []; e.partits = []; e.volums = []; e.volum_veu = 0; });
    L.sel = null;
    avis("Retoques quitados (⌘Z para recuperarlos)", 3000);
  });
  $("#l-zoom").addEventListener("input", (e) => {
    const centre = mDe(scroll.scrollLeft + scroll.clientWidth / 2);
    L.zoom = Number(e.target.value);
    pintaLinia();
    scroll.scrollLeft = xDe(centre) - scroll.clientWidth / 2;
    dibuixaLinia();
  });
  const volumTros = $("#l-volum-tros");
  volumTros.addEventListener("input", () => { $("#l-volum-tros-text").textContent = fmtDb(Number(volumTros.value)); });
  volumTros.addEventListener("change", () => { if (L.sel?.tipus === "tros") canviaVolumTros(L.sel.k, Number(volumTros.value)); });
  const volumVeu = $("#l-volum-veu");
  volumVeu.addEventListener("input", () => { $("#l-volum-veu-text").textContent = fmtDb(Number(volumVeu.value)); });
  volumVeu.addEventListener("change", () => canvia((e) => { e.volum_veu = Number(volumVeu.value); }));
  scroll.addEventListener("scroll", dibuixaLinia, { passive: true });
  new ResizeObserver(() => { if (L.obert) pintaLinia(); }).observe(scroll);

  // ⌘ (o Ctrl) i la rodeta: zoom al voltant del ratolí. La rodeta sola, endavant i endarrere.
  scroll.addEventListener("wheel", (e) => {
    if (e.metaKey || e.ctrlKey) {
      e.preventDefault();
      const x = xDelPunter(e), m = mDe(x), dins = x - scroll.scrollLeft;
      L.zoom = limita(L.zoom - e.deltaY * 0.002, 0, 1);
      $("#l-zoom").value = L.zoom;
      pintaLinia();
      scroll.scrollLeft = xDe(m) - dins;
      dibuixaLinia();
    } else if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      e.preventDefault();
      scroll.scrollLeft += e.deltaY;
    }
  }, { passive: false });

  scroll.addEventListener("pointerdown", (e) => {
    if (e.button !== 0 || vista !== "directe" || !trams.length) return;
    scroll.focus({ preventScroll: true });
    const x = xDelPunter(e);
    const vora = e.target.closest(".l-vora");
    const peca = e.target.closest(".l-peca");
    const tros = e.target.closest(".l-tros");
    const sonava = sona();
    if (vora) {
      const k = Number(vora.parentElement.dataset.k);
      if (sonava) atura();
      L.arrossega = { tipus: "vora", k, costat: vora.dataset.costat, x0: x, limits: limitsVora(k, vora.dataset.costat),
        orig: vora.dataset.costat === "esq" ? trams[k][0] : trams[k][1] };
    } else if (peca) {
      const p = pecesDeLaPista(peca.dataset.tipus === "grafic" || peca.dataset.tipus === "titol" ? "grafic" : peca.dataset.tipus)
        .find((q) => String(q.id) === peca.dataset.id);
      L.arrossega = { tipus: "peca", el: peca, x0: x, p, mogut: false };
    } else if (tros) {
      L.arrossega = { tipus: "tros", k: Number(tros.dataset.k), x0: x, mogut: false, silenci: e.target.closest(".l-silenci") };
    } else {
      if (sonava) atura();
      L.arrossega = { tipus: "capcal", m: limita(mDe(x), 0, duradaFinal), sonava };
      vesA(L.arrossega.m);
    }
    scroll.setPointerCapture(e.pointerId);
    e.preventDefault();
  });

  scroll.addEventListener("pointermove", (e) => {
    const ar = L.arrossega;
    if (!ar) return;
    const x = xDelPunter(e);
    if (ar.tipus === "capcal") {
      ar.m = limita(mDe(x), 0, duradaFinal);
      vesA(ar.m);
      mouCapcalLinia();
    } else if (ar.tipus === "vora") {
      const nou = aFotograma(limita(ar.orig + (x - ar.x0) / L.pxs, ...ar.limits));
      ar.nou = nou;
      L.provisional = trams.map((t, j) => (j !== ar.k ? t : ar.costat === "esq" ? [nou, t[1]] : [t[0], nou]));
      pintaLinia();
      const d = nou - ar.orig, canvi = ar.costat === "dre" ? d : -d;
      const { inicis } = inicisDe(L.provisional);
      const xVora = xDe(inicis[ar.k] + (ar.costat === "dre" ? nou - L.provisional[ar.k][0] : 0));
      etiquetaLinia(xVora, `${canvi >= 0 ? "+" : "−"}${fmtSegons(Math.abs(canvi)).replace(" s", "")} s · ${Math.round(Math.abs(canvi) * fpsL())} fot.`);
    } else if (ar.tipus === "peca") {
      if (Math.abs(x - ar.x0) > 3) ar.mogut = true;
      if (ar.mogut && ar.p?.classe === "grafic") {
        ar.el.classList.add("arrossegant");
        ar.el.style.left = `${xDe(ar.p.inici) + (x - ar.x0)}px`;
      }
    } else if (ar.tipus === "tros") {
      if (Math.abs(x - ar.x0) > 4) ar.mogut = true;
      if (ar.mogut) {
        const t0 = originalDeX(ar.x0, ar.k, trams), t1 = originalDeX(x, ar.k, trams);
        L.sel = { tipus: "rang", k: ar.k, a: Math.min(t0, t1), b: Math.max(t0, t1) };
        pintaLinia();
      }
    }
  });

  const acaba = (e) => {
    const ar = L.arrossega;
    if (!ar) return;
    L.arrossega = null;
    $("#l-contingut .l-etiqueta")?.remove();
    const x = xDelPunter(e);
    if (ar.tipus === "capcal") {
      if (ar.sonava) reprodueix();
    } else if (ar.tipus === "vora") {
      L.provisional = null;
      if (ar.nou != null) retocaVora(ar.k, ar.costat, ar.nou);
      pintaLinia();
    } else if (ar.tipus === "peca") {
      if (ar.mogut && ar.p?.classe === "grafic") mouGrafic(ar.p.id, ar.p.inici + (x - ar.x0) / L.pxs);
      else if (ar.p) vesA(ar.p.inici);
      pintaLinia();
    } else if (ar.tipus === "tros") {
      if (!ar.mogut) {
        const s = ar.silenci;
        L.sel = s ? { tipus: "silenci", k: ar.k, a: Number(s.dataset.a), b: Number(s.dataset.b) }
          : { tipus: "tros", k: ar.k, a: trams[ar.k][0], b: trams[ar.k][1] };
        const { inicis } = inicisDe(trams);
        vesA(inicis[ar.k] + originalDeX(x, ar.k, trams) - trams[ar.k][0]);
      } else if (L.sel && L.sel.b - L.sel.a < 1 / fpsL()) L.sel = null;
      pintaLinia();
    }
  };
  scroll.addEventListener("pointerup", acaba);
  scroll.addEventListener("pointercancel", acaba);

  // Amb la pista enfocada: ⌫ treu el que hi ha triat, S parteix al cursor i Esc deixa la selecció.
  scroll.addEventListener("keydown", (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if ((e.key === "Backspace" || e.key === "Delete") && L.sel) { e.preventDefault(); e.stopPropagation(); treuSeleccioLinia(); }
    else if (e.code === "KeyS") { e.preventDefault(); e.stopPropagation(); parteixAlCursor(); }
    else if (e.key === "Escape" && L.sel) { e.stopPropagation(); L.sel = null; pintaLinia(); }
  });

  if (llegeix("tallat.linia", false)) obre(true);
}

// Quan canvien els trossos (cada desament torna els del servidor), el que hi havia triat es busca als nous.
function trossosNousLinia() {
  if (L.sel) {
    const { a, b } = L.sel;
    const k = trams.findIndex(([x, y]) => Math.min(b, y) - Math.max(a, x) > 1e-4);
    if (k < 0) L.sel = null;
    else {
      L.sel.k = k;
      if (L.sel.tipus === "tros") { L.sel.a = trams[k][0]; L.sel.b = trams[k][1]; }
    }
  }
  pintaLinia();
}

instalaLinia();
