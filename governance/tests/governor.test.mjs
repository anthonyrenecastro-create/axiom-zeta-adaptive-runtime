import test from 'node:test';
import assert from 'node:assert/strict';
import {WorldGovernor} from '../governor.mjs';
import {freezeState,createInitialWorldState} from '../dist/core/state.js';
import {executeStateTransport} from '../dist/core/transport.js';
const domain=(id='compute',weights={energy:1,service:.1})=>({id,observations:{load:.4},bounds:{cpu:{min:.5,max:1}},objectives:weights,candidates:[{id:'eco',feasible:true,targets:{cpu:.7},metrics:{energy:1,service:.5},predicted_observations:{load:.4}},{id:'full',feasible:true,targets:{cpu:1},metrics:{energy:2,service:0},predicted_observations:{load:.8}}]});
const input=d=>({domains:[d]});

test('governs compute without a weather model or context',()=>{
 const g=new WorldGovernor();const r=g.plan(input(domain()));assert.equal(r.plans.compute.id,'eco');assert.equal(r.context.weather,undefined);assert.ok(r.ledger.accepted);assert.ok(r.retrieved_context);g.observe({observations:{'compute.load':.4},committed:true});
});
test('objective weights change actual selected action',()=>{
 const energy=new WorldGovernor().plan(input(domain('compute',{energy:1,service:.1})));
 const service=new WorldGovernor().plan(input(domain('compute',{energy:.1,service:10})));
 assert.equal(energy.plans.compute.id,'eco');assert.equal(service.plans.compute.id,'full');
});
test('shared substrate governs two independently modeled domains',()=>{
 const g=new WorldGovernor();const r=g.plan({domains:[domain('compute'),domain('water',{energy:.1,service:10})]});
 assert.equal(r.plans.compute.id,'eco');assert.equal(r.plans.water.id,'full');assert.equal(g.state.weatherTwin,undefined);
 const feedback=g.observe({observations:{'compute.load':.4,'water.load':.8},committed:true});assert.ok(feedback.consequence.creditAssignments.length>0);
});
test('core snapshots are recursively immutable',()=>{
 const s=freezeState(createInitialWorldState(42,2,false));assert.throws(()=>s.field.values.node_0=.9,TypeError);
});
test('zero compute budget cannot select an action',()=>{
 const r=new WorldGovernor().plan({...input(domain()),budget:0});assert.deepEqual(r.plans,{});assert.equal(r.used_budget,0);assert.ok(r.ledger.rejectedContributions.some(x=>x.reason.includes('budget')));
});
test('policy veto disables actions without disabling the substrate',()=>{
 const r=new WorldGovernor().plan({...input(domain()),allow_actions:false});assert.deepEqual(r.plans,{});assert.ok(r.ledger.acceptedContributions.length>0);
});
test('outcomes update reputation, memory and full state hash',()=>{
 const g=new WorldGovernor();const r=g.plan(input(domain()));const before=r.state_hash;
 const f=g.observe({observations:{'compute.load':.4},committed:true,progress:.3});assert.notEqual(f.state_hash,before);assert.ok(f.memory_layers.episodic>0);assert.ok(f.reputations.domain_compute_energy.totalContributions>0);
});
test('failed dispatch assigns blame to contributors',()=>{
 const g=new WorldGovernor();g.plan(input(domain()));const f=g.observe({observations:{'compute.load':.4},committed:false});assert.ok(f.consequence.creditAssignments.every(c=>c.blame===1&&c.reward===0));
});
test('invalid bounds, duplicate candidates and incomplete outcomes reject',()=>{
 const g=new WorldGovernor();const d=domain();d.candidates[0].targets.cpu=2;assert.throws(()=>g.plan(input(d)),/bounds/);
 const dup=domain();dup.candidates.push(dup.candidates[0]);assert.throws(()=>g.plan(input(dup)),/duplicate candidate/);
 g.plan(input(domain()));assert.throws(()=>g.observe({observations:{},committed:true}),/incomplete/);assert.throws(()=>g.plan(input(domain())),/previous/);
});
test('export/restore yields deterministic transitions',()=>{
 const a=new WorldGovernor();a.plan(input(domain()));a.observe({observations:{'compute.load':.4},committed:true});
 const b=new WorldGovernor(a.export());assert.deepEqual(a.plan(input(domain())),b.plan(input(domain())));
});
test('structural mass transport isolates intentional field updates',()=>{
 const previous=createInitialWorldState(42,2,false);const draft=structuredClone(previous);draft.field.values.node_0+=.1;
 const r=executeStateTransport(previous,draft,[]);assert.equal(r.conservationResidual,0);
});
