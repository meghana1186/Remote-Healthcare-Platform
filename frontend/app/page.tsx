"use client";

import { useEffect, useState } from "react";
import {
  Activity, ArrowRight, CalendarDays, ChevronRight, Clock3, FileText,
  HeartPulse, LayoutDashboard, Menu, MessageSquare, Mic, ShieldCheck,
  Stethoscope, Users, X, Search, Video, MapPin, Upload, Send,
  BarChart3, ClipboardList, UserRound, LogOut, Wifi, RefreshCw
} from "lucide-react";
import { runTriage, getPatients, getProviders } from "../lib/api";

type View = "Overview" | "AI Triage" | "Appointments" | "Health Record" | "Care Team" | "Referrals" | "Impact";

const nav: [View, any][] = [
  ["Overview", LayoutDashboard],
  ["AI Triage", Activity],
  ["Appointments", CalendarDays],
  ["Health Record", FileText],
  ["Care Team", Users],
  ["Referrals", MapPin],
  ["Impact", BarChart3],
];

export default function Home() {
  const [active, setActive] = useState<View>("Overview");
  const [mobile, setMobile] = useState(false);

  return (
    <main className="app-shell">
      <aside className={`sidebar ${mobile ? "mobile-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><HeartPulse size={18} /></div>
          <div><div className="brand-name">RemoteCare</div><div className="brand-sub">AI CARE PLATFORM</div></div>
        </div>
        <div className="nav-label">Workspace</div>
        <nav>
          {nav.map(([label, Icon]) => (
            <button key={label} className={`nav-item ${active === label ? "active" : ""}`}
              onClick={() => { setActive(label); setMobile(false); }}>
              <Icon size={17}/><span>{label}</span>{active === label && <span className="nav-line"/>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="secure-card"><ShieldCheck size={17}/><div><strong>Private by design</strong><span>Encrypted clinical workflows</span></div></div>
          <button className="profile"><div className="avatar">AR</div><div className="profile-copy"><strong>Arjun Rao</strong><span>Patient account</span></div><ChevronRight size={15}/></button>
        </div>
      </aside>

      <section className="main">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobile(!mobile)}>{mobile ? <X size={20}/> : <Menu size={20}/>}</button>
          <div className="crumb"><span>Workspace</span><ChevronRight size={14}/><strong>{active}</strong></div>
          <div className="top-actions"><span className="status"><span className="status-dot"/> Care network online</span><div className="mini-avatar">AR</div></div>
        </header>
        <div className="content">
          {active === "Overview" && <Overview onNavigate={setActive}/>}
          {active === "AI Triage" && <Triage/>}
          {active === "Appointments" && <Appointments/>}
          {active === "Health Record" && <HealthRecord/>}
          {active === "Care Team" && <CareTeam/>}
          {active === "Referrals" && <Referrals/>}
          {active === "Impact" && <Impact/>}
          <footer className="footer"><span>RemoteCare AI v3.0</span><span>AI-assisted · Clinician-led · Privacy-first</span></footer>
        </div>
      </section>
    </main>
  );
}

function Overview({onNavigate}:{onNavigate:(v:View)=>void}) {
  return <>
    <section className="hero">
      <div><p className="eyebrow">MONDAY, 07 SEPTEMBER 2026</p><h1>Good morning, Arjun.</h1>
      <p className="hero-copy">Your care, organized in one quiet place. Get guided support, prepare for your next consultation, and keep your health record close.</p>
      <div className="hero-actions"><button className="primary" onClick={()=>onNavigate("AI Triage")}><Activity size={17}/> Start AI triage <ArrowRight size={16}/></button><button className="secondary" onClick={()=>onNavigate("Appointments")}><CalendarDays size={17}/> View appointments</button></div></div>
      <div className="hero-orbit"><div className="orbit-ring ring-one"/><div className="orbit-ring ring-two"/><div className="orbit-core"><HeartPulse size={31}/></div></div>
    </section>
    <div className="section-head"><div><span className="section-kicker">CARE AT A GLANCE</span><h2>Today</h2></div><button className="text-button" onClick={()=>onNavigate("Health Record")}>View health record <ArrowRight size={15}/></button></div>
    <section className="metric-grid">
      <Metric label="Next consultation" value="4:30 PM" note="Dr. Meera Sharma" icon={<Stethoscope size={18}/>}/>
      <Metric label="Care priority" value="Routine" note="No active alerts" icon={<ShieldCheck size={18}/>}/>
      <Metric label="Health record" value="12 items" note="2 reports need review" icon={<FileText size={18}/>}/>
    </section>
    <section className="dashboard-grid">
      <div className="glass-card triage-card"><div className="card-head"><div><span className="section-kicker">AI ASSISTANCE</span><h3>Talk through a symptom</h3></div><div className="soft-icon"><MessageSquare size={17}/></div></div>
      <p className="muted">Describe how you are feeling. RemoteCare checks for urgent signals, asks useful follow-up questions, and prepares a concise handoff for a clinician.</p>
      <div className="voice-box"><div className="voice-button"><Mic size={23}/></div><div><strong>Start with your voice</strong><span>Whisper-powered transcription</span></div><span className="live-pill">READY</span></div>
      <button className="wide-secondary" onClick={()=>onNavigate("AI Triage")}>Open AI triage workspace <ArrowRight size={16}/></button>
      <div className="safety-note"><ShieldCheck size={15}/><span>AI assistance does not replace a clinician.</span></div></div>
      <div className="glass-card appointment-card"><div className="card-head"><div><span className="section-kicker">UP NEXT</span><h3>Consultation</h3></div><span className="confirmed">CONFIRMED</span></div>
      <div className="doctor-row"><div className="doctor-avatar">MS</div><div><strong>Dr. Meera Sharma</strong><span>General Medicine</span></div></div>
      <div className="appointment-time"><Clock3 size={17}/><div><strong>Today, 4:30 PM</strong><span>Video consultation · 20 min</span></div></div>
      <button className="wide-secondary" onClick={()=>onNavigate("Appointments")}>Open consultation details <ArrowRight size={16}/></button></div>
    </section>
  </>;
}

function Triage() {
  const [text,setText]=useState(""); const [loading,setLoading]=useState(false); const [result,setResult]=useState<any>(null);
  async function submit(){ if(!text.trim()) return; setLoading(true); try{setResult(await runTriage(text));}catch(e){setResult({error:"Backend unavailable. Start FastAPI on port 8000."});}finally{setLoading(false)}}
  return <><PageTitle kicker="AI ASSISTANCE" title="Triage workspace" desc="A safety-first intake flow that structures patient information for clinician review."/>
    <div className="triage-layout">
      <div className="glass-card workspace-card">
        <div className="input-label">Describe what you are experiencing</div>
        <textarea value={text} onChange={e=>setText(e.target.value)} placeholder="Example: I have had a cough for three days and feel tired..." />
        <div className="composer-row"><span className="privacy"><ShieldCheck size={14}/> Processed through the RemoteCare safety layer</span><button className="primary" onClick={submit} disabled={loading}>{loading ? "Analyzing..." : "Run triage"} <Send size={15}/></button></div>
        <div className="suggestions"><button onClick={()=>setText("I have a mild headache since this morning.")}>Mild symptom</button><button onClick={()=>setText("I have chest pressure and trouble breathing.")}>Emergency test</button><button onClick={()=>setText("I have a cough for three days but can breathe normally.")}>Respiratory case</button></div>
      </div>
      <div className="glass-card result-card">
        <div className="card-head"><div><span className="section-kicker">CLINICIAN HANDOFF</span><h3>Assessment</h3></div><div className="soft-icon"><ClipboardList size={17}/></div></div>
        {!result ? <EmptyState title="Ready for intake" text="Your structured assessment will appear here after you run triage."/> :
        result.error ? <EmptyState title="API connection needed" text={result.error}/> :
        <><div className={`urgency ${result.urgency}`}>{result.urgency?.toUpperCase()}</div><p className="result-summary">{result.summary}</p>
        <div className="result-block"><span>Follow-up questions</span>{(result.next_questions||[]).map((q:string,i:number)=><div key={i} className="result-row"><ChevronRight size={14}/>{q}</div>)}</div>
        <div className="result-block"><span>Safety flags</span>{(result.safety_flags||[]).length ? result.safety_flags.map((q:string,i:number)=><div key={i} className="result-row"><ShieldCheck size={14}/>{q}</div>) : <div className="muted">No deterministic safety flags.</div>}</div>
        </>}
      </div>
    </div>
  </>;
}

function Appointments(){ return <><PageTitle kicker="SCHEDULE" title="Appointments" desc="Your upcoming consultations and care history."/><div className="two-col">
  <div className="glass-card list-card"><div className="list-head"><h3>Upcoming</h3><span className="confirmed">1 CONFIRMED</span></div><Appointment name="Dr. Meera Sharma" specialty="General Medicine" time="Today · 4:30 PM" type="Video consultation"/><Appointment name="Community Health Worker" specialty="Follow-up visit" time="18 Sep · 11:00 AM" type="Home visit"/></div>
  <div className="glass-card side-panel"><span className="section-kicker">CONSULTATION ROOM</span><h3>Ready when you are.</h3><p className="muted">Your next appointment is prepared. Review your health record or start a pre-consultation triage before joining.</p><button className="primary"><Video size={16}/> Enter waiting room</button></div>
  </div></>}

function HealthRecord(){ const reports=[["Blood report","Complete blood count","06 Sep 2026","Needs review"],["Discharge summary","General medicine","24 Aug 2026","Reviewed"],["Vitals","Blood pressure + pulse","20 Aug 2026","Reviewed"]]; return <><PageTitle kicker="PERSONAL HEALTH" title="Health record" desc="A chronological view of reports, vitals, consultations, and clinician notes."/><div className="record-toolbar"><div className="search"><Search size={15}/><input placeholder="Search your record"/></div><button className="secondary"><Upload size={15}/> Upload report</button></div><div className="glass-card table-card"><div className="table-head"><span>Document</span><span>Type</span><span>Date</span><span>Status</span></div>{reports.map((r,i)=><div className="table-row" key={i}><div className="doc"><div className="soft-icon"><FileText size={15}/></div><strong>{r[0]}</strong></div><span>{r[1]}</span><span>{r[2]}</span><span className={r[3]==="Needs review"?"review":"done"}>{r[3]}</span></div>)}</div></>}

function CareTeam(){ const [people,setPeople]=useState<any[]>([]); useEffect(()=>{getProviders().then(setPeople).catch(()=>{})},[]); return <><PageTitle kicker="CARE NETWORK" title="Care team" desc="Clinicians and community health workers connected to your care."/><div className="provider-grid">{(people.length?people:[{name:"Dr. Meera Sharma",specialty:"General Medicine",location:"Bengaluru"},{name:"Dr. Vikram Rao",specialty:"Family Medicine",location:"Tumakuru"},{name:"Community Health Team",specialty:"Field care",location:"Rural outreach"}]).map((p,i)=><div className="glass-card provider" key={i}><div className="provider-avatar">{p.name.split(" ").map((x:string)=>x[0]).slice(0,2).join("")}</div><span className="section-kicker">VERIFIED CARE PROVIDER</span><h3>{p.name}</h3><p>{p.specialty}</p><span className="provider-location"><MapPin size={13}/>{p.location}</span><button className="wide-secondary">View profile <ArrowRight size={15}/></button></div>)}</div></>}

function Referrals(){return <><PageTitle kicker="CARE COORDINATION" title="Referrals" desc="Track recommended facilities and the status of your care handoffs."/><div className="glass-card list-card"><div className="list-head"><h3>Active referrals</h3><span className="confirmed">2 OPEN</span></div><Referral facility="District Community Health Centre" specialty="General medicine" status="Awaiting appointment" distance="4.8 km"/><Referral facility="Primary Care Clinic" specialty="Diagnostics" status="Referral sent" distance="7.2 km"/></div></>}

function Impact(){return <><PageTitle kicker="SYSTEM INSIGHTS" title="Impact analytics" desc="A demo view of operational signals for a community-health program."/><div className="metric-grid"><Metric label="Patients supported" value="1,248" note="+18% this month" icon={<Users size={18}/>}/><Metric label="Clinician handoffs" value="326" note="92% completed" icon={<Stethoscope size={18}/>}/><Metric label="Urgent escalations" value="41" note="Safety engine triggered" icon={<ShieldCheck size={18}/>}/></div><div className="glass-card chart-card"><div className="card-head"><div><span className="section-kicker">CARE VOLUME</span><h3>12-week activity</h3></div><span className="muted">Synthetic demo data</span></div><div className="bars">{[42,56,48,70,63,78,72,88,75,91,86,96].map((v,i)=><div key={i} className="bar-col"><div className="bar" style={{height:`${v}%`}}/><span>W{i+1}</span></div>)}</div></div></>}

function PageTitle({kicker,title,desc}:{kicker:string;title:string;desc:string}){return <div className="page-title"><span className="section-kicker">{kicker}</span><h1>{title}</h1><p>{desc}</p></div>}
function EmptyState({title,text}:{title:string;text:string}){return <div className="empty"><div className="soft-icon"><Activity size={18}/></div><strong>{title}</strong><span>{text}</span></div>}
function Metric({label,value,note,icon}:{label:string;value:string;note:string;icon:React.ReactNode}){return <div className="metric glass-card"><div className="metric-icon">{icon}</div><div><span>{label}</span><strong>{value}</strong><small>{note}</small></div></div>}
function Appointment({name,specialty,time,type}:{name:string;specialty:string;time:string;type:string}){return <div className="appointment-list"><div className="doctor-avatar">{name.split(" ").map(x=>x[0]).slice(0,2).join("")}</div><div className="appointment-copy"><strong>{name}</strong><span>{specialty} · {type}</span><small>{time}</small></div><button className="icon-button"><ChevronRight size={16}/></button></div>}
function Referral({facility,specialty,status,distance}:{facility:string;specialty:string;status:string;distance:string}){return <div className="appointment-list"><div className="soft-icon"><MapPin size={16}/></div><div className="appointment-copy"><strong>{facility}</strong><span>{specialty} · {distance}</span><small>{status}</small></div><button className="icon-button"><ChevronRight size={16}/></button></div>}
