const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

async function fixture(config={}) {
  const dom = new JSDOM('<!doctype html><body></body>',{runScripts:'outside-only'});
  const w=dom.window;
  w.customElements.define('home-assistant',class extends w.HTMLElement{});
  w.eval(fs.readFileSync(path.join(__dirname,'../custom_components/selfa_sfh/www/selfa-card.js'),'utf8'));
  await w.customElements.whenDefined('selfa-card');
  const entities={},states={},calls=[];
  function set(key,value,domain='sensor',device='unit1') {
    const entity_id=domain+'.'+device+'_'+key;
    entities[entity_id]={entity_id,platform:'selfa_sfh',translation_key:key,device_id:device};
    states[entity_id]={state:String(value),attributes:{selfa_key:key}};
  }
  for(const [key,value] of Object.entries({total_pv_input:5.125,p_ac:4.5,battery_p:-1.2,soc:87.5,working_status:'on_grid',working_status_raw:2,battery_mode:'charging',daily_pv_gen:25.2})) set(key,value);
  set('unbalanced_output','off','switch');set('peak_load_shifting','on','switch');
  const hass={entities,states,locale:{language:'pl'},callService:async(...args)=>{calls.push(args)}};
  const card=w.document.createElement('selfa-card');card.setConfig(config);w.document.body.append(card);card.hass=hass;
  return {dom,card,hass,set,calls};
}

test('state changes update the card and missing values are not zero',async()=>{
  const {dom,card,hass,set}=await fixture();
  const r=card.shadowRoot;
  assert.match(r.getElementById('pv').textContent,/5,13 kW/);
  assert.equal(r.getElementById('grid').textContent,'—');
  assert.equal(r.getElementById('status').textContent,'Praca on-grid');
  set('total_pv_input','unavailable');set('working_status_raw','unavailable');card.hass=hass;
  assert.equal(r.getElementById('pv').textContent,'—');
  assert.equal(r.getElementById('status').textContent,'Brak połączenia');
  dom.window.close();
});

test('card uses the configured device even after entity IDs are renamed',async()=>{
  const {dom,card,hass,set}=await fixture();
  set('total_pv_input',8,'sensor','unit2');
  const entry=hass.entities['sensor.unit2_total_pv_input'];
  delete hass.entities['sensor.unit2_total_pv_input'];
  entry.entity_id='sensor.renamed_pv';hass.entities[entry.entity_id]=entry;
  hass.states[entry.entity_id]={state:'8',attributes:{selfa_key:'total_pv_input'}};
  card.setConfig({device_id:'unit2',title:'<b>Selfa</b>'});card.hass=hass;
  assert.equal(card.shadowRoot.getElementById('pv').textContent,'8 kW');
  assert.equal(card.shadowRoot.getElementById('title').textContent,'<b>Selfa</b>');
  assert.equal(card.shadowRoot.getElementById('title').children.length,0);
  dom.window.close();
});

test('a rejected switch change is shown as an error without optimistic state',async()=>{
  const {dom,card,hass}=await fixture();
  hass.callService=async()=>{throw Error('rejected')};
  await card.shadowRoot.querySelector('[data-switch="unbalanced_output"]').onclick();
  const button=card.shadowRoot.querySelector('[data-switch="unbalanced_output"]');
  assert.equal(button.classList.contains('on'),false);
  assert.equal(button.disabled,false);
  assert.match(card.shadowRoot.getElementById('error').textContent,/rejected/);
  dom.window.close();
});

test('switch service targets the resolved entity and controls stay disabled while pending',async()=>{
  const {dom,card,hass,calls}=await fixture();
  let release;
  hass.callService=(...args)=>{calls.push(args);return new Promise(r=>release=r)};
  const button=card.shadowRoot.querySelector('[data-switch="unbalanced_output"]');
  const pending=button.onclick();card.hass=hass;
  assert.equal(button.disabled,true);
  await button.onclick();
  assert.equal(calls.length,1);
  assert.deepEqual(calls[0].slice(0,2),['switch','turn_on']);
  assert.equal(calls[0][2].entity_id,'switch.unit1_unbalanced_output');
  release();await pending;
  dom.window.close();
});

test('language changes and all typography uses Arial without remote dependencies',async()=>{
  const {dom,card,hass}=await fixture();
  hass.locale.language='en';card.hass=hass;
  assert.equal(card.shadowRoot.getElementById('status').textContent,'On-grid');
  assert.match(card.shadowRoot.querySelector('style').textContent,/Arial,Helvetica,sans-serif/);
  assert.equal(card.shadowRoot.querySelectorAll('script,link').length,0);
  dom.window.close();
});
