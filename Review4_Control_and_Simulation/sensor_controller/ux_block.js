/* ---------------- Judge-friendly layer: start page, one-click scenarios, live plain-language status, simple view ---------------- */
function uxSet(id, v) { const el = $(id); if (!el) return; el.value = v; el.dispatchEvent(new Event('input')); }
function uxFault(v) { const f = $('#sens-fault'); if (f) { f.value = v; f.dispatchEvent(new Event('change')); } }
function uxRain(on) { const U = window.SRMC_UI; if (U && !!U.st.rain !== on) $('#b-rain').click(); }
function uxGo(tab) { const b = document.querySelector('[data-t="' + tab + '"]'); if (b) b.click(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
const UX_SCEN = [
  { id: 'clear', icon: '☀', name: 'Clear noon', what: 'Strong sun, nothing wrong.', watch: 'The panels settle on the angle that gives the best mix of electricity and crop light. See the shadow stripes on the crop.', set: () => { uxSet('#t-day', 105); uxSet('#t-hour', 12); uxSet('#sens-cloud', 0); uxSet('#sens-wind', 3); } },
  { id: 'cloud', icon: '⛅', name: 'Passing clouds', what: 'Cloud cover 70 %.', watch: 'Sunlight drops, so the sensors tell the controller less shade is needed: the angle changes.', set: () => { uxSet('#t-day', 105); uxSet('#t-hour', 11); uxSet('#sens-cloud', 70); uxSet('#sens-wind', 3); } },
  { id: 'hot', icon: '🔥', name: 'Hot dry afternoon', what: '40 °C, 25 % humidity, dry soil.', watch: 'The crop is stressed, so the panels give it more shade. Compare the angle with the clear-noon case.', set: () => { uxSet('#t-day', 105); uxSet('#t-hour', 14); uxSet('#sens-cloud', 0); uxSet('#sens-temp', 40); uxSet('#sens-rh', 25); uxSet('#sens-soil', 12); uxSet('#sens-wind', 3); } },
  { id: 'rain', icon: '🌧', name: 'Rain', what: 'The rain sensor gets wet.', watch: 'Panels go flat (3°) and the roof drains into the gutter and tank. Watch the cistern level in the 3D view.', set: () => { uxSet('#t-day', 220); uxSet('#t-hour', 14); uxSet('#sens-cloud', 70); uxSet('#sens-wind', 5); uxRain(true); } },
  { id: 'storm', icon: '🌪', name: 'Storm wind', what: 'Wind 20 m/s (72 km/h).', watch: 'The wind sensor passes 15 m/s, so the panels turn edge-on (90°) and the wind passes through.', set: () => { uxSet('#t-day', 105); uxSet('#t-hour', 15); uxSet('#sens-cloud', 30); uxSet('#sens-wind', 20); } },
  { id: 'night', icon: '🌙', name: 'Night', what: 'No sunlight.', watch: 'The sunlight sensor reads nearly zero, so the panels park and nothing moves.', set: () => { uxSet('#t-day', 105); uxSet('#t-hour', 19); uxSet('#sens-wind', 2); } },
  { id: 'fault', icon: '⚠', name: 'Broken rain sensor', what: 'The rain sensor is stuck on "wet" in dry sun.', watch: 'The safety layer notices the rain reading makes no sense and ignores it, so the panels keep tracking the sun. Read the "Safety" line in the sensor panel.', set: () => { uxSet('#t-day', 105); uxSet('#t-hour', 11); uxSet('#sens-wind', 3); uxFault('rainWet'); } },
  { id: 'attack', icon: '🛡', name: 'Fake wind reading', what: 'A hacked wind sensor says 0 during a 22 m/s storm.', watch: 'A load cell on the drive wire feels the real wind, flags the wind sensor as faulty and stows the panels. Untick the monitor on the "ESP32 and attack" tab to see what happens without it.', set: () => { uxSet('#t-day', 105); uxSet('#t-hour', 15); uxSet('#sens-wind', 22); uxFault('windZero'); } }
];
const UX_MAP = [['twin', 'Live 3D demo', 'Move the sensors, watch the panels'], ['light', 'Sun and shade', 'How the sun and shadow move through the day'], ['gmap', 'Shade map', 'Red = heavy shade, green = well lit, on the whole field'], ['mech', 'How it tilts', 'Motor, drum, wire and lever arm explained'], ['tilt', 'Best angle', 'Why one angle cannot serve both electricity and crops'], ['water', 'Rain and water', 'Rain harvest, tank, irrigation by the soil sensor'], ['crops', 'Crops and soil', 'Which crop suits which soil and light'], ['eco', 'Money', 'Income for the farmer and the investor, with uncertainty'], ['acc', 'How accurate', 'Score against the best possible angle, 864 noisy cases'], ['struct', 'Strength', 'Wind load, stress in the lever arm, the 3-goal trade-off'], ['dex', 'Design explorer', 'Many designs compared by computer search'], ['edge', 'ESP32 and attack test', 'Small neural network for a cheap board, hacked wind sensor'], ['method', 'Limits', 'What is modelled and what is not']];
function uxScenario(id) {
  const sc = UX_SCEN.find(s => s.id === id); const U = window.SRMC_UI; if (!U) return;
  $('#sens-reset') && $('#sens-reset').click(); uxFault('none'); uxRain(false); uxSet('#sens-wind', 3); $('#sens-on').checked = true; $('#sens-on').dispatchEvent(new Event('change'));
  sc.set(); window.UXW = sc; const w = $('#ux-watch'); if (w) w.innerHTML = `<b>${sc.icon} ${sc.name}:</b> ${sc.what} <span>What to watch: ${sc.watch}</span>`; uxGo('twin'); setTimeout(uxLive, 400);
}
function uxLive() {
  const el = $('#ux-live'), el2 = $('#ux-strip'); const U = window.SRMC_UI; if (!U) return; const S0 = U.SENS, L = S0.last;
  const mode = L ? L.action.split(':')[0] : '', say = { OPTIMISE: 'Tracking the sun: picking the best mix of electricity and crop light', RAIN: 'Rain: panels flat, rainwater runs to the gutter and tank', STOW: 'Storm: panels edge-on so the wind passes through', NIGHT: 'Night: panels parked' }[mode] || (L ? mode : 'starting...');
  const col = { OPTIMISE: '#72B830', RAIN: '#4B9EE8', STOW: '#FF8080', NIGHT: '#9a9484' }[mode] || '#9a9484';
  const ang = L && L.angle != null && ['STOW', 'RAIN', 'NIGHT'].includes(L.mode) ? L.angle.toFixed(1) : (S0.cmd != null ? S0.cmd.toFixed(1) : '-'), pv = L && L.pvRel ? Math.round(100 * L.pvRel) + ' %' : '-', cr = L && L.cropRel > 0 ? Math.round(100 * L.cropRel) + ' %' : (L && L.pvRel ? 'no crop in season' : '-');
  const hh = U.st.hour, hm = Math.floor(hh) + ':' + String(Math.round((hh % 1) * 60)).padStart(2, '0');
  const rows = [['Sunlight (pyranometer)', L ? Math.round(L.ghi) + ' W/m²' : '-'], ['Light under the panels (PAR)', L ? Math.round(L.par) + ' µmol/m²/s' : '-'], ['Air (DHT11)', S0.temp + ' °C, ' + S0.rh + ' % humidity'], ['Soil moisture', S0.soil + ' % of plant-available water'], ['Rain sensor', U.st.rain ? 'WET' : 'dry'], ['Wind (anemometer)', S0.wind + ' m/s' + (S0.fault && S0.fault.startsWith('wind') ? ' (attacked)' : '')]];
  const html = `<div class="live"><div class="big" style="border-color:${col}"><span>Panel tilt</span><b>${ang}°</b></div><div class="big"><span>Electricity vs best</span><b>${pv}</b></div><div class="big"><span>Crop light vs best</span><b>${cr}</b></div>
    <div class="say" style="border-left-color:${col}"><b>${say}</b><br><span>Day ${U.st.day + 1}, ${hm} solar time${S0.fault && S0.fault !== 'none' ? ' · <b style="color:#FF8080">a sensor fault is injected</b>' : ''}</span></div></div>
    <table class="rd">${rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join('')}</table>`;
  if (el && el.offsetParent !== null) el.innerHTML = html;
  if (el2) el2.innerHTML = `<b style="color:${col}">${ang}°</b> <span>${say}</span> · electricity <b>${pv}</b> · crop light <b>${cr}</b>`;
}
function uxInit() {
  const sc = $('#ux-scen'); if (!sc) return; sc.innerHTML = UX_SCEN.map(s => `<button class="sc" data-s="${s.id}"><i>${s.icon}</i><b>${s.name}</b><span>${s.what}</span></button>`).join(''); $$('.sc').forEach(b => b.onclick = () => uxScenario(b.dataset.s));
  $('#ux-map').innerHTML = UX_MAP.map(m => `<button class="sc" data-g="${m[0]}"><b>${m[1]}</b><span>${m[2]}</span></button>`).join(''); $$('[data-g]').forEach(b => b.onclick = () => uxGo(b.dataset.g));
  setInterval(uxLive, 600); uxLive();
  const tg = $('#ux-toggle'); if (tg) tg.onclick = () => { document.body.classList.toggle('adv'); tg.textContent = document.body.classList.contains('adv') ? 'Hide design controls' : 'Show design controls'; setTimeout(() => { try { scene3d.resize(); } catch (e) { } }, 100); };
}
