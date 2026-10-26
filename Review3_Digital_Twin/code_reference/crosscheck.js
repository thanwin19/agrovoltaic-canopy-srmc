// Compares the MATLAB results (out/matlab_results.json) with the JS engine used by the digital twin
const S=require('../engine/srmc_engine.js'),fs=require('fs');
const L=f=>JSON.parse(fs.readFileSync('data/'+f));
const clim=L('climates.json')[0],soil=L('soils.json')[0],crops=L('crops.json');
const D=JSON.parse(fs.readFileSync('design/design.json')),dp=D.presets[D.active],pw=+(dp.panelPitch-dp.panelGap).toFixed(4);
const params={bayLen:dp.bayLen,pitch:dp.panelPitch,panelW:pw,height:dp.clearanceLowestEdge+pw/2*Math.sin(dp.maxTiltDeg*Math.PI/180),tankM3:dp.cistern.m3,rainSlope:dp.rainSlopeDeg,stops:Array.from({length:Math.round((dp.stopsDeg[1]-dp.stopsDeg[0])/5)+1},(_,i)=>dp.stopsDeg[0]+5*i)};
const r=S.run({clim,soil,crops,params}), m=JSON.parse(fs.readFileSync('out/matlab_results.json'));
const rows=[['pv kWh/m2/yr',r.annual.pvKWhPerM2,m.pvKWhPerM2],['annual GHI',r.annual.ghi,m.ghi],
 ['harvested m3',r.wb.harvested,m.harvested],['demand m3',r.wb.demand,m.demand],['unmet m3',r.wb.unmet,m.unmet],
 ['capex',r.eco.capex,m.capex],['solar revenue',r.eco.solarRev,m.solarRev],['crop net',r.eco.cropNet,m.cropNet],['payback yr',r.eco.payback,m.payback],['farmer income/yr',r.eco.farmerAnnual,m.farmerAnnual],['industry net/yr',r.eco.industryNet,m.industryNet]];
r.annual.meanStrip.forEach((v,i)=>rows.push(['zone '+(i+1)+' light',v,m.meanStrip[i]]));
r.wb.zones.forEach((z,i)=>{rows.push(['zone '+(i+1)+' yield '+z.crop,z.yield,m.yield[i]]);});
let worst=0;
console.log('quantity'.padEnd(26),'JS twin'.padStart(14),'MATLAB'.padStart(14),'diff %');
for(const [n,a,b] of rows){const d=Math.abs(a-b)/Math.max(Math.abs(a),1e-9)*100;worst=Math.max(worst,d);console.log(n.padEnd(26),a.toFixed(3).padStart(14),Number(b).toFixed(3).padStart(14),d.toFixed(4));}
console.log('crops JS',r.zones.map(z=>z.crop.id).join(','),'| MATLAB',m.zoneCrops.join(','));
console.log('WORST DIFF %',worst.toFixed(4));
