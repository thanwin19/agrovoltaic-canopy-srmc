// Loads the engine, data and controller script blocks out of the twin HTML into Node (same code the browser runs).
const fs = require('fs'), vm = require('vm'), path = require('path');
module.exports = function load(htmlPath, extra) {
  const t = fs.readFileSync(htmlPath, 'utf8'), blocks = [...t.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  const ctx = { console, Math, JSON, Object, Array, Number, String, Date, Set, Map, isFinite, isNaN, Infinity, NaN };
  ctx.window = ctx; ctx.globalThis = ctx; vm.createContext(ctx);
  for (const b of blocks) if (/SRMC_DATA=|SRMC simulation engine|SRMC-SC:|SRMC_VP|SRMC_IRRSTUDY=|SRMC_ACC=/.test(b.slice(0, 400)) && !/UI layer/.test(b.slice(0, 200))) vm.runInContext(b, ctx);
  for (const f of extra || []) vm.runInContext(fs.readFileSync(f, 'utf8'), ctx);
  return ctx;
};
