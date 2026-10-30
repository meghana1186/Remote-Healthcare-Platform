from pathlib import Path
import json
import pandas as pd
import streamlit as st
from config.settings import APP_NAME, APP_VERSION
from ai.groq_client import GroqAI
from ai.triage import run_triage
from ai.safety import rules_cover
from components.ui import metric_card, section_title
from services.data_service import patients, providers, consultations, health_workers
from services.metrics import compute_metrics

st.set_page_config(page_title=APP_NAME,page_icon="🏥",layout="wide")
st.markdown(f"<style>{Path('assets/css/app.css').read_text()}</style>",unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🩺 RemoteCare AI")
    st.caption(f"v{APP_VERSION}")
    page=st.radio("Navigation",[
        "Dashboard","AI Triage","Emergency Mode","Doctor Console","Health Worker",
        "Patient Record","Report Analyzer","Health Copilot","Referrals & Providers",
        "Campaigns","Impact Analytics"])
    LANGUAGES={"English":"English","ಕನ್ನಡ":"Kannada","हिन्दी":"Hindi","தமிழ்":"Tamil","తెలుగు":"Telugu","मराठी":"Marathi"}
    language=LANGUAGES[st.selectbox("🌐 Language",list(LANGUAGES))]
    if st.toggle("📶 Low-bandwidth mode"):
        st.markdown('<div class="low-bandwidth">Low-bandwidth mode active</div>',unsafe_allow_html=True)

if page=="Dashboard":
    st.markdown('<div class="hero"><h1>Good evening 👋</h1><p>AI-assisted healthcare access for underserved communities.</p></div>',unsafe_allow_html=True)
    m=compute_metrics()
    cols=st.columns(4)
    for col,label,value,cap in zip(cols,
        ["Patients","Consultations","Avg wait","Villages"],
        [m["patients"],m["consultations"],f"{m['avg_wait_minutes']} min",m["villages"]],
        [f"{m['high_risk_patients']} high-risk",f"{m['consultations_waiting']} waiting now","across consultations",f"{m['health_workers']} health workers"]):
        with col: metric_card(label,value,cap)
    st.caption("Computed from the synthetic seed data in data/.")
    section_title("Care at a glance","Move from patient concern to appropriate human care.")
    a,b,c,d=st.columns(4)
    with a: st.markdown("### 🩺 AI Triage"); st.write("Safety-first symptom intake and next-step guidance.")
    with b: st.markdown("### 🚨 Emergency"); st.write("Fast emergency warning-sign workflow.")
    with c: st.markdown("### 👨‍⚕️ Clinician"); st.write("Structured handoff and provider connection.")
    with d: st.markdown("### 📄 Reports"); st.write("Patient-friendly report explanations.")

elif page=="AI Triage":
    section_title("AI Triage Copilot","AI assists with triage; clinicians remain responsible for care decisions.")
    if not rules_cover(language):
        st.warning(f"The emergency keyword rules cover English, Hindi and Kannada. For {language}, "
                   "emergencies are screened by the LLM check only, which needs a Groq API key.")
    with st.form("triage"):
        age=st.number_input("Age",0,120,37); sex=st.selectbox("Sex",["Female","Male","Other / prefer not to say"])
        symptoms=st.text_area("Describe what is happening",placeholder="Example: fever for 3 days, vomiting twice, reduced appetite")
        duration=st.text_input("Duration","3 days")
        go=st.form_submit_button("Run safety-first triage",type="primary")
    if go:
        r=run_triage({"age":age,"sex":sex,"symptoms":symptoms,"duration":duration},language)
        if r.get("screen_note"): st.warning(r["screen_note"])
        st.markdown(f"### Urgency: `{r.get('urgency','unknown').upper()}`")
        if r.get("emergency"): st.error(r.get("clinician_handoff",""))
        if r.get("risk_flags"): st.write("**Risk flags:**",", ".join(r["risk_flags"]))
        if not r.get("emergency"): st.info(r.get("clinician_handoff") or "Arrange professional assessment.")
        st.write("**Patient explanation**"); st.write(r.get("summary",""))
        if r.get("follow_up_questions"):
            st.write("**Questions for next step**")
            for q in r["follow_up_questions"]: st.write("•",q)
        if r.get("retrieved"):
            with st.expander(f"Knowledge used ({len(r.get('sources',[]))} cited of {len(r['retrieved'])} retrieved)"):
                for d in r["retrieved"]:
                    mark="✓" if d["topic"] in r.get("sources",[]) else "·"
                    st.write(f"{mark} {d['topic']} (score {d['score']}) — {d['source']}")
        elif r.get("retrieval_status","").startswith("unavailable"):
            st.caption(f"Knowledge retrieval {r['retrieval_status']}")
        st.caption(f"Emergency screen decided by: {r.get('safety_decided_by','none')}. Not a diagnosis or prescription.")

elif page=="Emergency Mode":
    section_title("🚨 Emergency Mode","If someone may be in immediate danger, seek emergency care now.")
    guidance={g["id"]:g for g in json.loads(Path("knowledge/emergency_guidance.json").read_text(encoding="utf-8"))}
    situations={"Difficulty breathing":"em-breathing","Chest pain":"em-chest-pain","Unconscious":"em-unconscious",
                "Severe bleeding":"em-bleeding","Seizure":"em-seizure","Stroke signs":"em-stroke","Poisoning":"em-poisoning",
                "Snake bite":"em-snakebite","Severe burn":"em-burns","Severe allergic reaction":"em-allergy"}
    options=st.multiselect("What is happening?",list(situations))
    if options:
        st.error("Potential emergency identified. Call 112, or 108 for an ambulance.")
        for item in options:
            g=guidance[situations[item]]
            st.markdown(f"**{item}**")
            for n,step in enumerate(g["steps"],1): st.write(f"{n}. {step}")
            st.caption(f"Source: {g['source']}")
    st.warning("Do not delay emergency care while using this application.")

elif page=="Doctor Console":
    section_title("Doctor Console","Prioritized queue with AI-prepared handoffs.")
    st.dataframe(consultations(),use_container_width=True,hide_index=True)
    selected=st.selectbox("Open patient",patients()["name"].tolist())
    row=patients()[patients()["name"]==selected].iloc[0].to_dict()
    st.markdown("### AI Clinical Brief"); st.write(GroqAI().summarize(row))
    st.success("Human clinician remains responsible for clinical decisions.")

elif page=="Health Worker":
    section_title("Community Health Worker","Prioritize home visits, high-risk patients and follow-ups.")
    hw=health_workers(); st.dataframe(hw,use_container_width=True,hide_index=True)
    for _,r in hw.iterrows(): st.markdown(f"**{r['name']}** · {r['village']} · {r['visits_today']} visits · 🔴 {r['high_risk']} high-risk")

elif page=="Patient Record":
    section_title("Patient Health Record","Synthetic demonstration data.")
    df=patients(); selected=st.selectbox("Patient",df["name"].tolist()); row=df[df["name"]==selected].iloc[0]
    st.json(row.to_dict()); st.markdown("### Care journey"); st.write("AI triage → clinician consultation → referral → follow-up")

elif page=="Report Analyzer":
    section_title("📄 Medical Report Analyzer","Upload a synthetic TXT report or paste text.")
    uploaded=st.file_uploader("Upload TXT report",type=["txt"]); text=""
    if uploaded: text=uploaded.read().decode("utf-8",errors="ignore")
    text=st.text_area("Report text",value=text,height=220)
    if st.button("Explain report",type="primary") and text: st.write(GroqAI().explain_report(text)); st.caption("Not a diagnosis.")

elif page=="Health Copilot":
    section_title("Health Copilot","General health education in the selected language.")
    q=st.text_area("Your question",placeholder="What are warning signs of dehydration?")
    if st.button("Ask RemoteCare AI",type="primary") and q: st.write(GroqAI().copilot(q,language)); st.caption("Educational information only.")

elif page=="Referrals & Providers":
    section_title("Providers & Referral Network")
    pr=providers(); available=pr[pr["status"]=="Available"]; st.dataframe(available,use_container_width=True,hide_index=True)
    patient=st.selectbox("Patient",patients()["name"].tolist())
    facility=st.selectbox("Facility",available["facility"].tolist()); urgency=st.selectbox("Care level",["Emergency","Urgent","Same-day","Routine"])
    if st.button("Create referral",type="primary"): st.success(f"Referral prepared: {patient} → {facility} ({urgency}).")

elif page=="Campaigns":
    section_title("Community Health Campaigns")
    st.dataframe(pd.DataFrame(json.loads(Path("data/campaigns.json").read_text())),use_container_width=True,hide_index=True)

elif page=="Impact Analytics":
    section_title("Impact Analytics","Computed from the synthetic seed data in data/.")
    m=compute_metrics()
    cols=st.columns(4)
    for col,label,value in zip(cols,["Patients","Consultations completed","Escalations","Home visits today"],
                               [m["patients"],f"{m['consultations_completed']} of {m['consultations']}",m["escalations"],m["home_visits_today"]]):
        with col: metric_card(label,value)
    st.write(f"Campaign households visited: {m['households_visited']:,} of {m['households_targeted']:,}")
    st.bar_chart(pd.DataFrame({"Condition":list(m["patients_by_condition"]),"Patients":list(m["patients_by_condition"].values())}).set_index("Condition"))

st.divider()
st.caption("RemoteCare AI is a hackathon prototype. Synthetic data only. AI outputs are not medical diagnoses or prescriptions.")
