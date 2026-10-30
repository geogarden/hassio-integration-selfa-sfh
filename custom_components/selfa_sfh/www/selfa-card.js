/* Selfa SFH: bundled local dashboard, no ESPHome or external JS dependencies. */
const SELFA_CARD_VERSION = "2.2.1";
const SELFA_LABELS = {
  pl: { home:"Dom", estimated:"Bilans AC · moc szacowana", live:"Panele i bateria · odczyty bieżące", flow:"Przepływ energii", importing:"Pobieranie z sieci", exporting:"Oddawanie do sieci", standby:"Oczekiwanie", title:"Selfa SFH", pv:"Panele PV", string:"String", total:"PV razem", readonly:"Tylko odczyt", battery:"Bateria", inverter:"Falownik AC", grid:"Sieć · licznik", backup:"Backup / EPS",
    today:"Dzisiaj", production:"Produkcja PV", load:"Zużycie domu", imported:"Pobrano z sieci", exported:"Oddano do sieci",
    charged:"Ładowanie baterii", discharged:"Rozładowanie baterii", phase:"Faza", voltage:"Napięcie", current:"Prąd", power:"Moc licznika",
    controls:"Sterowanie", asymmetry:"Asymetria On-Grid", peak:"Peak Load Shifting", on:"Włączone", off:"Wyłączone",
    waiting_for_grid:"Oczekiwanie na sieć",self_test:"Autotest",on_grid:"Praca on-grid",fault:"Błąd",firmware_update:"Aktualizacja",off_grid:"Praca off-grid",
    charging:"Ładowanie",discharging:"Rozładowywanie",other:"Nieznany stan",missing:"Brak danych Selfa. Dodaj integrację lub wskaż device_id.",offline:"Brak połączenia",
    sign:"Moce sieci i baterii pokazano ze znakiem raportowanym przez falownik.",error:"Zmiana nie została potwierdzona: " },
  en: { home:"Home", estimated:"AC balance · estimated power", live:"Panels and battery · live readings", flow:"Energy flow", importing:"Importing from grid", exporting:"Exporting to grid", standby:"Standby", title:"Selfa SFH",pv:"Solar PV",string:"String",total:"PV total",readonly:"Read only",battery:"Battery",inverter:"Inverter AC",grid:"Grid · meter",backup:"Backup / EPS",
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
  getCardSize() { return 15; }
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
    return this._formatNumber(number,unit,precision);
  }
  _formatNumber(number,unit="",precision=2) {
    if (number == null) return "—";
    return new Intl.NumberFormat(this._language,{maximumFractionDigits:precision}).format(number) + (unit ? " "+unit : "");
  }
  _build() {
    const t = this._t;
    const node = (cls,icon,label,body)=>`<div class="node ${cls}"><ha-icon icon="mdi:${icon}" aria-hidden="true"></ha-icon><div class="node-label">${label}</div>${body}</div>`;
    this.shadowRoot.innerHTML = `<style>
      /* Inherited HA variables update immediately, including themes applied to one card.
         Keep selfa-card-background as an optional explicit user override. */
      :host {display:block;font-family:Arial,Helvetica,sans-serif;color:var(--primary-text-color,CanvasText);
        --_selfa-text:var(--primary-text-color,CanvasText);
        --_selfa-muted:var(--secondary-text-color,GrayText);
        --_selfa-surface:var(--ha-card-background,var(--card-background-color,Canvas));
        --_selfa-line:var(--ha-card-border-color,var(--divider-color,color-mix(in srgb,var(--_selfa-text) 18%,transparent)));
        --_selfa-node:var(--selfa-node-background,color-mix(in srgb,var(--_selfa-text) 5%,var(--_selfa-surface)));
        --_selfa-inverter:color-mix(in srgb,var(--primary-color,#03a9f4) 10%,var(--_selfa-surface));
        --_selfa-solar:var(--energy-solar-color,var(--warning-color,#b87800));
        --_selfa-grid:var(--energy-grid-consumption-color,var(--success-color,#2e7d32));
        --_selfa-battery:var(--energy-battery-out-color,#9360c5);
        --_selfa-home:var(--primary-color,#0288d1);
      }
      * {box-sizing:border-box;}
      ha-card {padding:22px;background:var(--selfa-card-background,color-mix(in srgb,var(--_selfa-surface) 82%,transparent));color:var(--_selfa-text);border:1px solid var(--_selfa-line);border-radius:22px;font-family:inherit;container-type:inline-size;backdrop-filter:blur(10px);}
      .head {display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;}
      h2 {font-size:24px;margin:0;font-weight:600;letter-spacing:1px;}
      .status {font-size:13px;color:var(--_selfa-muted);}.status.online {color:var(--success-color,#2e7d32);}
      .flow {position:relative;display:grid;grid-template-columns:minmax(0,1fr) 38px minmax(0,1.15fr) 38px minmax(0,1fr);grid-template-rows:180px 34px 176px 34px 142px;margin:22px auto;max-width:850px;}
      .pv-group {grid-area:1/1/2/6;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px 14px;width:76%;justify-self:center;min-width:0;}
      .pv-total {grid-column:1/-1;text-align:center;font-size:12px;color:var(--_selfa-muted);}
      .pv-total strong {font-weight:500;}
      .pv-link {grid-area:2/1/3/6;width:76%;justify-self:center;--flow-color:var(--_selfa-solar);}
      .grid-link {grid-area:3/2;--flow-color:var(--_selfa-grid);}
      .battery-link {grid-area:3/4;--flow-color:var(--_selfa-battery);}
      .home-link {grid-area:4/3;--flow-color:var(--_selfa-home);}
      .link {position:relative;min-width:0;}
      .wires {position:absolute;width:100%;height:100%;inset:0;pointer-events:none;overflow:visible;}
      .wire {fill:none;stroke-width:2;stroke:var(--flow-color);opacity:.25;}
      .stream {fill:none;stroke:var(--flow-color);stroke-width:3;stroke-dasharray:1 17;stroke-linecap:round;opacity:0;}
      .stream.active {opacity:1;animation:flow 2s linear infinite;}.stream.reverse {animation-direction:reverse;}
      @keyframes flow {to {stroke-dashoffset:-36;}}
      .node {position:relative;z-index:1;display:flex;flex-direction:column;justify-content:center;align-items:center;min-width:0;padding:12px;text-align:center;border:1px solid var(--_selfa-line);border-radius:17px;background:var(--_selfa-node);}
      .node ha-icon {display:flex;align-items:center;justify-content:center;width:32px;height:32px;flex:0 0 32px;--mdc-icon-size:26px;color:var(--node-color);margin:0 0 6px;}
      .node-label {font-size:13px;color:var(--_selfa-muted);margin-bottom:8px;overflow-wrap:anywhere;}
      .power {font-size:28px;font-weight:600;font-variant-numeric:tabular-nums;overflow-wrap:anywhere;}
      .detail {font-size:12px;line-height:1.5;color:var(--_selfa-muted);margin-top:6px;overflow-wrap:anywhere;}
      .pv {--node-color:var(--_selfa-solar);}.grid {grid-area:3/1;--node-color:var(--_selfa-grid);}
      .inverter {grid-area:3/3;--node-color:var(--_selfa-home);background:var(--_selfa-inverter);}.battery {grid-area:3/5;--node-color:var(--_selfa-battery);}
      .home {grid-area:5/3;--node-color:var(--_selfa-home);}.inverter .power {font-size:22px;letter-spacing:1px;}
      .soc-track {width:80%;height:6px;background:color-mix(in srgb,var(--_selfa-battery) 18%,var(--_selfa-surface));border-radius:4px;margin-top:10px;overflow:hidden;}
      .soc-fill {height:100%;background:var(--_selfa-battery);width:0;}
      .section {border-top:1px solid var(--_selfa-line);padding-top:18px;margin-top:20px;}
      h3 {font-size:16px;font-weight:600;margin:0 0 14px;}
      .tiles {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;}
      .tile {background:var(--_selfa-node);border-radius:12px;padding:14px;min-width:0;}
      .label {font-size:13px;line-height:1.5;color:var(--_selfa-muted);}
      .number {display:block;font-size:21px;line-height:1.6;font-variant-numeric:tabular-nums;overflow-wrap:anywhere;}
      .energy .tile {background:none;padding:8px 0;}
      table {color:inherit;width:100%;border-collapse:collapse;font-size:14px;font-variant-numeric:tabular-nums;}
      th,td {padding:12px 4px;text-align:right;border-bottom:1px solid var(--_selfa-line);}
      th:first-child,td:first-child {text-align:left;}th {font-size:12px;color:var(--_selfa-muted);font-weight:400;}
      .caption {margin:12px 0 0;color:var(--_selfa-muted);font-size:12px;line-height:1.5;}
      .backup-row {display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:14px;}.backup-row ha-icon {color:var(--_selfa-home);}
      .battery-readings {display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;color:var(--_selfa-muted);font-size:13px;}
      .empty {font-size:14px;padding:12px 0;color:var(--_selfa-muted);}
      [hidden] {display:none!important;}
      @container(max-width:560px) {.flow {grid-template-columns:minmax(0,1fr) 18px minmax(0,1.15fr) 18px minmax(0,1fr);}.power {font-size:22px;}.node {padding:9px 4px;}.node-label,.detail {font-size:12px;}.number {font-size:19px;}}
      @container(max-width:370px) {.flow {grid-template-columns:minmax(0,1fr) 12px minmax(0,1.15fr) 12px minmax(0,1fr);grid-template-rows:170px 28px 176px 28px 142px;}.power {font-size:18px;}.inverter .power {font-size:17px;letter-spacing:.5px;}.node-label,.detail {font-size:11px;}.node-label {margin-bottom:5px;}.detail {margin-top:4px;}.tiles {grid-template-columns:repeat(2,minmax(0,1fr));}.number {font-size:18px;}ha-card {padding:16px 10px;}}
      @media(prefers-reduced-motion:reduce) {.stream.active {animation:none;}}
    </style><ha-card>
      <div class="head"><div><h2 id="title"></h2><div class="caption">${t.flow} · ${t.readonly}</div></div><span class="status" id="status"></span></div>
      <div class="empty" id="empty" hidden></div><div id="content">
        <div class="flow" role="group" aria-label="${t.flow}">
          <div class="pv-group">
            ${node("pv","solar-power",`PV · ${t.string} 1`,'<div class="power" id="pv1">—</div><div class="detail" id="pv1detail"></div>')}
            ${node("pv","solar-power",`PV · ${t.string} 2`,'<div class="power" id="pv2">—</div><div class="detail" id="pv2detail"></div>')}
            <div class="pv-total">${t.total} · <strong id="pv">—</strong> / <span id="pvToday"></span></div>
          </div>
          ${[
            ["pv-link",[["pv1","M25 0V45H50V100"],["pv2","M75 0V45H50V100"]]],
            ["grid-link",[["grid","M100 50H0"]]],
            ["battery-link",[["battery","M100 50H0"]]],
            ["home-link",[["home","M50 0V100"]]],
          ].map(([cls,paths])=>`<div class="link ${cls}"><svg class="wires" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">${paths.map(([key,d])=>`<path class="wire" d="${d}" vector-effect="non-scaling-stroke"/><path id="flow-${key}" class="stream" d="${d}" vector-effect="non-scaling-stroke"/>`).join("")}</svg></div>`).join("")}
          ${node("grid","transmission-tower",t.grid,'<div class="power" id="grid">—</div><div class="detail" id="gridDirection"></div>')}
          ${node("inverter","chip",t.inverter,'<div class="power">SELFA</div><div class="detail" id="ac">—</div><div class="detail" id="inverterStatus"></div>')}
          ${node("battery","battery",t.battery,'<div class="power" id="soc">—</div><div class="detail"><span id="batteryMode"></span> · <span id="battery">—</span></div><div class="soc-track"><div class="soc-fill" id="socFill"></div></div>')}
          ${node("home","home-outline",t.home,'<div class="power" id="home">—</div><div class="detail" id="homeToday"></div>')}
        </div>
        <div class="caption">${t.home}: ${t.estimated}</div>
        <div class="section battery-readings"><span>${t.battery}</span><span id="batteryV"></span><span id="batteryI"></span><span id="soh"></span></div>
        <div class="section"><h3>${t.today}</h3><div class="tiles energy">
          ${[["daily_pv_gen",t.production],["daily_load",t.load],["daily_purch",t.imported],["daily_inj",t.exported],["daily_bat_chg",t.charged],["daily_bat_dchg",t.discharged]].map(([k,n])=>`<div class="tile"><span class="label">${n}</span><span class="number" data-energy="${k}"></span></div>`).join("")}
        </div></div>
        <div class="section"><h3>AC · ${t.voltage} / ${t.current}</h3><table><thead><tr><th>${t.phase}</th><th>V</th><th>A</th><th>${t.power}</th></tr></thead><tbody>
          ${["a","b","c"].map(k=>`<tr><td>${k.toUpperCase()}</td><td data-value="phase_${k}_v"></td><td data-value="phase_${k}_i"></td><td data-value="pmeter_${k}"></td></tr>`).join("")}
        </tbody></table><div class="caption">${t.sign}</div></div>
        <div class="section backup-row"><ha-icon icon="mdi:power-socket-eu" aria-hidden="true"></ha-icon><span>${t.backup}</span><strong id="backup">—</strong></div>
      </div></ha-card>`;
    this._built = true;
  }
  _update() {
    const r = this.shadowRoot,t = this._t,$=id=>r.getElementById(id);
    $("title").textContent=this._config.title||t.title;
    const found = !!this._map["sensor:total_pv_input"];
    $("empty").hidden=found;$("empty").textContent=t.missing;$("content").hidden=!found;
    if (!found) return;
    const status=this._state("working_status")?.state;
    const online=this._value("working_status_raw")!=null && this._state("connection","binary_sensor")?.state!=="off";
    $("status").textContent=online?(t[status]||t.other):t.offline;
    $("status").classList.toggle("online",online);
    $("inverterStatus").textContent=$("status").textContent;
    for(const [id,key] of [["pv","total_pv_input"],["grid","pmeter_3ph"],["ac","p_ac"],["battery","battery_p"],["backup","backup_total_p"],["pv1","pv1_p"],["pv2","pv2_p"]]) $(id).textContent=this._format(key,"kW");
    $("soc").textContent=this._format("soc","%",1);
    const soc=this._value("soc");
    $("socFill").style.width=(soc==null?0:Math.max(0,Math.min(100,soc)))+"%";
    const batteryPower=this._value("battery_p"),batteryMode=this._state("battery_mode")?.state;
    $("batteryMode").textContent=batteryPower!=null && Math.abs(batteryPower)<0.01?t.standby:(t[batteryMode]||"—");
    const meter=this._value("pmeter_3ph"),ac=this._value("p_ac");
    // Positive meter power means export by default; retain raw signed readouts.
    const exported=meter==null?null:meter*(this._config.grid_export_positive===false?-1:1);
    const home=ac==null||exported==null?null:ac-exported;
    $("home").textContent=this._formatNumber(home,"kW");
    $("gridDirection").textContent=!online||exported==null?"—":Math.abs(exported)<0.01?t.standby:exported>0?t.exporting:t.importing;
    $("pvToday").textContent=t.today+" · "+this._format("daily_pv_gen","kWh",1);
    $("homeToday").textContent=t.today+" · "+this._format("daily_load","kWh",1);
    $("soh").textContent="SOH "+this._format("soh","%",1);
    for(const [key,power,reverse,valid] of [
      ["pv1",this._value("pv1_p"),false,true],
      ["pv2",this._value("pv2_p"),false,true],
      ["grid",exported,exported<0,true],
      ["battery",batteryPower,batteryMode==="charging",["charging","discharging"].includes(batteryMode)],
      ["home",home,home<0,true],
    ]) {
      const stream=$("flow-"+key);
      stream.classList.toggle("active",online&&valid&&power!=null&&Math.abs(power)>=0.01&&this._config.animate!==false);
      stream.classList.toggle("reverse",reverse);
    }
    for(const k of ["pv1","pv2"]) $(k+"detail").textContent=this._format(k+"_v","V",1)+" · "+this._format(k+"_i","A",1);
    $("batteryV").textContent=this._format("battery_v","V",1);$("batteryI").textContent=this._format("battery_i","A",1);
    for(const el of r.querySelectorAll("[data-energy]")) el.textContent=this._format(el.dataset.energy,"kWh",1);
    for(const el of r.querySelectorAll("[data-value]")) el.textContent=this._format(el.dataset.value,el.dataset.value.startsWith("pmeter")?"kW":"",el.dataset.value.startsWith("pmeter")?3:1);

  }
}

function defineSelfaCard() {
  if (!window.customElements.get("selfa-card")) window.customElements.define("selfa-card",SelfaCard);
}
window.customElements.whenDefined("home-assistant").then(defineSelfaCard);
window.customCards=window.customCards||[];
if (!window.customCards.some(c=>c.type==="selfa-card")) window.customCards.push({type:"selfa-card",name:"Selfa SFH",description:"PV, battery, grid and backup · direct Modbus",preview:true});
console.info("SELFA-CARD",SELFA_CARD_VERSION);
