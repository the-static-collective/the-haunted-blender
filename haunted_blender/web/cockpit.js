const S={view:null,resume:null,id:null,media:null,engine:null,provider:null,preview:null};
const $=id=>document.getElementById(id);
const esc=v=>String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
const tc=v=>"temp-"+String(v||"sleeping").toLowerCase();
const tm=v=>{v=Math.max(0,Number(v||0));return Math.floor(v/60)+":"+Math.floor(v%60).toString().padStart(2,"0");};
const usd=micros=>"$"+(Number(micros||0)/1000000).toFixed(4);

async function api(url,opt={}){
  const r=await fetch(url,{cache:"no-store",...opt,headers:{...(opt.body&&!(opt.body instanceof Blob)?{"Content-Type":"application/json"}:{}),...(opt.headers||{})}});
  const d=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(d.error||("HTTP "+r.status));
  return d;
}
function toast(msg,bad=false){
  const e=$("toast");e.textContent=msg;e.className="toast show"+(bad?" error":"");
  clearTimeout(toast.t);toast.t=setTimeout(()=>e.className="toast",3000);
}
function section(){return S.view?.sections?.find(x=>x.id===S.id)||null;}
function mediaUrl(p){return "/media/"+p.split("/").map(encodeURIComponent).join("/");}
function mainMedia(){return S.media?.scene||S.media?.sixup||S.media?.candidates?.[0]||null;}

async function refresh(first=false){
  [S.view,S.resume]=await Promise.all([api("/api/view"),api("/api/resume")]);
  if(first||!S.view.sections.some(x=>x.id===S.id))S.id=S.view.sections[0]?.id||null;
  $("project-title").textContent=S.view.title;
  $("local-only").checked=!!S.view.localOnly;
  $("resume-jobs").textContent=S.view.resume.unresolvedProviderJobs;
  $("resume-dreams").textContent=S.view.resume.unbornSixups;
  $("resume-scenes").textContent=S.view.resume.keptScenesAwaitingRender;
  $("project-status").textContent=S.view.localOnly?"LOCAL ONLY - remote motion locked":"REMOTE MOTION ARMED";
  drawStrip();
  await drawSelected();
}
function drawStrip(){
  const h=$("sections");h.innerHTML="";
  for(const x of S.view.sections){
    const b=document.createElement("button");
    b.className="section-card "+tc(x.temperature)+(x.id===S.id?" selected":"");
    b.innerHTML='<div class="name">'+esc(x.label)+'</div>'+
      '<div class="time">'+tm(x.start)+' -> '+tm(x.end)+'</div>'+
      '<div class="temperature-chip '+tc(x.temperature)+'">'+esc(x.temperature.toUpperCase())+'</div>'+
      '<div class="marks">'+
      (x.hasDreams?"<span>* dreams</span>":"")+
      (x.hasScene?"<span>scene</span>":"")+
      (x.awakeningCount?("<span>awaken "+x.awakeningCount+"</span>"):"")+
      (x.witnessed?"<span>witnessed</span>":"")+
      '</div>';
    b.onclick=async()=>{S.id=x.id;S.preview=null;drawStrip();await drawSelected();};
    h.appendChild(b);
  }
}
async function drawSelected(){
  const x=section();
  if(!x){S.media=null;S.engine=null;S.provider=null;drawViewer();drawControls();return;}
  [S.media,S.engine,S.provider]=await Promise.all([
    api("/api/media-view/"+encodeURIComponent(x.id)),
    api("/api/engine-view/"+encodeURIComponent(x.id)),
    api("/api/provider-view/"+encodeURIComponent(x.id))
  ]);
  $("selected-title").textContent=x.label;
  $("selected-temp").textContent=x.temperature.toUpperCase();
  $("selected-temp").className="temperature-chip "+tc(x.temperature);
  $("viewer-title").textContent=x.label;
  $("viewer-eyebrow").textContent=x.kind.toUpperCase()+" - "+tm(x.start)+"-"+tm(x.end);
  drawViewer();drawControls();
  $("evidence").textContent=JSON.stringify({
    section:x,engine:S.engine,provider:S.provider,media:S.media,resume:S.resume?.resume,
    blackBox:S.resume?.blackBox?{lanes:S.resume.blackBox.lanes,laws:S.resume.blackBox.laws}:null
  },null,2);
}
function trackedCandidate(relativePath){
  return (S.provider?.candidates||[]).some(c=>c.relativePath===relativePath);
}
function drawViewer(){
  const x=section(),stage=$("primary-stage"),board=$("candidate-board");board.innerHTML="";
  const m=S.preview?{path:S.preview}:mainMedia();
  if(m){
    stage.className="primary-stage";
    stage.innerHTML='<video id="primary-video" controls playsinline preload="metadata" src="'+mediaUrl(m.path)+'"></video>';
  }else{
    stage.className="primary-stage empty-stage";
    stage.innerHTML='<div class="stage-empty"><strong>'+(x?esc(x.temperature.toUpperCase()):"Pick a section.")+'</strong><span>'+(x?"GROW will make the first six-up automatically.":"Six-up, scene, or current cut appears here.")+'</span></div>';
  }
  for(const c of S.media?.candidates||[]){
    const a=document.createElement("article"),cost=c.costClass||"deterministic";
    const canKeep=section()?.temperature==="awakening"&&trackedCandidate(c.path);
    a.className="candidate";
    a.innerHTML='<video class="candidate-video" controls playsinline preload="metadata" src="'+mediaUrl(c.path)+'"></video>'+
      '<div class="candidate-meta"><span>'+esc(c.label||c.providerId||"Candidate")+'</span>'+
      '<span class="cost-pill cost-'+esc(cost)+'">'+esc(cost)+'</span></div>'+
      (canKeep?'<button class="candidate-keep">KEEP THIS TAKE</button>':"");
    const keep=a.querySelector(".candidate-keep");
    if(keep)keep.onclick=()=>keepCandidate(c.path);
    board.appendChild(a);
  }
}
function proposalSelect(){
  const proposals=S.engine?.proposals||[];
  if(!proposals.length)return '<p>No six-up proposals are indexed yet.</p>';
  return '<label>Future to KEEP<select id="field-slot">'+proposals.map(p=>
    '<option value="'+p.slot+'">'+p.slot+' - '+esc(p.label)+' ('+esc((p.traits||[]).join(", "))+')</option>'
  ).join("")+'</select></label>';
}
function quoteBlock(){
  const q=S.provider?.quote,a=S.provider?.attempt;
  if(!q||!a)return "";
  const amount=q.wholeJobUsdMicros!=null?usd(q.wholeJobUsdMicros):(esc(q.amount??"?")+" "+esc(q.denomination||"units"));
  return '<div class="quote-card"><div class="eyebrow">EXACT QUOTE</div>'+
    '<strong>'+esc(a.providerId)+' / '+esc(a.model)+'</strong>'+
    '<span>'+amount+' · '+Number(q.generatedDurationSeconds||0).toFixed(2)+'s generated</span></div>';
}
function drawControls(){
  const x=section(),f=$("action-form"),c=$("door-copy"),t=$("door-title");
  const b={grow:$("grow-button"),keep:$("keep-button"),awaken:$("awaken-button"),play:$("play-button")};
  Object.values(b).forEach(z=>z.disabled=true);f.innerHTML="";
  b.play.disabled=!S.view?.sections?.some(s=>s.hasScene);
  b.awaken.textContent="AWAKEN";
  if(!x){t.textContent="Select a section";c.textContent="The Cockpit exposes only state-valid actions.";return;}
  t.textContent=x.temperature.toUpperCase();
  if(!S.engine?.configured){
    c.textContent="One-time engine configuration is missing. Configure the cutout kit and source receipts once; the verbs then stop asking for internal IDs.";
    f.innerHTML='<code>python -m haunted_blender.cockpit_engine_cli configure ...</code>';
    return;
  }
  if(["sleeping","haunted"].includes(x.temperature)){
    c.textContent="GROW will create the deterministic DREAMBREEDER ecology and render all six unborn previews.";
    b.grow.disabled=false;
  }else if(x.temperature==="dreaming"){
    c.textContent="Choose one visible future. KEEP is the human editorial decision; the longer deterministic section compiles immediately afterward.";
    f.innerHTML=proposalSelect();
    b.keep.disabled=!(S.engine.proposals||[]).length;
  }else if(x.temperature==="kept"){
    c.textContent="KEEP is recorded but scene rendering did not finish. Press KEEP again to resume the deterministic compiler.";
    f.innerHTML=proposalSelect();
    const slot=S.engine?.keptSlot;if(slot&&$("field-slot"))$("field-slot").value=String(slot);
    b.keep.disabled=!slot;
  }else if(x.temperature==="moving"||x.temperature==="alive"){
    const windows=S.engine?.awakeningWindows||[];
    c.textContent=S.view.localOnly?
      "The deterministic scene exists. PLAY works locally; LOCAL ONLY locks provider execution.":
      (windows.length?"AWAKEN prepares the bounded 006/007 plan, then immediately walks the cheapest configured adapter until a human hinge appears.":"This section has no bounded chorus/bridge AWAKEN window.");
    b.awaken.disabled=S.view.localOnly||!windows.length;
  }else if(x.temperature==="awakening"){
    const p=S.provider||{};
    if(!p.configured){
      c.textContent="Motion Organ is prepared, but no cockpit.adapters.json is configured.";
      f.innerHTML='<code>python -m haunted_blender.provider_driver_cli configure ...</code>';
      return;
    }
    if(p.reconcileRequired){
      c.textContent="A SUBMIT intent exists without a durable submit receipt. Do not resubmit. Reconcile the already-created vendor job here.";
      f.innerHTML='<label>Existing vendor job ID<input id="reconcile-job" placeholder="job_..." /></label>'+
        '<label>Submitted parameter SHA-256<input id="reconcile-sha" placeholder="64 lowercase hex characters" /></label>'+
        '<button id="reconcile-submit" class="secondary-button">RECONCILE EXISTING JOB</button>';
      setTimeout(()=>{const z=$("reconcile-submit");if(z)z.onclick=reconcileSubmit;},0);
      return;
    }
    if(p.approvalRequired){
      c.textContent="The exact paid quote is inside budget, but SUBMIT is blocked until a separate one-time approval.";
      f.innerHTML=quoteBlock()+'<button id="approve-spend" class="spend-button">APPROVE & SUBMIT '+usd(p.quote?.wholeJobUsdMicros)+'</button>';
      setTimeout(()=>{const z=$("approve-spend");if(z)z.onclick=approveSpend;},0);
      return;
    }
    if(p.nextAction==="PRESENT"){
      c.textContent="Candidate motion is ready. KEEP any tracked take in the board, or deliberately continue to the next planned provider.";
      if(p.canDeclineAndContinue){
        f.innerHTML='<button id="try-next" class="secondary-button">TRY NEXT PROVIDER</button>';
        setTimeout(()=>{const z=$("try-next");if(z)z.onclick=tryNext;},0);
      }
      return;
    }
    if(p.status==="reconcile_required"||p.nextAction==="STOP"){
      c.textContent="Execution stopped. An ambiguous submitted job must be reconciled; the router will not fall through and risk a duplicate charge.";
      return;
    }
    c.textContent=p.nextAction==="STATUS"?
      "The same vendor job is still active. AWAKEN polls that existing job; it does not resubmit.":
      ("Provider driver next action: "+(p.nextAction||"unknown")+". AWAKEN continues only that frozen plan.");
    b.awaken.textContent=p.nextAction==="STATUS"?"POLL":"CONTINUE";
    b.awaken.disabled=false;
  }else if(x.temperature==="witnessed"){
    c.textContent="The chosen provider take has been verified, human-KEEP'd, and spliced only into its frozen window. ALIVE admits that scene into the working cut.";
    f.innerHTML='<button id="bridge" class="secondary-button">Admit to current cut -> ALIVE</button>';
    setTimeout(()=>{const z=$("bridge");if(z)z.onclick=()=>direct("alive",{});},0);
  }
}
async function auto(verb,body={}){
  if(verb==="play"){
    const r=await api("/api/auto/play",{method:"POST",body:"{}"});
    S.preview=r.relativePath;drawViewer();
    const v=$("primary-video");if(v)await v.play();
    return r;
  }
  const r=await api("/api/auto/section/"+encodeURIComponent(S.id)+"/"+verb,{method:"POST",body:JSON.stringify(body)});
  await refresh();return r;
}
async function providerAction(action,body={}){
  const r=await api("/api/provider/section/"+encodeURIComponent(S.id)+"/"+action,{method:"POST",body:JSON.stringify(body)});
  await refresh();return r;
}
async function driveProvider(){
  const r=await providerAction("drive",{maxSteps:12});
  if(r.status==="approval_required")toast("Exact paid quote needs approval.");
  else if(r.status==="running")toast("Provider job is running; next AWAKEN polls the same job.");
  else if(r.status==="candidate_ready")toast("Candidate ready for human KEEP.");
  else if(r.status==="reconcile_required")toast("Ambiguous provider state: stopped for reconciliation.",true);
  return r;
}
async function approveSpend(){
  try{
    const amount=S.provider?.quote?.wholeJobUsdMicros;
    if(amount==null)throw new Error("Exact USD quote is missing.");
    await providerAction("approve",{expectedUsdMicros:amount,approvedAt:new Date().toISOString()});
    toast("One-time spend approval recorded.");
    await driveProvider();
  }catch(e){toast(e.message,true);}
}
async function reconcileSubmit(){
  try{
    const vendorRequestId=$("reconcile-job")?.value?.trim()||"";
    const submittedParameterSha256=$("reconcile-sha")?.value?.trim()||"";
    if(!vendorRequestId||!submittedParameterSha256)throw new Error("Existing vendor job ID and parameter SHA-256 are required.");
    await providerAction("reconcile",{vendorRequestId,submittedParameterSha256,observedAt:new Date().toISOString()});
    toast("Existing provider submission reconciled. Polling the same job.");
    await driveProvider();
  }catch(e){toast(e.message,true);}
}
async function tryNext(){
  try{
    await providerAction("decline",{reason:"artist requested another provider candidate"});
    toast("Candidate preserved; continuing route.");
    await driveProvider();
  }catch(e){toast(e.message,true);}
}
async function keepCandidate(path){
  try{
    await providerAction("accept",{candidatePath:path});
    toast("Take KEEP'd and spliced into the bounded window.");
  }catch(e){toast(e.message,true);}
}
async function direct(action,body){
  await api("/api/section/"+encodeURIComponent(S.id)+"/"+action,{method:"POST",body:JSON.stringify(body)});
  await refresh();
}
async function act(a){
  const button=$(a+"-button"),old=button.textContent;
  try{
    button.disabled=true;button.textContent=a==="play"?"BUILDING...":"WORKING...";
    if(a==="grow"){await auto("grow");toast("Six futures grown.");}
    else if(a==="keep"){
      const slot=Number($("field-slot")?.value||S.engine?.keptSlot||0);
      if(!slot)throw new Error("Choose one of the six futures.");
      await auto("keep",{slot});toast("KEEP compiled into a moving scene.");
    }else if(a==="awaken"){
      if(section()?.temperature!=="awakening"){
        await auto("awaken");
      }
      await driveProvider();
    }else{
      await auto("play");toast("Current cut preview built.");
    }
  }catch(e){toast(e.message,true);}
  finally{button.textContent=old;drawControls();}
}
async function upload(kind,input){
  const file=input.files?.[0];if(!file||!S.id)return;
  try{
    const headers={"X-Section-Id":S.id,"X-Media-Kind":kind,"X-File-Name":file.name,"X-Cost-Class":kind==="candidate"?(prompt("Cost class: free / included / paid","free")||"free"):"deterministic"};
    if(kind==="candidate"){headers["X-Provider-Id"]=prompt("Provider label (optional)","")||"";headers["X-Label"]=headers["X-Provider-Id"]||file.name;}
    const r=await fetch("/api/upload",{method:"POST",headers,body:file}),d=await r.json().catch(()=>({}));
    if(!r.ok)throw new Error(d.error||"Upload failed.");
    input.value="";await drawSelected();toast(kind+" attached.");
  }catch(e){toast(e.message,true);}
}
function sync(){
  const vs=[...document.querySelectorAll(".candidate-video")];
  if(!vs.length)return toast("No candidate videos.",true);
  if(vs.some(v=>!v.paused)){vs.forEach(v=>v.pause());return;}
  const t=Math.min(...vs.map(v=>Number.isFinite(v.currentTime)?v.currentTime:0));
  vs.forEach(v=>v.currentTime=t);Promise.allSettled(vs.map(v=>v.play()));
}
$("refresh").onclick=()=>refresh().catch(e=>toast(e.message,true));
$("local-only").onchange=async e=>{try{await api("/api/local-only",{method:"POST",body:JSON.stringify({enabled:e.target.checked})});await refresh();}catch(x){toast(x.message,true);}};
["grow","keep","awaken","play"].forEach(a=>$(a+"-button").onclick=()=>act(a));
$("sync-play").onclick=sync;
$("upload-sixup").onchange=e=>upload("sixup",e.target);
$("upload-scene").onchange=e=>upload("scene",e.target);
$("upload-candidate").onchange=e=>upload("candidate",e.target);
refresh(true).catch(e=>toast(e.message,true));
