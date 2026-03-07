import streamlit as st
import pandas as pd
import random
import json
import os
import google.generativeai as genai
import time
==========================================
1. Database & Auth System
==========================================
DB_FILE = "sat_auth_db.json"
REVIEW_DB = "flagged_questions.json"
VALID_CODES = ["888888", "666666", "123456", "sat1500"]
def init_db():
if not os.path.exists(DB_FILE):
with open(DB_FILE, 'w') as f: json.dump({"free_users": 0}, f)
if not os.path.exists(REVIEW_DB):
with open(REVIEW_DB, 'w') as f: json.dump([], f)
def load_db(file):
with open(file, 'r') as f: return json.load(f)
def save_db(data, file):
with open(file, 'w') as f: json.dump(data, f)
==========================================
2. Vocabulary Loader
==========================================
@st.cache_data
def load_vocab():
try:
core = pd.read_excel("Core.xlsx")['Word'].dropna().tolist()
adv = pd.read_excel("Advanced.xlsx")['Word'].dropna().tolist()
sprint = pd.read_excel("Sprint.xlsx")['Word'].dropna().tolist()
if not core: core = ["Ubiquitous"]
if not adv: adv = core
if not sprint: sprint = adv
return core, adv, sprint
except Exception as e:
st.error("Error: Excel files not found! Please check GitHub repo.")
return ["CoreWord"], ["AdvWord"], ["SprintWord"]
DOMAINS = ["Cutting-edge Technology", "Deep Historical Document", "Complex Political Commentary", "Hard Science / Biology"]
Initialize Session State
for key in ['authenticated', 'is_active_section', 'target_words', 'target_domains', 'current_q_idx', 'current_q_data', 'answered']:
if key not in st.session_state:
if key in ['target_words', 'target_domains']: st.session_state[key] = []
elif key == 'current_q_idx': st.session_state[key] = 0
elif key == 'current_q_data': st.session_state[key] = None
else: st.session_state[key] = False
st.set_page_config(page_title="SAT Vocab Master", page_icon="🎓", layout="centered")
UI Styling
st.markdown("""
<style>
.stRadio > div { padding-top: 10px; }
.css-1v0mbdj { margin-top: -20px; }
</style>
""", unsafe_allow_html=True)
==========================================
3. Login Panel
==========================================
if not st.session_state.authenticated:
st.title("🎓 SAT 词汇终极训练营")
st.markdown("### Powered by 1500+ Elite SAT Vocab")
init_db()
db = load_db(DB_FILE)
free_spots_left = max(0, 100 - db["free_users"])

if free_spots_left > 0:
    st.info(f"🎉 尝鲜福利：前 100 名用户免授权码！(剩余名额: {free_spots_left})")
else:
    st.warning("⚠️ 免费名额已满。请向管理员索要 6 位授权码。")

st.markdown("---")

api_key = st.text_input("🔑 请输入您的 Google API Key (必填):", type="password")
auth_code = st.text_input("🎫 请输入 6 位授权码 (前100名直接留空):", type="password")

st.markdown("---")

if st.button("🚀 进入系统 (Access System)", type="primary", use_container_width=True):
    if not api_key:
        st.error("API Key 不能为空！")
    else:
        passed = False
        if free_spots_left > 0 and not auth_code:
            db["free_users"] += 1
            save_db(db, DB_FILE)
            passed = True
            st.success("免密验证通过！正在进入系统...")
        elif auth_code in VALID_CODES:
            passed = True
            st.success("授权码验证成功！正在进入系统...")
        elif free_spots_left <= 0 and not auth_code:
            st.error("❌ 免费名额已满，必须输入有效的授权码。")
        else:
            st.error("❌ 授权码无效。")
            
        if passed:
            st.session_state.api_key = api_key
            st.session_state.authenticated = True
            time.sleep(1)
            st.rerun()
==========================================
4. Core Engine
==========================================
else:
genai.configure(api_key=st.session_state.api_key)
  @st.cache_data(ttl=300)
def get_models():
    try:
        return [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except Exception:
        return []
        
available_models = get_models()
if not available_models:
    st.error("❌ Invalid API Key or Quota Exceeded.")
    if st.button("⬅️ Logout & Retry"):
        st.session_state.authenticated = False
        st.rerun()
    st.stop()
    
st.sidebar.title("⚙️ Settings & Progress")
selected_model = st.sidebar.selectbox("AI Model", available_models)
model = genai.GenerativeModel(selected_model.replace("models/", ""))

st.sidebar.markdown("---")
selected_mode = st.sidebar.selectbox("🎯 Section Mode", [
    "Standard (Mixed 8-8-4)", 
    "All Core (Medium)", 
    "All Advanced (Hard)", 
    "All Sprint (Extreme)"
], disabled=st.session_state.is_active_section)

core_list, adv_list, sprint_list = load_vocab()

if not st.session_state.is_active_section:
    st.title("🎓 SAT Vocab Master Class")
    st.info("💡 **TIP for Mobile Users:** Tap the `>` arrow in the top-left corner to open sidebar!")
    st.markdown(f"**Current Mode:** `{selected_mode}`")
    
    if st.button("🚀 Start 20-Question Section", type="primary", use_container_width=True):
        if "Standard" in selected_mode:
            words = random.sample(core_list, min(8, len(core_list))) + \
                    random.sample(adv_list, min(8, len(adv_list))) + \
                    random.sample(sprint_list, min(4, len(sprint_list)))
        elif "Core" in selected_mode:
            words = random.sample(core_list, min(20, len(core_list)))
        elif "Advanced" in selected_mode:
            words = random.sample(adv_list, min(20, len(adv_list)))
        else:
            words = random.sample(sprint_list, min(20, len(sprint_list)))
            
        domains = DOMAINS * 5
        random.shuffle(domains)
        
        st.session_state.target_words = words
        st.session_state.target_domains = domains
        st.session_state.current_q_idx = 0
        st.session_state.current_q_data = None
        st.session_state.is_active_section = True
        st.rerun()

else:
    current_idx = st.session_state.current_q_idx
    total_target = 20
    
    st.sidebar.progress((current_idx) / total_target)
    st.sidebar.write(f"**Question {current_idx + 1} of {total_target}**")
    if st.sidebar.button("⏹️ End Section Early"):
        st.session_state.is_active_section = False
        st.rerun()

    if st.session_state.current_q_data is None:
        target_w = st.session_state.target_words[current_idx]
        target_d = st.session_state.target_domains[current_idx]
        
        with st.spinner(f"🧠 Generating Question {current_idx + 1}..."):
            prompt = f"""
            You are an expert SAT test creator. Create ONE high-difficulty SAT Reading 'Words in Context' question.
            Target word: '{target_w}'. Domain: '{target_d}'.
            CRITICAL: Output ONLY a valid JSON. DO NOT use markdown code blocks like ```json.
            Format:
            {{
              "word": "{target_w}",
              "domain": "{target_d}",
              "passage": "<Highly academic English passage. Put '_____' where the word belongs.>",
              "options": ["<Option 1>", "<Option 2>", "<Option 3>", "<Option 4>"],
              "correct_index": <integer 0, 1, 2, or 3>,
              "analysis": "<Concise English analysis>"
            }}
            """
            try:
                response = model.generate_content(prompt)
                clean_text = response.text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                
                q_data = json.loads(clean_text.strip())
                st.session_state.current_q_data = q_data
                st.rerun()
            except Exception as e:
                st.error(f"Generation failed. Error: {e}")
                if st.button("🔄 Retry Generation"):
                    st.rerun()
                st.stop()
    
    q_data = st.session_state.current_q_data
    
    if "Standard" in selected_mode:
        if current_idx < 8: difficulty_badge = "🟢 Core"
        elif current_idx < 16: difficulty_badge = "🟡 Advanced"
        else: difficulty_badge = "🔴 Sprint"
    else:
        difficulty_badge = f"🔵 {selected_mode.split()[0]} {selected_mode.split()[1]}"

    st.caption(f"**Difficulty:** {difficulty_badge} | 🏷️ **Domain:** {q_data.get('domain', 'Academic')}")
    st.markdown(f"**Passage:**\n{q_data.get('passage', '')}")
    
    options = q_data.get('options', ['A', 'B', 'C', 'D'])
    choices = options + ["N (Skip / Unsure)"]
    
    user_choice = st.radio("Select your answer:", choices, index=None, disabled=st.session_state.answered)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if not st.session_state.answered:
            if st.button("✅ Submit Answer", type="primary"):
                if user_choice:
                    st.session_state.answered = True
                    st.rerun()
                else:
                    st.warning("Please select an option first!")
    with col2:
        if st.button("⚠️ Flag Question"):
            st.toast("Flagged for manual review!", icon="✅")

    if st.session_state.answered:
        st.divider()
        correct_ans = options[int(q_data.get('correct_index', 0))]
        if user_choice == correct_ans:
            st.success(f"🎯 Correct! (Answer: {correct_ans})")
        elif user_choice and user_choice.startswith("N"):
            st.warning(f"⏩ You skipped this question. (Answer: {correct_ans})")
        else:
            st.error(f"❌ Incorrect. (Answer: {correct_ans})")
            
        st.info(f"**🧠 Analysis:** {q_data.get('analysis', '')}")
        
        if st.button("➡️ Next Question", type="primary", use_container_width=True):
            if current_idx + 1 < total_target:
                st.session_state.current_q_idx += 1
                st.session_state.answered = False
                st.session_state.current_q_data = None 
                st.rerun()
            else:
                st.session_state.is_active_section = False
                st.session_state.answered = False
                st.session_state.current_q_data = None
                st.balloons()
                st.success("🎉 Excellent! You have completed the 20-question section!")
                time.sleep(3)
                st.rerun()
