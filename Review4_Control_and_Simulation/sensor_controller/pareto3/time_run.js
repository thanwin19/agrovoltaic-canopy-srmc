const fs=require('fs'),path=require('path');const ROOT=path.join(__dirname,'..','..','..');
const S=require(path.join(ROOT,'Review3_Digital_Twin','code_reference','srmc_engine.js'));const DD=path.join(ROOT,'Review1_Design_and_CAD','results','design'),L=f=>JSON.parse(fs.readFileSync(path.join(DD,f)));
const clim=L('climates.json')[0],soil=L('soils.json')[0],crops=L('crops.json'),D=L('design.json'),dp=D.presets[D.active],pw=+(dp.panelPitch-dp.panelGap).toFixed(4);
const params={bayLen:dp.bayLen,pitch:dp.panelPitch,panelW:pw,height:dp.clearanceLowestEdge+pw/2*Math.sin(dp.maxTiltDeg*Math.PI/180),tankM3:dp.cistern.m3,rainSlope:dp.rainSlopeDeg,stops:[15,20,25,30,35,40,45,50,55,60]};
let t=Date.now();const R=S.run({clim,soil,crops,params});console.log('smart run ms',Date.now()-t,Object.keys(R.P).join(','));
t=Date.now();const R2=S.run({clim,soil,crops,params:Object.assign({},params,{tiltMode:'fixed',tilt:30})});console.log('fixed run ms',Date.now()-t, R2.eco.solarRev, R2.eco.cropNet);
console.log(Object.keys(R.eco).join(','));console.log(Object.keys(R.wb).join(','));console.log(R.eco.solarRev,R.eco.om,R.eco.cropNet,R.wb.supplied,R.wb.demand,R.wb.harvested,R.annual.pvKWhPerM2,R.annual.meanLight);
