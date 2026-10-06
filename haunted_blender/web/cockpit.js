const state = {view:null,resume:null,selectedId:null,media:null};
const $ = (id) => document.getElementById(id);

async function api(url, options={}) {
  const response = await fetch(url, {
    cache:"no-store",
    ...options,
    headers:{
      ...(options.body && !(options.body instanceof Blob) ? {"Content-Type":"application/json"} : {}),
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed: ${response.status}`);
  return data;
}

function toast(message,error=false){
  const el=$("toast");
  el.textContent=message;
  el.className=`toast show${error ? " error" : ""}`;
  clearTimeout(toast.timer);
  toast.timer=setTimeout(()=>{el.className="toast";},2600);
}

function fmtTime(seconds){
  const value=Math.max(0,Number(seconds||0));
  const m=Math.floor(value/60);
  const s=Math.floor(value%60).toString().padStart(2,"0");
  return `${m}:${s}`;
}
function tempClass(value){return `temp-${String(value||"sleeping").toLowerCase()}`;}
function sectionById(id){return state.view?.sections?.find((section)=>section.id===id)||null;}

async function refresh({keepSelection=true}={}){
  const [view,resume]=await Promise.all([api("/api/view"),api("/api/resume")]);
  state.view=view; state.resume=resume;
  $("project-title").textContent=view.title;
  $("local-only").checked=!!view.localOnly;
  $("resume-hobs").textContent=view.resume.unresolvedProviderJobs;
  $("resume-dreams").textContent=view.resume.unbornSixups;
  $("resume-scenes").textContent=view.resume.keptScenesAwaitingRender;
  $("project-status").textContent=view.localOnly ? "LOCAL ONLY - remote motion locked" : "REMOTE MOTION ARMED";
  if(!keepSelection || !sectionById(state.selectedId)) state.selectedId=view.sections[0]?.id||null;
  renderSections();
  await refreshSelected();
}

function renderSections(){
  const host=$("sections"); host.innerHTML="";
  for(const section of state.view.sections){
    const button=document.createElement("button");
    button.className=`section-card ${tempClass(section.temperature)}${section.id===state.selectedId ?" selected":""}`;
    button.dataset.sectionId=section.id;
    button.innerHTML=`
      <div class="name">${escapeHtml(section.label)}</div>
      <div class="time">${fmtTime(section.start)} -> ${fmtTime(section.end)}</div>
      <div class="temperature-chip ${tempClass(section.temperature)}">${escapeHtml(section.temperature.toUpperCase())}</div>
      <div class="marks">
        ${section.hasDreams ? "<span>* dreams</span>" : ""}
        ${section.hasScene ? "<span>scene</span>" : ""}
        ${section.awakeningCount ? `<span>awaken ${section.awakeningCount}</span>` : ""}
        ${section.hauntCount ? `<span>ghost ${section.hauntCount}</span>` : ""}
        ${section.witnessed ? "<span>witnessed</span>" : ""}
      </div>`;
    button.addEventListener("click",async()=>{state.selectedId=section.id;renderSections();await refreshSelected();});
    host.appendChild(button);
  }
}

async function refreshSelected(){
  const section=sectionById(state.selectedId);
  if(!section){state.media=null;$("selected-title").textContent="Choose a section";$("selected-temp").textContent="SLEEPING";renderViewer(null);renderControls(null);return;}
  state.media=await api(`/api/media-view/${encodeURIComponent(section.id)}`);
  $("selected-title").textContent=section.label;
  $("selected-temp").textContent=section.temperature.toUpperCase();
  $("selected-temp").className=`temperature-chip ${tempClass(section.temperature)}`;
  $("viewer-title").textContent=section.label;
  $("viewer-eyebrow").textContent=`${section.kind.toUpperCase()} - ${fmtTime(section.start)}-${fmtTime(section.end)}`;
  renderViewer(section);renderControls(section);renderEvidence(section);
}
