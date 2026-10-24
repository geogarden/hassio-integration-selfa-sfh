/* Selfa SFH: bundled local dashboard, no ESPHome or external JS dependencies. */
const SELFA_CARD_VERSION = "2.0.0";
const SELFA_LABELS = {
  pl: { title:"Selfa SFH", pv:"Panele PV", battery:"Bateria", inverter:"Falownik AC", grid:"Sieć · licznik", backup:"Backup / EPS",
    today:"Dzisiaj", production:"Produkcja PV", load:"Zużycie domu", imported:"Pobrano z sieci", exported:"Oddano do sieci",
    charged:"Ładowanie baterii", discharged:"Rozładowanie baterii", phase:"Faza", voltage:"Napięcie", current:"Prąd", power:"Moc licznika",
    controls:"Sterowanie", asymmetry:"Asymetria On-Grid", peak:"Peak Load Shifting", on:"Włączone", off:"Wyłączone",
    waiting_for_grid:"Oczekiwanie na sieć",self_test:"Autotest",on_grid:"Praca on-grid",fault:"Błąd",firmware_update:"Aktualizacja",off_grid:"Praca off-grid",
    charging:"Ładowanie",discharging:"Rozładowywanie",other:"Nieznany stan",missing:"Brak danych Selfa. Dodaj integrację lub wskaż device_id.",offline:"Brak połączenia",
    sign:"Moce sieci i baterii pokazano ze znakiem raportowanym przez falownik.",error:"Zmiana nie została potwierdzona: " },
  en: { title:"Selfa SFH",pv:"Solar PV",battery:"Battery",inverter:"Inverter AC",grid:"Grid · meter",backup:"Backup / EPS",
    today:"Today",production:"PV production",load:"Home consumption",imported:"Grid import",exported:"Grid export",charged:"Battery charge",discharged:"Battery discharge",
    phase:"Phase",voltage:"Voltage",current:"Current",power:"Meter power",controls:"Controls",asymmetry:"On-grid unbalanced output",peak:"Peak Load Shifting",on:"On",off:"Off",
    waiting_for_grid:"Waiting for grid",self_test:"Self-test",on_grid:"On-grid",fault:"Fault",firmware_update:"Firmware update",off_grid:"Off-grid",
    charging:"Charging",discharging:"Discharging",other:"Unknown state",missing:"No Selfa data. Add the integration or set device_id.",offline:"Disconnected",
    sign:"Grid and battery powers retain the sign reported by the inverter.",error:"Change was not confirmed: " },
};

class SelfaCard extends HTMLElement {
  static getStubConfig() { return {}; }
  setConfig(config) {
    this._config = config || {};
    this._built = false;
    if (this._hass) this.hass = this._hass;
  }
  getCardSize() { return 8; }
  getGridOptions() { return {columns:12,rows:"auto",min_columns:6}; }
  set hass(hass) {
    this._hass = hass;
    if (!this.shadowRoot) this.attachShadow({mode:"open"});
    const language = (hass.locale?.language || hass.language || "en").startsWith("pl") ? "pl" : "en";
    if (this._language !== language) { this._language = language; this._built = false; }
    this._t = SELFA_LABELS[language];
    this._findEntities();
    if (!this._built) this._build();
    this._update();
  }
  _findEntities() {
    const all = Object.values(this._hass.entities || {}).filter(e=>e.platform === "selfa_sfh");
    const device = this._config?.device_id || all.find(e=>e.device_id)?.device_id;
    this._map = {};
    for (const e of all) {
      if (e.device_id !== device) continue;
      const key = e.translation_key || this._hass.states[e.entity_id]?.attributes?.selfa_key;
      if (key) this._map[`${e.entity_id.split(".")[0]}:${key}`] = e.entity_id;
    }
  }
  _state(key, domain="sensor") { return this._hass.states[this._map[`${domain}:${key}`]]; }
  _value(key) {
    const state = this._state(key);
    if (!state || ["unknown","unavailable"].includes(state.state)) return null;
    const number = Number(state.state);
    return Number.isFinite(number) ? number : null;
  }
  _format(key, unit="", precision=2) {
    const number = this._value(key);
    if (number == null) return "—";
    return new Intl.NumberFormat(this._language,{maximumFractionDigits:precision}).format(number) + (unit ? " "+unit : "");
  }
  _build() {
    const t = this._t;
    this.shadowRoot.innerHTML = `<style>
      :host {display:block;font-family:Arial,Helvetica,sans-serif;color:var(--primary-text-color,#e8eff7);}
      ha-card {padding:18px;font-family:inherit;}
      .head {display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;}
      h2 {font-size:22px;margin:0;font-weight:600;}
      .status {font-size:14px;color:var(--secondary-text-color,#9aa);}
      svg {display:block;width:100%;height:auto;margin:12px 0;overflow:visible;}
      svg text {font-family:Arial,Helvetica,sans-serif;text-anchor:middle;fill:var(--primary-text-color,#e8eff7);font-variant-numeric:tabular-nums;}
      .box {fill:var(--secondary-background-color,#243548);stroke:var(--divider-color,#526478);stroke-width:1.2;}
      .pv {stroke:#e8bf60;} .bat {stroke:#68b8a5;} .ac {stroke:#6c9fda;}
      .wire {fill:none;stroke:var(--divider-color,#526478);stroke-width:3;}
      .name {font-size:19px;fill:var(--secondary-text-color,#aab);}
      .power {font-size:27px;font-weight:600;}
      .detail {font-size:16px;fill:var(--secondary-text-color,#aab);}
      .caption {margin:6px 0;color:var(--secondary-text-color,#9aa);font-size:12px;line-height:1.5;}
      h3 {font-size:16px;font-weight:600;margin:18px 0 10px;}
      .tiles {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;}
      .tile {background:var(--secondary-background-color,#243548);border-radius:12px;padding:12px;min-width:0;}
      .label {font-size:13px;line-height:1.4;color:var(--secondary-text-color,#9aa);}
      .number {display:block;font-size:20px;line-height:1.6;font-variant-numeric:tabular-nums;overflow-wrap:anywhere;}
      table {width:100%;border-collapse:collapse;font-size:14px;font-variant-numeric:tabular-nums;}
      th,td {padding:8px 4px;text-align:right;border-bottom:1px solid var(--divider-color,#526478);}
      th:first-child,td:first-child {text-align:left;} th {font-size:12px;color:var(--secondary-text-color,#9aa);font-weight:400;}
      .controls {display:flex;gap:8px;flex-wrap:wrap;}
      button {font:inherit;font-size:14px;padding:10px 14px;border:1px solid var(--divider-color,#526478);border-radius:12px;background:transparent;color:inherit;cursor:pointer;}
      button.on {border-color:var(--primary-color,#6c9fda);color:var(--primary-color,#6c9fda);}
      button:disabled {opacity:.5;cursor:default;} button:focus-visible {outline:2px solid var(--primary-color,#6c9fda);outline-offset:2px;}
      .error {color:var(--error-color,#eb8793);font-size:14px;margin-top:10px;}
      .empty {font-size:14px;padding:12px 0;color:var(--secondary-text-color,#9aa);}
      [hidden] {display:none!important;}
      @media(max-width:440px) {.tiles {grid-template-columns:repeat(2,minmax(0,1fr));}.number {font-size:18px;}ha-card{padding:12px;}}
    </style><ha-card>
      <div class="head"><h2 id="title"></h2><span class="status" id="status"></span></div>
      <div class="empty" id="empty" hidden></div>
      <div id="content">
      <svg viewBox="0 0 640 360" role="img" aria-label="${t.pv}, ${t.inverter}, ${t.grid}, ${t.battery}, ${t.backup}">
        <path class="wire" d="M320 98 V140 M184 193 H230 M410 193 H456 M320 244 V274"/>
        <rect class="box pv" x="213" y="4" width="214" height="94" rx="14"/>
        <text class="name" x="320" y="32">${t.pv}</text><text class="power" id="pv" x="320" y="67">—</text>
        <rect class="box" x="4" y="143" width="180" height="100" rx="14"/>
        <text class="name" x="94" y="175">${t.grid}</text><text class="power" id="grid" x="94" y="213">—</text>
        <rect class="box ac" x="230" y="140" width="180" height="104" rx="14"/>
        <text class="name" x="320" y="174">${t.inverter}</text><text class="power" id="ac" x="320" y="213">—</text>
        <rect class="box bat" x="456" y="126" width="180" height="134" rx="14"/>
        <text class="name" x="546" y="154">${t.battery}</text><text class="power" id="battery" x="546" y="187">—</text>
        <text class="detail" id="soc" x="546" y="217">—</text><text class="detail" id="batteryMode" x="546" y="242"></text>
        <rect class="box" x="213" y="274" width="214" height="80" rx="14"/>
        <text class="name" x="320" y="302">${t.backup}</text><text class="power" id="backup" x="320" y="337">—</text>
      </svg>
      <div class="caption">${t.sign}</div>
      <div class="tiles"><div class="tile"><span class="label">PV1</span><span class="number" id="pv1"></span><span class="label" id="pv1detail"></span></div>
        <div class="tile"><span class="label">PV2</span><span class="number" id="pv2"></span><span class="label" id="pv2detail"></span></div>
        <div class="tile"><span class="label">${t.battery}</span><span class="number" id="batteryV"></span><span class="label" id="batteryI"></span></div></div>
      <h3>${t.today}</h3><div class="tiles">
        ${[["daily_pv_gen",t.production],["daily_load",t.load],["daily_purch",t.imported],["daily_inj",t.exported],["daily_bat_chg",t.charged],["daily_bat_dchg",t.discharged]].map(([k,n])=>`<div class="tile"><span class="label">${n}</span><span class="number" data-energy="${k}"></span></div>`).join("")}
      </div>
      <h3>AC · ${t.voltage} / ${t.current}</h3><table><thead><tr><th>${t.phase}</th><th>V</th><th>A</th><th>${t.power}</th></tr></thead><tbody>
        ${["a","b","c"].map(k=>`<tr><td>${k.toUpperCase()}</td><td data-value="phase_${k}_v"></td><td data-value="phase_${k}_i"></td><td data-value="pmeter_${k}"></td></tr>`).join("")}
      </tbody></table><h3>${t.controls}</h3><div class="controls">
        <button data-switch="unbalanced_output">${t.asymmetry}</button><button data-switch="peak_load_shifting">${t.peak}</button>
      </div><div class="error" id="error" role="alert" hidden></div></div>
    </ha-card>`;
    for (const button of this.shadowRoot.querySelectorAll("button[data-switch]")) {
      button.onclick = async()=>{
        const key = button.dataset.switch, entity_id = this._map[`switch:${key}`];
        if (!entity_id) return;
        this._busy = this._busy || new Set();
        if (this._busy.has(key)) return;
        this._busy.add(key);
        const error = this.shadowRoot.getElementById("error");error.hidden=true;
        button.disabled=true;
        try {await this._hass.callService("switch",this._state(key,"switch")?.state === "on" ? "turn_off" : "turn_on",{entity_id});}
        catch (err) {error.textContent=t.error+(err?.message||String(err));error.hidden=false;}
        finally {this._busy.delete(key);this._update();}
      };
    }
    this._built = true;
  }
  _update() {
    const r = this.shadowRoot,t = this._t,$=id=>r.getElementById(id);
    $("title").textContent=this._config.title||t.title;
    const found = !!this._map["sensor:total_pv_input"];
    $("empty").hidden=found;$("empty").textContent=t.missing;$("content").hidden=!found;
    if (!found) return;
    const status=this._state("working_status")?.state;
    $("status").textContent=this._value("working_status_raw")==null?t.offline:(t[status]||t.other);
    for(const [id,key] of [["pv","total_pv_input"],["grid","pmeter_3ph"],["ac","p_ac"],["battery","battery_p"],["backup","backup_total_p"],["pv1","pv1_p"],["pv2","pv2_p"]]) $(id).textContent=this._format(key,"kW");
    $("soc").textContent="SOC "+this._format("soc","%",1);
    $("batteryMode").textContent=t[this._state("battery_mode")?.state]||"—";
    for(const k of ["pv1","pv2"]) $(k+"detail").textContent=this._format(k+"_v","V",1)+" · "+this._format(k+"_i","A",1);
    $("batteryV").textContent=this._format("battery_v","V",1);$("batteryI").textContent=this._format("battery_i","A",1);
    for(const el of r.querySelectorAll("[data-energy]")) el.textContent=this._format(el.dataset.energy,"kWh",1);
    for(const el of r.querySelectorAll("[data-value]")) el.textContent=this._format(el.dataset.value,el.dataset.value.startsWith("pmeter")?"kW":"",el.dataset.value.startsWith("pmeter")?3:1);
    for(const b of r.querySelectorAll("[data-switch]")) {
      const state=this._state(b.dataset.switch,"switch")?.state;
      b.disabled=this._busy?.has(b.dataset.switch)||!state||["unknown","unavailable"].includes(state);
      b.classList.toggle("on",state==="on");b.setAttribute("aria-pressed",String(state==="on"));
      b.title=state==="on"?t.on:state==="off"?t.off:t.offline;
    }
  }
}

function defineSelfaCard() {
  if (!window.customElements.get("selfa-card")) window.customElements.define("selfa-card",SelfaCard);
}
window.customElements.whenDefined("home-assistant").then(defineSelfaCard);
window.customCards=window.customCards||[];
if (!window.customCards.some(c=>c.type==="selfa-card")) window.customCards.push({type:"selfa-card",name:"Selfa SFH",description:"PV, battery, grid and backup · direct Modbus",preview:true});
console.info("SELFA-CARD",SELFA_CARD_VERSION);
