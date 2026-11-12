#!/usr/bin/env node
/** Static HTML link checker. Run: node tools/check-links.mjs [site-root]. Set CHECK_EXTERNAL=1 for best-effort HEAD checks. */
import fs from 'node:fs';
import path from 'node:path';
const root = path.resolve(process.argv[2] || '.');
const files = []; const failures = []; const external = new Set();
function walk(dir) { for (const e of fs.readdirSync(dir,{withFileTypes:true})) { if (['.git','node_modules','_site'].includes(e.name)) continue; const p=path.join(dir,e.name); if(e.isDirectory()) walk(p); else if(e.isFile() && p.endsWith('.html')) files.push(p); } }
walk(root);
for (const file of files) { const html=fs.readFileSync(file,'utf8'); const refs=[...html.matchAll(/\\b(?:href|src|poster)=[\"']([^\"'\\s]+)[\"']/gi)].map(m=>m[1]); for(const raw of refs) { if(/^(https?:|mailto:|tel:|data:|javascript:|blob:)/i.test(raw) || raw.startsWith('#')) { if(/^https?:/i.test(raw)) external.add(raw.split('#')[0]); continue; } const clean=raw.split('#')[0].split('?')[0]; if(!clean) continue; let target; try { target=clean.startsWith('/')?path.join(root,clean.replace(/^\\/+/,'')):path.resolve(path.dirname(file),decodeURIComponent(clean)); } catch { failures.push([file,raw,'invalid URL']); continue; } if(!target.startsWith(root+path.sep) && target!==root) { failures.push([file,raw,'outside root']); continue; } const candidates=[target,path.join(target,'index.html'),path.join(target,'index.htm')]; if(!candidates.some(p=>fs.existsSync(p)&&fs.statSync(p).isFile())) failures.push([file,raw,'missing']); } }
console.log('Scanned '+files.length+' HTML files; '+external.size+' external URLs.');
if(process.env.CHECK_EXTERNAL==='1') for(const url of external) { try { const r=await fetch(url,{method:'HEAD',redirect:'follow',signal:AbortSignal.timeout(10000)}); if(!r.ok) console.error('EXTERNAL '+r.status+' '+url); } catch(e) { console.error('EXTERNAL ERROR '+url+' '+e.message); } }
else console.log('External checks skipped; set CHECK_EXTERNAL=1.');
for(const f of failures) console.error('BROKEN '+path.relative(root,f[0])+' -> '+f[1]+' ('+f[2]+')');
if(failures.length) process.exitCode=1; else console.log('No broken local HTML links found.');
