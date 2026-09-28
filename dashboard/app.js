const files = {
  metrics: "../data/generated/retention_metrics.csv",
  context: "../data/generated/metric_signal_context.csv",
  signals: "../data/generated/external_signals_curated.csv",
  quality: "../data/generated/quality_report.json",
  objectives: "../data/fixtures/retention_objectives.csv",
};
const targets = {}, labels = {};
const indicatorLabels = { unemployment_rate: "Unemployment rate", job_vacancy_rate: "Job vacancy rate", consumer_price_inflation: "Consumer-price inflation" };
const unitLabels = { annual_percent_change: "% annual change", percent_of_labour_force: "% of labour force", percent: "%" };
const sources = {
  unemployment_rate: "https://ec.europa.eu/eurostat/databrowser/view/UNE_RT_M/",
  job_vacancy_rate: "https://ec.europa.eu/eurostat/databrowser/view/JVS_Q_NACE2/",
  consumer_price_inflation: "https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG",
};
let metrics = [], context = [], signals = [], quality = {};

function csv(text) {
  const records=[]; let row=[], field="", quoted=false;
  for(let i=0;i<text.length;i++) { const c=text[i]; if(quoted && c==='"' && text[i+1]==='"'){field+='"';i++;} else if(c==='"'){quoted=!quoted;} else if(c===',' && !quoted){row.push(field);field="";} else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(field);if(row.some(value=>value!==""))records.push(row);row=[];field="";} else field+=c; }
  if(field!==""||row.length){row.push(field);records.push(row);}
  const keys=records.shift(); return records.map(values=>Object.fromEntries(keys.map((key,index)=>[key,values[index]??""])));
}
function choices(id, values, format = value => value) { const select=document.querySelector(id), previous=select.value; select.innerHTML=values.map(value=>`<option value="${escapeHtml(value)}">${escapeHtml(format(value))}</option>`).join(""); if(values.includes(previous))select.value=previous; }
function pct(value) { return `${(Number(value)*100).toFixed(1)}%`; }
function monthKey(date){return String(date).slice(0,7);}
function fmtNumber(value,digits=1){return Number(value).toLocaleString(undefined,{maximumFractionDigits:digits});}
function formatSignalValue(value,unit){const amount=fmtNumber(value,2);if(unit==="percent")return `${amount}%`;if(unit==="annual_percent_change")return `${amount}% annual change`;if(unit==="percent_of_labour_force")return `${amount}% of labour force`;return `${amount}${unit?` ${unitLabels[unit]||unit}`:""}`;}
function escapeHtml(value){return String(value).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;");}
function enableChartTooltips(svg){
  if(svg.dataset.tooltipReady)return;
  svg.dataset.tooltipReady="true";
  const wrap=svg.closest(".chart-wrap"),tooltip=wrap.querySelector(".chart-tooltip");
  let pendingFrame;
  const show=point=>{
    if(!point)return;
    tooltip.textContent=point.dataset.tooltip;tooltip.setAttribute("aria-hidden","false");
    const pointBounds=point.getBoundingClientRect(),tipWidth=tooltip.offsetWidth,tipHeight=tooltip.offsetHeight;
    tooltip.style.left=`${Math.max(tipWidth/2+10,Math.min(window.innerWidth-tipWidth/2-10,pointBounds.left+pointBounds.width/2))}px`;
    const above=pointBounds.top-tipHeight-10;
    tooltip.style.top=`${above>=8?above:Math.min(window.innerHeight-tipHeight-8,pointBounds.bottom+10)}px`;
    cancelAnimationFrame(pendingFrame);
    pendingFrame=requestAnimationFrame(()=>tooltip.classList.add("is-visible"));
  };
  svg.onpointerover=event=>show(event.target.closest("circle[data-tooltip]"));
  const hide=()=>{cancelAnimationFrame(pendingFrame);tooltip.classList.remove("is-visible");tooltip.setAttribute("aria-hidden","true");};
  svg.onpointerleave=hide;
  window.addEventListener("resize",hide);
  svg.addEventListener("focusin",event=>show(event.target.closest("circle[data-tooltip]")));
  svg.addEventListener("focusout",event=>{if(!svg.contains(event.relatedTarget))hide();});
  svg.addEventListener("keydown",event=>{if(event.key==="Escape")hide();});
}

function render() {
  const objective=document.querySelector("#objective").value, country=document.querySelector("#country").value, segment=document.querySelector("#segment").value;
  const from=document.querySelector("#date-from").value||"2021-01", to=document.querySelector("#date-to").value||"2025-12";
  const inRange=row=>monthKey(row.reporting_period)>=from&&monthKey(row.reporting_period)<=to;
  const periodRows=metrics.filter(row=>row.objective_id===objective&&row.country_code===country&&row.segment_value===segment&&inRange(row));
  const selected=periodRows.filter(row=>row.metric_value!=="").sort((a,b)=>a.reporting_period.localeCompare(b.reporting_period));
  const status=document.querySelector("#status"), content=document.querySelector("#content");
  document.querySelector("#censored").textContent=periodRows.reduce((total,row)=>total+Number(row.censored_population||0),0).toLocaleString();
  const isTurnover=objective==="REGRETTED_TURNOVER_12M";
  document.querySelector("#population-label").textContent=isTurnover?"Average headcount":"Eligible population";
  if(!selected.length){
    content.hidden=false;
    status.textContent=from>to?"Choose a start date on or before the end date.":periodRows.length?"No mature observations fall inside this range. Select an earlier cohort range to see retention rates.":"No observations match this selection. Try a different country, segment, or date range.";
    for(const id of ["#latest-value","#latest-period","#population","#target-status","#target-copy"])document.querySelector(id).textContent="—";
    document.querySelector("#sample-warning").textContent="";
    document.querySelector("#population-note").textContent="No mature observations";
    document.querySelector("#chart").innerHTML="";
    document.querySelector("#signals").textContent="No mature reporting period selected.";
    renderRelationship(objective,segment,from,to);
    return;
  }
  content.hidden=false; status.textContent=`${selected.length} mature reporting periods shown for ${labels[objective]}.`;
  const latest=selected.at(-1), [target,direction]=targets[objective], hit=direction==="at least"?Number(latest.metric_value)>=target:Number(latest.metric_value)<=target;
  document.querySelector("#latest-value").textContent=pct(latest.metric_value); document.querySelector("#latest-period").textContent=latest.reporting_period;
  document.querySelector("#population-note").textContent=isTurnover?`${latest.regretted_exits||0} regretted exits in trailing year`:"at latest mature cohort";
  document.querySelector("#population").textContent=fmtNumber(latest.eligible_population);
  const sampleSize=Number(latest.eligible_population);
  document.querySelector("#sample-warning").textContent=sampleSize<30?`Small sample (n=${fmtNumber(sampleSize,0)}). Treat this rate as an early signal.`:"";
  const statusNode=document.querySelector("#target-status");statusNode.textContent=hit?"On target":"Outside target";statusNode.className=hit?"good":"warn";document.querySelector("#target-copy").textContent=`${direction} ${pct(target)}`;
  document.querySelector("#censored").textContent=periodRows.reduce((total,row)=>total+Number(row.censored_population||0),0).toLocaleString();
  drawTrend(selected,objective);
  const currentSignals=context.filter(row=>row.objective_id===objective&&row.country_code===country&&row.reporting_period===latest.reporting_period&&row.segment_value===segment);
  document.querySelector("#signals").innerHTML=currentSignals.length?currentSignals.map(row=>`<div class="signal"><strong>${indicatorLabels[row.indicator]||row.indicator}: ${formatSignalValue(row.signal_value,row.unit)}</strong><small>${row.provider} · ${row.frequency} · period ${row.signal_period_end} · available ${row.signal_available_on} · age ${row.signal_age_days} days</small><a href="${sources[row.indicator]||row.source_url}" target="_blank" rel="noreferrer">View source</a></div>`).join(""):"<p>No signal met the documented as-of rule in this period.</p>";
  renderRelationship(objective,segment,from,to);
}
function drawTrend(rows,objective){
  const width=800,height=260,pad=46,values=rows.map(row=>Number(row.metric_value)),maxValue=Math.max(...values),upper=objective==="REGRETTED_TURNOVER_12M"?Math.max(maxValue*1.2,targets[objective][0]*1.2):1;
  const dates=rows.map(row=>Date.parse(row.reporting_period)),span=dates.at(-1)-dates[0];
  const coords=values.map((value,index)=>[pad+(span?(dates[index]-dates[0])/span:0)*(width-2*pad),height-pad-(value/upper)*(height-2*pad)]);
  const ticks=[0,upper/2,upper]; const svg=document.querySelector("#chart");
  svg.innerHTML=`${ticks.map(value=>{const y=height-pad-(value/upper)*(height-2*pad);return `<line class="grid" x1="${pad}" y1="${y}" x2="${width-pad}" y2="${y}"/><text class="axis-label" x="4" y="${y+4}">${pct(value)}</text>`}).join("")}<path class="trend" d="M ${coords.map(point=>point.join(" ")).join(" L ")}"/>${coords.map((point,index)=>{const row=rows[index],isTurnover=objective==="REGRETTED_TURNOVER_12M",detail=isTurnover?`${fmtNumber(row.regretted_exits||0,0)} exits / avg. headcount ${fmtNumber(row.eligible_population,0)}`:`${fmtNumber(row.retained_population,0)} of ${fmtNumber(row.eligible_population,0)} hires retained`;const shortLabel=isTurnover?"12-month regretted turnover":objective==="SENIOR_HIRE_12M"?"12-month retention":"6-month retention";const tip=`${monthKey(row.reporting_period)} · ${shortLabel} ${pct(values[index])}\n${detail}`;return `<circle class="point" cx="${point[0]}" cy="${point[1]}" r="5" tabindex="0" role="img" aria-label="${escapeHtml(tip)}" data-tooltip="${escapeHtml(tip)}"><title>${escapeHtml(tip)}</title></circle>`}).join("")}<text class="axis-label" x="${pad}" y="${height-7}">${monthKey(rows[0].reporting_period)}</text><text class="axis-label" x="${width-pad-42}" y="${height-7}">${monthKey(rows.at(-1).reporting_period)}</text>`;
  enableChartTooltips(svg);
}
function renderRelationship(objective,segment,from,to){
  const indicator=document.querySelector("#indicator").value;
  // First collapse carried-forward signals to their original observation periods,
  // then average paired periods within country. Each plotted point is one country.
  const rows=context.filter(row=>row.objective_id===objective&&row.segment_value===segment&&row.indicator===indicator&&monthKey(row.reporting_period)>=from&&monthKey(row.reporting_period)<=to&&row.metric_value!==""&&row.signal_value!=="");
  const byCountryPeriod=new Map();
  for(const row of rows){const key=`${row.country_code}|${row.signal_period_end}`;const item=byCountryPeriod.get(key)||{country:row.country_code,metric:[],signal:[]};item.metric.push(Number(row.metric_value));item.signal.push(Number(row.signal_value));byCountryPeriod.set(key,item);}
  const countryMeans=new Map();
  for(const item of byCountryPeriod.values()){const country=countryMeans.get(item.country)||{metric:[],signal:[]};country.metric.push(item.metric.reduce((a,b)=>a+b,0)/item.metric.length);country.signal.push(item.signal[0]);countryMeans.set(item.country,country);}
  const points=[...countryMeans].map(([country,item])=>({country,x:item.signal.reduce((a,b)=>a+b,0)/item.signal.length,y:item.metric.reduce((a,b)=>a+b,0)/item.metric.length})).filter(point=>Number.isFinite(point.x)&&Number.isFinite(point.y));
  const xs=points.map(point=>point.x),ys=points.map(point=>point.y),r=pearson(xs,ys),interval=fisherInterval(r,points.length);
  document.querySelector("#relationship-stat").textContent=r===null?"Insufficient data":`r = ${r.toFixed(2)}${interval?` · 95% interval ${interval[0].toFixed(2)} to ${interval[1].toFixed(2)}`:""}`;
  document.querySelector("#relationship-note").textContent=`${points.length} country averages · ${indicatorLabels[indicator]||indicator} · ${points.length<4?"too few countries for a useful interval":"interval assumes independent country averages"}`;
  const unit=context.find(row=>row.indicator===indicator)?.unit||"";
  drawScatter(points,indicator,objective,unit);
}
function pearson(xs,ys){if(xs.length<3)return null;const xm=xs.reduce((a,b)=>a+b,0)/xs.length,ym=ys.reduce((a,b)=>a+b,0)/ys.length;let top=0,xx=0,yy=0;for(let i=0;i<xs.length;i++){top+=(xs[i]-xm)*(ys[i]-ym);xx+=(xs[i]-xm)**2;yy+=(ys[i]-ym)**2;}return xx&&yy?top/Math.sqrt(xx*yy):null;}
function fisherInterval(r,n){if(r===null||n<=3)return null;const safe=Math.max(-.999,Math.min(.999,r)),z=Math.atanh(safe),margin=1.96/Math.sqrt(n-3);return [Math.tanh(z-margin),Math.tanh(z+margin)];}
function drawScatter(points,indicator,objective,unit){
  const svg=document.querySelector("#relationship-chart"),w=800,h=260,left=78,right=28,top=22,bottom=66;
  if(points.length<2){svg.innerHTML="<text x='60' y='120' class='axis-label'>Not enough country-level observations for this selection.</text>";return;}
  const valuesX=points.map(point=>point.x),valuesY=points.map(point=>point.y),minValueX=Math.min(...valuesX),maxValueX=Math.max(...valuesX),spanX=maxValueX-minValueX;
  const xPadding=spanX?spanX*.08:Math.max(Math.abs(minValueX)*.08,.5),minX=minValueX-xPadding,maxX=maxValueX+xPadding;
  const maxY=Math.max(...valuesY),yMax=objective==="REGRETTED_TURNOVER_12M"?Math.max(Math.ceil(maxY*100)/100,targets[objective][0]*1.1):1;
  const plotWidth=w-left-right,plotHeight=h-top-bottom,xAt=value=>left+(value-minX)/(maxX-minX)*plotWidth,yAt=value=>h-bottom-value/yMax*plotHeight;
  const yLabel=objective==="REGRETTED_TURNOVER_12M"?"Average 12-month regretted turnover":objective==="SENIOR_HIRE_12M"?"Average 12-month retention":"Average 6-month retention";
  const xLabel=`${indicatorLabels[indicator]||indicator}${unit?` (${unitLabels[unit]||unit})`:""}`;
  const xTicks=Array.from({length:4},(_,index)=>minX+(maxX-minX)*index/3),yTicks=[0,yMax/2,yMax];
  const grid=yTicks.map(value=>{const y=yAt(value);return `<line class="grid" x1="${left}" y1="${y}" x2="${w-right}" y2="${y}"/><text class="axis-label" x="${left-9}" y="${y+4}" text-anchor="end">${pct(value)}</text>`}).join("");
  const ticks=xTicks.map(value=>{const x=left+(value-minX)/(maxX-minX)*plotWidth;return `<line class="grid vertical-grid" x1="${x}" y1="${top}" x2="${x}" y2="${h-bottom}"/><text class="axis-label" x="${x}" y="${h-bottom+17}" text-anchor="middle">${fmtNumber(value,1)}</text>`}).join("");
  const circles=points.map(point=>{const x=left+(point.x-minX)/(maxX-minX)*plotWidth,y=yAt(point.y),tip=`${point.country} · ${xLabel}: ${formatSignalValue(point.x,unit)}\n${yLabel}: ${pct(point.y)} · country average`;return `<circle class="scatter-point" cx="${x}" cy="${y}" r="7" tabindex="0" role="img" aria-label="${escapeHtml(tip)}" data-tooltip="${escapeHtml(tip)}"><title>${escapeHtml(tip)}</title></circle><text class="country-label" x="${x+9}" y="${y-8}">${escapeHtml(point.country)}</text>`}).join("");
  svg.setAttribute("viewBox",`0 0 ${w} ${h}`);
  svg.setAttribute("aria-label",`${yLabel} versus ${xLabel} by country`);
  svg.innerHTML=`${grid}${ticks}<line class="axis" x1="${left}" y1="${h-bottom}" x2="${w-right}" y2="${h-bottom}"/><line class="axis" x1="${left}" y1="${top}" x2="${left}" y2="${h-bottom}"/>${circles}<text class="axis-label" x="${left+plotWidth/2}" y="${h-7}" text-anchor="middle">${escapeHtml(xLabel)}</text><text class="axis-label" transform="translate(16 ${top+plotHeight/2}) rotate(-90)" text-anchor="middle">${escapeHtml(yLabel)}</text>`;
  enableChartTooltips(svg);
}
function renderQualityAndSources(){
  const valid=Number(quality.valid_rows||0),excluded=Number(quality.excluded_rows||0),total=Number(quality.input_rows||0),externalRows=Number(quality.external_signal_rows||0);
  document.querySelector("#quality-summary").innerHTML=`<h3>Workforce data</h3><p>${valid.toLocaleString()} of ${total.toLocaleString()} records included. ${excluded.toLocaleString()} excluded after validation.</p><p>${quality.duplicate_rows||0} duplicate rows, ${quality.invalid_country||0} invalid country values, ${quality.missing_or_future_hire_date||0} missing/future hire dates, and ${quality.termination_before_hire||0} terminations before hire date.</p><p>${quality.unknown_regretted_valid_termination||0} valid terminations have unknown regretted status and are excluded from regretted exits.</p><p>${externalRows.toLocaleString()} external observations across ${quality.external_indicators||0} indicators. Workforce extract as of 2025-12-31.</p>`;
  const items=[...new Set(signals.map(row=>row.indicator))].map(indicator=>{const group=signals.filter(row=>row.indicator===indicator),countries=new Set(group.map(row=>row.country_code)),periods=group.map(row=>row.period_end).sort();const item=group[0];return {indicator,provider:item.provider,frequency:item.frequency,unit:item.unit,access:item.source_access_date,url:sources[indicator],coverage:`${countries.size}/6 countries`,period:`${monthKey(periods[0])} to ${monthKey(periods.at(-1))}`};});
  document.querySelector("#source-register").innerHTML=`<h3>External sources and coverage</h3>${items.map(item=>`<p><a href="${item.url}" target="_blank" rel="noreferrer">${indicatorLabels[item.indicator]}</a><br><small>${item.provider} · ${item.frequency} · ${unitLabels[item.unit]||item.unit} · ${item.coverage} · ${item.period} · snapshot ${item.access}</small></p>`).join("")}<small>Lag estimates: monthly 45d · quarterly 90d · annual 120d.</small>`;
}
async function boot(){
  try{
    const [metricText,contextText,signalText,qualityJson,objectiveText]=await Promise.all([fetch(files.metrics).then(response=>{if(!response.ok)throw Error("metrics unavailable");return response.text();}),fetch(files.context).then(response=>{if(!response.ok)throw Error("context unavailable");return response.text();}),fetch(files.signals).then(response=>{if(!response.ok)throw Error("source coverage unavailable");return response.text();}),fetch(files.quality).then(response=>{if(!response.ok)throw Error("quality report unavailable");return response.json();}),fetch(files.objectives).then(response=>{if(!response.ok)throw Error("objectives unavailable");return response.text();})]);
    for(const row of csv(objectiveText)){
      if(!["NEW_HIRE_6M","SENIOR_HIRE_12M","REGRETTED_TURNOVER_12M"].includes(row.objective_id)||!["at_least","at_most"].includes(row.direction)||row.target_value===""||!Number.isFinite(Number(row.target_value)))throw Error("objective schema is invalid");
      labels[row.objective_id]=row.objective_name;
      targets[row.objective_id]=[Number(row.target_value),row.direction==="at_least"?"at least":"at most"];
    }
    if(Object.keys(targets).length!==3)throw Error("three objective definitions are required");
    metrics=csv(metricText);context=csv(contextText);signals=csv(signalText);quality=qualityJson;
    for(const [name,rows,required] of [["metrics",metrics,["objective_id","country_code","reporting_period","segment_value","metric_value","eligible_population"]],["context",context,["indicator","signal_value","metric_value","signal_period_end"]],["signals",signals,["indicator","provider","frequency","source_access_date"]]]){
      if(rows.length&&required.some(key=>!(key in rows[0])))throw Error(`${name} schema is invalid`);
    }
    if(!metrics.length){document.querySelector("#status").textContent="No workforce observations are available. Check the quality report and input data.";return;}
    choices("#objective",Object.keys(labels),value=>labels[value]);choices("#country",[...new Set(metrics.map(row=>row.country_code))].sort());
    const populateSegments=()=>{const objective=document.querySelector("#objective").value,country=document.querySelector("#country").value;const values=[...new Set(metrics.filter(row=>row.objective_id===objective&&row.country_code===country).map(row=>row.segment_value))].sort();choices("#segment",values,value=>value);render();};
    choices("#indicator",[...new Set(context.map(row=>row.indicator))],value=>indicatorLabels[value]||value);
    for(const selector of ["#objective","#country"])document.querySelector(selector).addEventListener("change",populateSegments);
    for(const selector of ["#segment","#indicator","#date-from","#date-to"])document.querySelector(selector).addEventListener("change",render);
    populateSegments();renderQualityAndSources();
  }catch(error){document.querySelector("#content").hidden=true;document.querySelector("#status").textContent=`Dashboard evidence failed to load: ${error.message}. Run the data workflow and serve the repository root.`;}
}
boot();
