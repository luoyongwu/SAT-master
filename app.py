import streamlit as st
import pandas as pd
import random
import json
import os
import google.generativeai as genai
import time

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

for key in ['authenticated', 'is_active_section', 'target_words', 'target_domains', 'current_q_idx', 'current_q_data', 'answered']:
    if key not in st.session_state:
        if key in ['target_words', 'target_domains']: st.session_state[key] = []
        elif key == 'current_q_idx': st.session_state[key] = 0
        elif key == 'current_q_data': st.session_state[key] = None
        else: st.session_state[key] = False

st.set_page_config(page_title="SAT Vocab Master", page_icon="ð", layout="centered")

st.markdown("""
<style>
.stRadio > div { padding-top: 10px; }
.css-1v0mbdj { margin-top: -20px; } 
</style>
""", unsafe_allow_html=True)

if not st.session_state.authenticated:
    st.title("ð SAT è¯æ±ç»æè®­ç»è¥")
    st.markdown("### Powered by 1500+ Elite SAT Vocab")
    
    init_db()
    db = load_db(DB_FILE)
    free_spots_left = max(0, 100 - db["free_users"])
    
    if free_spots_left > 0:
        st.info(f"ð å°é²ç¦å©ï¼å 100 åç¨æ·åææç ï¼(å©ä½åé¢: {free_spots_left})")
    else:
        st.warning("â ï¸ åè´¹åé¢å·²æ»¡ãè¯·åç®¡çåç´¢è¦ 6 ä½ææç ã")
    
    st.markdown("---")
    
    api_key = st.text_input("ð è¯·è¾å¥æ¨ç Google API Key (å¿å¡«):", type="password")
    auth_code = st.text_input("ð« è¯·è¾å¥ 6 ä½ææç  (å100åç´æ¥çç©º):", type="password")
    
    st.markdown("---")
    
    if st.button("ð è¿å¥ç³»ç» (Access System)", type="primary", use_container_width=True):
        if not api_key:
            st.error("API Key ä¸è½ä¸ºç©ºï¼")
        else:
            passed = False
            if free_spots_left > 0 and not auth_code:
                db["free_users"] += 1
                save_db(db, DB_FILE)
                passed = True
                st.success("åå¯éªè¯éè¿ï¼æ­£å¨è¿å¥ç³»ç»...")
            elif auth_code in VALID_CODES:
                passed = True
                st.success("ææç éªè¯æåï¼æ­£å¨è¿å¥ç³»ç»...")
            elif free_spots_left <= 0 and not auth_code:
                st.error("â åè´¹åé¢å·²æ»¡ï¼å¿é¡»è¾å¥ææçææç ã")
            else:
                st.error("â ææç æ æã")
                
            if passed:
                st.session_state.api_key = api_key
                st.session_state.authenticated = True
                time.sleep(1)
                st.rerun()

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
        st.error("â Invalid API Key or Quota Exceeded.")
        if st.button("â¬ï¸ Logout & Retry"):
            st.session_state.authenticated = False
            st.rerun()
        st.stop()
        
    st.sidebar.title("âï¸ Settings / è®¾ç½®")
    
    ui_lang = st.sidebar.radio("ð Language / çé¢è¯­è¨", ["English", "ä¸­æ/English"])
    def t(en, zh):
        return zh if ui_lang == "ä¸­æ/English" else en

    flash_idx = 0
    for i, m in enumerate(available_models):
        if "flash" in m.lower():
            flash_idx = i
            break
            
    selected_model = st.sidebar.selectbox("AI Model (Flash is faster)", available_models, index=flash_idx)
    model = genai.GenerativeModel(selected_model.replace("models/", ""))
    
    st.sidebar.markdown("---")
    selected_mode = st.sidebar.selectbox(t("ð¯ Section Mode", "ð¯ åºé¢æ¨¡å¼"), [
        "Standard (Mixed 8-8-4)", 
        "All Core (Medium)", 
        "All Advanced (Hard)", 
        "All Sprint (Extreme)"
    ], disabled=st.session_state.is_active_section)
    
    core_list, adv_list, sprint_list = load_vocab()

    if not st.session_state.is_active_section:
        st.title(t("ð SAT Vocab Master Class", "ð SAT è¯æ±ç»æè®­ç»è¥"))
        st.info(t("ð¡ TIP for Mobile Users: Tap the `>` arrow in the top-left corner to open sidebar!", "ð¡ ææºç¨æ·æç¤ºï¼ç¹å»å·¦ä¸è§ç `>` ç®­å¤´å¯æå¼ä¾§è¾¹æ è®¾ç½®è¯­è¨åæ¨¡å¼ï¼"))
        st.markdown(f"**{t('Current Mode:', 'å½åæ¨¡å¼ï¼')}** `{selected_mode}`")
        
        start_btn = t("ð Start 20-Question Section", "ð å¼å§ 20 é¢æµè¯")
        if st.button(start_btn, type="primary", use_container_width=True):
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
        st.sidebar.write(f"**{t('Question', 'å½åè¿åº¦')} {current_idx + 1} / {total_target}**")
        if st.sidebar.button(t("â¹ï¸ End Section Early", "â¹ï¸ æåç»ææµè¯")):
            st.session_state.is_active_section = False
            st.rerun()

        if st.session_state.current_q_data is None:
            target_w = st.session_state.target_words[current_idx]
            target_d = st.session_state.target_domains[current_idx]
            
            loading_msg = f"ð§  Generating Question {current_idx + 1}..." if ui_lang == "English" else f"ð§  æ­£å¨æéçæç¬¬ {current_idx + 1} é¢ï¼è¯·ç¨å..."
            with st.spinner(loading_msg):
                
                lang_instruction = "Write the 'analysis' entirely in concise English." if ui_lang == "English" else "Write the 'analysis' ENTIRELY IN CHINESE (ä¸­æè§£æ), explaining the target word's meaning and why the correct option fits contextually."
                
                prompt = f"""
                You are an expert SAT test creator. Create ONE high-difficulty SAT Reading 'Words in Context' question.
                Target word: '{target_w}'. Domain: '{target_d}'.
                {lang_instruction}
                CRITICAL: Output ONLY a valid JSON. DO NOT use markdown blocks.
                {{
                  "word": "{target_w}",
                  "domain": "{target_d}",
                  "passage": "<Academic English passage. Put '_____' where the word belongs.>",
                  "options": ["<Option 1>", "<Option 2>", "<Option 3>", "<Option 4>"],
                  "correct_index": <integer 0-3>,
                  "analysis": "<Your analysis based on language instruction>"
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
                    st.error(t(f"Generation failed. Error: {e}", f"çæå¤±è´¥ï¼ç½ç»å¯è½æ³¢å¨ãéè¯¯: {e}"))
                    if st.button(t("ð Retry Generation", "ð éæ°çææ­¤é¢")):
                        st.rerun()
                    st.stop()
        
        q_data = st.session_state.current_q_data
        
        if "Standard" in selected_mode:
            if current_idx < 8: difficulty_badge = "ð¢ Core"
            elif current_idx < 16: difficulty_badge = "ð¡ Advanced"
            else: difficulty_badge = "ð´ Sprint"
        else:
            difficulty_badge = f"ðµ {selected_mode.split()[0]} {selected_mode.split()[1]}"

        st.caption(f"**{t('Difficulty:', 'é¾åº¦:')}** {difficulty_badge} | ð·ï¸ **{t('Domain:', 'é¢å:')}** {q_data.get('domain', 'Academic')}")
        st.markdown(f"**{t('Passage:', 'éè¯»éæ®µ (Passage):')}**\n\n{q_data.get('passage', '')}")
        
        options = q_data.get('options', ['A', 'B', 'C', 'D'])
        choices = options + [t("N (Skip / Unsure)", "N (è·³è¿ / ä¸ç¡®å®)")]
        
        user_choice = st.radio(t("Select your answer:", "è¯·éæ©æä½³å¡«ç©ºè¯ï¼"), choices, index=None, disabled=st.session_state.answered)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if not st.session_state.answered:
                if st.button(t("â Submit Answer", "â æäº¤ç­æ¡"), type="primary"):
                    if user_choice:
                        st.session_state.answered = True
                        st.rerun()
                    else:
                        st.warning(t("Please select an option first!", "è¯·åéæ©ä¸ä¸ªéé¡¹ï¼"))
        with col2:
            if st.button(t("â ï¸ Flag Question", "â ï¸ æ è®°æ¥é (å­å¥éé¢æ¬)")):
                reviews = load_db(REVIEW_DB)
                q_data["flagged_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                reviews.append(q_data)
                save_db(reviews, REVIEW_DB)
                st.toast(t("Flagged and saved for review!", "å·²æåè®°å½è³éé¢æ¬ï¼ç­å¾æå¸å¤æ ¸ï¼"), icon="â")

        if st.session_state.answered:
            st.divider()
            correct_ans = options[int(q_data.get('correct_index', 0))]
            if user_choice == correct_ans:
                st.success(t(f"ð¯ Correct! (Answer: {correct_ans})", f"ð¯ åç­æ­£ç¡®ï¼ (æ åç­æ¡: {correct_ans})"))
            elif user_choice and user_choice.startswith("N"):
                st.warning(t(f"â© You skipped. (Answer: {correct_ans})", f"â© æ¨è·³è¿äºæ­¤é¢ã (æ åç­æ¡: {correct_ans})"))
            else:
                st.error(t(f"â Incorrect. (Answer: {correct_ans})", f"â åç­éè¯¯ã (æ åç­æ¡: {correct_ans})"))
                
            st.info(f"**ð§  {t('Analysis:', 'æ·±åº¦è§£æ:')}**\n\n{q_data.get('analysis', '')}")
            
            if st.button(t("â¡ï¸ Next Question", "â¡ï¸ ä¸ä¸é¢ (æéçæ)"), type="primary", use_container_width=True):
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
                    st.success(t("ð Excellent! Section completed!", "ð å¤ªæ£äºï¼æ¨å·²æåå®ææ¬ååçææè®­ç»ï¼"))
                    time.sleep(3)
                    st.rerun()
