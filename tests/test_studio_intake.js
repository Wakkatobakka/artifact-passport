#!/usr/bin/env node
/* Headless logic tests for Artifact Passport Studio v0.7. */
'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { webcrypto } = require('crypto');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'tools', 'passport-studio-v0.7.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'tools', 'Artifact-Passport-Studio-v0.7.html'), 'utf8');
assert(html.includes(source.trim()), 'The self-contained Studio must embed the tested JavaScript source');
for (const id of ['zipInput','zipIntakeBtn','exportHandoffBtn','exportBundleBtn','reviewStatus','currentStatus','currentKnownGood','currentObjective','nextMove','failedAttempts','mayLeaveDevice','approvedContexts','doNotBreak','decisionHistory','knownUncertainties','recentDeltaFrom','recentDelta']) {
  assert(html.includes(`id="${id}"`), `Studio interface is missing #${id}`);
}
const htmlIds=[...html.matchAll(/\sid="([^"]+)"/g)].map(match=>match[1]);
assert.equal(new Set(htmlIds).size,htmlIds.length,'Studio interface contains duplicate element IDs');

function fakeElement() { return { value:'', checked:false, textContent:'', innerHTML:'', style:{}, files:[], dataset:{}, classList:{add(){},remove(){},contains(){return false},toggle(){}}, addEventListener(){}, setAttribute(){}, appendChild(){}, append(){}, remove(){}, click(){}, showModal(){} }; }
const elements = new Map();
const document = { getElementById(id){if(!elements.has(id))elements.set(id,fakeElement());return elements.get(id)}, querySelectorAll(){return[]}, querySelector(){return null}, createElement(){return fakeElement()}, body:fakeElement(), title:'' };
const context = { document, console, confirm:()=>true, Blob, Response, TextEncoder, TextDecoder, DecompressionStream:globalThis.DecompressionStream, URL, setTimeout, clearTimeout, crypto:webcrypto };
context.globalThis=context;vm.createContext(context);vm.runInContext(source,context,{filename:'passport-studio-v0.7.js'});
const studio=context.ArtifactPassportStudio;assert(studio,'Studio functions were not exposed');

const existing=JSON.parse(fs.readFileSync(path.join(root,'examples','minimal','artifact-passport.json'),'utf8'));
const detected=studio.detectJson(existing,'artifact-passport.json',1200);assert.equal(detected.existing,true);assert.equal(detected.migrate,false);
const old=structuredClone(existing);old.spec_version='0.5';old.$schema='urn:artifact-passport:schema:0.5';delete old.review;
const migrated=studio.migratePassport(old,studio.detectJson(old,'old.passport.json',900));assert.equal(migrated.spec_version,'0.7');assert.equal(migrated.review.status,'ai-draft');assert.equal(migrated.intake.mode,'passport-migration');
const partial={$schema:'urn:artifact-passport:schema:0.5',spec_version:'0.5',passport_id:'demo.partial',artifact:{name:'Partial',version:'1'},intent:{purpose:'Test safe repair.'}};
const partialDetection=studio.detectJson(partial,'artifact-passport.json',300);assert(partialDetection.repair);const repaired=studio.repairPassport(partial,partialDetection);assert.equal(repaired.spec_version,'0.7');assert.equal(repaired.review.status,'ai-draft');assert(repaired.unresolved.some(x=>x.field==='operation'));
const packageLock=JSON.parse(fs.readFileSync(path.join(root,'examples','intake','package-lock.sample.json'),'utf8'));const manifest=studio.detectJson(packageLock,'package-lock.sample.json',640);assert.equal(manifest.type,'Node package lockfile');assert.equal(manifest.name,'county-reference-demo');assert(manifest.questions.some(x=>x.field==='authority'));
assert.equal(studio.passportFilename(existing),'example.minimal.note.passport.json');assert.equal(studio.handoffFilename(existing),'example.minimal.note.handoff.json');assert.equal(studio.safeFilePart('bad:/name*?'),'bad-name-');
const handoff=studio.defaultHandoff(existing,{context_snapshot:{do_not_break:['Keep it offline.'],decision_history:['Owner chose a single-file artifact.'],known_uncertainties:['Browser support needs field testing.'],recent_delta_from:'v0.6',recent_delta:['Added measurement.']}});assert.equal(handoff.passport_id,existing.passport_id);assert(handoff.context_routes.always_read.includes('artifact-passport.json'));assert(handoff.context_routes.always_read.includes('artifact-handoff.json'));assert.deepEqual(handoff.context_snapshot.do_not_break,['Keep it offline.']);assert.equal(handoff.context_snapshot.recent_delta_from,'v0.6');assert.equal(studio.validate(existing,handoff).structure,100);assert(studio.markdown(existing,handoff).includes('## Context snapshot'));
const blankContext=studio.defaultHandoff(existing);assert.deepEqual(blankContext.context_snapshot.do_not_break,[]);assert.equal(blankContext.context_snapshot.recent_delta_from,'');
const bundle=studio.createZipBytes({'project/artifact-passport.json':JSON.stringify(existing),'project/artifact-handoff.json':JSON.stringify(handoff),'project/src/main.js':'console.log("safe")','project/dist/app.js':'built output'});const zipFile={name:'project.zip',size:bundle.length,arrayBuffer:async()=>bundle.buffer};

(async()=>{
  assert.equal(studio.zipEntries(bundle.buffer).length,4);const zipDetection=await studio.detectZip(zipFile);assert.equal(zipDetection.mode,'zip');assert.equal(zipDetection.existing,true);assert.equal(zipDetection.handoffMeta.passport_id,existing.passport_id);assert.equal(zipDetection.fingerprint.algorithm,'sha256-inventory-v1');assert.equal(zipDetection.fingerprint.file_count,2);
  const unsafeBundle=studio.createZipBytes({'../escape.txt':'nope','safe/readme.md':'This is a sufficiently descriptive project readme for intake.'});const unsafe=await studio.detectZip({name:'unsafe.zip',size:unsafeBundle.length,arrayBuffer:async()=>unsafeBundle.buffer});assert(unsafe.archiveWarnings.some(x=>/unsafe path/.test(x)));assert(!unsafe.inventory.includes('../escape.txt'));
  const folder=await studio.detectFolder([{name:'README.md',webkitRelativePath:'digimon/README.md',size:100,text:async()=>'# Patch\n\nApplies quality-of-life fixes to a user-supplied game image.'},{name:'patch.ps1',webkitRelativePath:'digimon/patch.ps1',size:200,text:async()=>'Write-Host safe'}]);assert.equal(folder.mode,'folder');assert(folder.fileCandidates.some(x=>x.path==='patch.ps1'&&x.role==='editable-source'));assert.equal(folder.fingerprint.file_count,2);
  const routingPassport=structuredClone(existing);routingPassport.operation.entry_points=[{path:'run.cmd',role:'Launcher',open_with:'Command Prompt'}];routingPassport.structure.source_of_truth=[{path:'src/patch.ps1',role:'Patch logic'}];routingPassport.structure.generated_outputs=[{path:'out/patched.bin',role:'Output'}];const routes=studio.deriveContextRoutes(routingPassport);assert(routes.by_task.some(x=>x.task==='Modify the implementation'&&x.read.includes('src/patch.ps1')));assert(routes.avoid_by_default.includes('out/patched.bin'));
  for(const supplied of process.argv.slice(2)){
    const bytes=fs.readFileSync(path.resolve(supplied));const found=await studio.detectZip({name:path.basename(supplied),size:bytes.length,arrayBuffer:async()=>bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength)});
    console.log(`Supplied ZIP: ${path.basename(supplied)} — ${found.files.length} files, ${found.type}, ${found.archiveWarnings.length} warning(s)`);
  }
  console.log('Studio v0.7 intake, ZIP safety, repair, context snapshot, routing, and naming: PASS');
})().catch(error=>{console.error(error);process.exitCode=1});
