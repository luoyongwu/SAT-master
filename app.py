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
