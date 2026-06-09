import streamlit as st
import re
import os
import json
import base64


st.set_page_config(page_title="gcsim translator", layout="wide", initial_sidebar_state="expanded")

# ──────────────────────────────────────────────
#  DATA LOADING & CONSTANTS
# ──────────────────────────────────────────────
def load_data(filename, backup):
    path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            lines = [l.strip().lower() for l in f.readlines() if l.strip()]
            if lines:
                return sorted(list(set(lines)))
    return sorted(list(set([b.lower() for b in backup])))

CHARS_BK  = ["skirk", "furina", "mona", "escoffier", "raiden", "sara", "xianyun"]
WEAPS_BK  = ["azurelight", "favsword", "ttds", "favlance", "engulfinglightning", "absolution"]
ARTS_BK   = ["finaleofthedeepgalleries", "totm", "no", "scroll", "emblem", "viridescentvenerer", "instructor", "none"]

CHAR_LIST    = load_data("characters.txt",  CHARS_BK)
WEAPON_LIST  = load_data("weapons.txt",     WEAPS_BK)
ARTIFACT_LIST= load_data("artifacts.txt",   ARTS_BK)

FOUR_STAR_SETS = {
    "instructor", "theexile", "scholar", "defenderswill", 
    "braveheart", "martialartist", "gambler", "resolutionofsojourner", "tinymiracle"
}

ACTIONS = {
    "e": "skill", "he": "skill[hold=1]", "te": "skill", "q": "burst",
    "c": "charge", "d": "dash", "j": "jump", "aim": "aim",
    "lp": "low_plunge", "hp": "high_plunge", "w": "walk"
}

DEFAULT_LOADOUTS = [
    {
        "char": "skirk", "weap": "azurelight", "ref": 1, "cons": 0,
        "set": "finaleofthedeepgalleries", "mains": ["hp", "atk", "atk%", "cryo%", "cr"],
        "rolls": {"def%": 2, "def": 2, "hp": 2, "hp%": 2, "atk": 2, "atk%": 6, "er": 2, "em": 2, "cr": 8, "cd": 12}
    },
    {
        "char": "furina", "weap": "favsword", "ref": 3, "cons": 0,
        "set": "totm", "mains": ["hp", "atk", "hp%", "hydro%", "cd"],
        "rolls": {"def%": 2, "def": 2, "hp": 2, "hp%": 2, "atk": 2, "atk%": 2, "er": 8, "em": 2, "cr": 12, "cd": 6}
    },
    {
        "char": "mona", "weap": "ttds", "ref": 5, "cons": 4,
        "set": "no", "mains": ["hp", "atk", "er", "atk%", "cr"],
        "rolls": {"def%": 2, "def": 2, "hp": 2, "hp%": 2, "atk": 2, "atk%": 2, "er": 9, "em": 2, "cr": 5, "cd": 12}
    },
    {
        "char": "escoffier", "weap": "favlance", "ref": 3, "cons": 0,
        "set": "scroll", "mains": ["hp", "atk", "er", "cryo%", "cd"],
        "rolls": {"def%": 2, "def": 2, "hp": 2, "hp%": 2, "atk": 2, "atk%": 12, "er": 2, "em": 2, "cr": 12, "cd": 2}
    }
]

# ──────────────────────────────────────────────
#  LOCAL FILE ASSET INTEGRATION & BASE64 ENCODING
# ──────────────────────────────────────────────
def get_image_base64(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                return f"data:image/png;base64,{b64}"
        except: pass
    return None

def get_local_asset_url(name, asset_type="characters"):
    clean_name = name.lower().replace(" ", "").replace("'", "")
    local_path = os.path.join(os.path.dirname(__file__), "assets", asset_type, f"{clean_name}.png")
    
    b64_img = get_image_base64(local_path)
    if b64_img:
        return b64_img
    
    # Elegant custom SVG placeholder if local file is missing
    return f"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%231a1e34' rx='12' stroke='%23ffafc1' stroke-width='1' stroke-opacity='0.2'/><path d='M50,25 L75,50 L50,75 L25,50 Z' fill='none' stroke='%23c8b4ff' stroke-width='2' stroke-opacity='0.4'/><circle cx='50' cy='50' r='3' fill='%23c8b4ff' fill-opacity='0.6'/></svg>"

def load_local_constellation(char_name, cons_level):
    clean_name = char_name.lower().replace(" ", "")
    json_path = os.path.join(os.path.dirname(__file__), "assets", "constellations.json")
    
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if clean_name in data and str(cons_level) in data[clean_name]:
                    return data[clean_name][str(cons_level)]
        except: pass
        
    if cons_level == 0:
        return {"name": "Unawakened", "description": "Character is at base constellation level with no extra passives."}
    return {"name": f"Constellation {cons_level}", "description": f"Custom skill profile data for C{cons_level} {char_name.title()}."}

# ──────────────────────────────────────────────
#  ROTATION TRANSLATOR
# ──────────────────────────────────────────────
def translate_rotation(rotation_text, char_list):
    active_team = {c['name'].lower() for c in char_list if c['name']}
    words = rotation_text.split()
    result, current_chain = [], []
    action_pattern = re.compile(r"^(n\d+)?([eqcdjawphlteh]+)$|^(n\d+)$")
    for word in words:
        clean = word.lower().strip(",;")
        if clean in active_team or not action_pattern.match(clean):
            if current_chain:
                result.append(f"{current_chain[0]} " + ", ".join(current_chain[1:]) + ";")
            current_chain = [clean]
        else:
            match = action_pattern.match(clean)
            if match:
                prefix, letters, just_n = match.groups()
                translated = []
                if just_n:
                    translated.append(f"attack:{just_n[1:]}")
                else:
                    if prefix:
                        translated.append(f"attack:{prefix[1:]}")
                    i = 0
                    while i < len(letters):
                        found = False
                        for length in [3, 2, 1]:
                            code = letters[i:i+length]
                            if code in ACTIONS:
                                translated.append(ACTIONS[code])
                                i += length
                                found = True
                                break
                        if not found:
                            i += 1
                current_chain.extend(translated)
    if current_chain:
        result.append(f"{current_chain[0]} " + ", ".join(current_chain[1:]) + ";")
    return "\n    ".join(result)

def generate_config(chars, active_char, rotation, iterations, target_lvl, num_rotations):
    translated_rotation = translate_rotation(rotation, chars)
    config = ""
    seen = set()
    for c in chars:
        name = c['name'].lower()
        if not name or name in seen: continue
        seen.add(name)
        config += f'{name} char lvl={c["lvl"]}/{c["lvl"]} cons={c["cons"]} talent=9,9,9;\n'
        config += f'{name} add weapon="{c["weap"]}" refine={c["ref"]} lvl=90/90;\n'
        config += f'{name} add set="{c["s1"]}" count={c["c1"]};\n'
        if str(c["c2"]).strip() != "0" and c["s2"] != "none":
            config += f'{name} add set="{c["s2"]}" count={c["c2"]};\n'
        
        active_mainstat_data = MAINSTAT_DATA_4STAR if c["s1"] in FOUR_STAR_SETS else MAINSTAT_DATA
        m_parts = [f"{s}={active_mainstat_data[s]}" for s in c["mains"] if s != "None"]
        if m_parts: config += f'{name} add stats {" ".join(m_parts)};\n'
            
        s_parts = [f"{s}={SUBSTAT_DATA[s]}*{r}" for s, r in c["rolls"].items() if r > 0]
        if s_parts: config += f'{name} add stats {" ".join(s_parts)};\n'
        config += "\n"
        
    config += (
        f"target lvl={target_lvl} resist=0.1 radius=2 pos=0,2.4 hp=999999999 freeze_resist=1;\n"
        f"options swap_delay=12 iteration={iterations};\n"
        f"energy every interval=480,720 amount=1;\n"
        f"\n// rotation\nactive {active_char.lower()};\n"
        f"for let i=0; i<{num_rotations}; i=i+1 {{\n    {translated_rotation}\n}}"
    )
    return config

# ──────────────────────────────────────────────
#  STAT DICTIONARIES
# ──────────────────────────────────────────────
MAINSTAT_DATA = {
    "None": 0, "hp": 4780, "atk": 311, "em": 187, "er": 0.518, "atk%": 0.466, "hp%": 0.466, 
    "def%": 0.583, "cr": 0.311, "cd": 0.622, "pyro%": 0.466, "hydro%": 0.466, "cryo%": 0.466, 
    "electro%": 0.466, "anemo%": 0.466, "geo%": 0.466, "dendro%": 0.466, "phys%": 0.583, "heal": 0.359
}
MAINSTAT_DATA_4STAR = {
    "None": 0, "hp": 3571, "atk": 232, "em": 139, "er": 0.348, "atk%": 0.348, "hp%": 0.348, 
    "def%": 0.435, "cr": 0.232, "cd": 0.464, "pyro%": 0.348, "hydro%": 0.348, "cryo%": 0.348, 
    "electro%": 0.348, "anemo%": 0.348, "geo%": 0.348, "dendro%": 0.348, "phys%": 0.435, "heal": 0.268
}
SUBSTAT_DATA = {
    "hp": 253.94, "hp%": 0.0496, "atk": 16.54, "atk%": 0.0496, "def": 19.68, 
    "def%": 0.062, "er": 0.0551, "em": 19.82, "cr": 0.0331, "cd": 0.0662
}

# ══════════════════════════════════════════════
#  PAGE CONFIG & GLOBAL CSS
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600&display=swap');
:root {
    --pink:      #ffafc1;
    --pink-dim:  #e08898;
    --gold:      #ffd770;
    --navy:      #0d0f1a;
    --navy2:     #13162a;
    --navy3:     #1a1e34;
    --card:      #181b2e;
    --border:    rgba(255,175,193,0.18);
    --text:      #d8d4e8;
    --text-dim:  #8880a0;
    --radius:    14px;
    --transition: 0.22s cubic-bezier(.4,0,.2,1);
}
html, body, .stApp { background: var(--navy) !important; cursor: default !important; }
body { font-family: 'DM Sans', sans-serif !important; }

/* Smooth Global View Transitions */
@keyframes titleGlow {
    0% { text-shadow: 0 0 30px rgba(255,175,193,0.4); }
    50% { text-shadow: 0 0 50px rgba(255,175,193,0.75), 0 0 20px rgba(200,180,255,0.4); }
    100% { text-shadow: 0 0 30px rgba(255,175,193,0.4); }
}

.site-header h1 {
    color: var(--pink) !important;
    animation: titleGlow 4s infinite ease-in-out;
    letter-spacing: 0.06em !important;
    margin: 0 !important;
}
.site-header { border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; }

/* Grid Layout Elements and Input Containers Modification */
div[data-baseweb="select"] > div, input {
    background: var(--navy3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    transition: all var(--transition) !important;
}
div[data-baseweb="select"] > div:hover, input:hover {
    border-color: var(--pink-dim) !important;
}

/* Restored Sidebar / Header Visibility */
#MainMenu, footer { visibility: hidden !important; }

section[data-testid="stSidebar"] {
    background-color: var(--navy2) !important;
    border-right: 1px solid var(--border) !important;
}

label[data-testid="stWidgetLabel"] p { 
    color: #c8b4ff !important; 
    text-shadow: 0 0 8px rgba(200, 180, 255, 0.25) !important;
    font-weight: 500 !important; 
    letter-spacing: 0.08em !important; 
    text-transform: uppercase !important; 
}
.stExpander details summary p {
    color: #c8b4ff !important;
    font-weight: 600 !important;
}

.stExpander { 
    background: var(--card) !important; 
    border: 1px solid var(--border) !important; 
    border-radius: var(--radius) !important; 
    margin-bottom: 8px !important;
    transition: transform 0.2s ease, border-color 0.2s ease !important;
}
.stExpander:hover {
    transform: translateX(2px);
    border-color: var(--pink-dim) !important;
}

/* Layout Image Alignments */
.inline-img { 
    width: 38px;
    height: 38px;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: #111424;
    object-fit: contain;
}

.cons-panel { 
    background: linear-gradient(135deg, #13162a 0%, #0f1120 100%); 
    border: 1px solid var(--border); 
    border-radius: var(--radius); 
    padding: 16px; 
    margin-top: 4px; 
    margin-bottom: 28px;
}
.cons-title { color: var(--gold); font-size: 0.92rem; font-weight: 600; }
.cons-desc { color: var(--text); font-size: 0.82rem; line-height: 1.6; margin-top: 4px; }
.cons-badge { display: inline-block; background: rgba(255,175,193,0.15); border: 1px solid rgba(255,175,193,0.3); border-radius: 20px; padding: 2px 12px; font-size: 0.72rem; color: var(--pink); font-weight: 600; margin-bottom: 8px; }

div[data-testid="stCodeBlock"] pre { height: 60vh !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; background: #0a0c16 !important; }
.stButton > button { background: linear-gradient(135deg, rgba(255,175,193,0.14) 0%, rgba(255,175,193,0.06) 100%) !important; border: 1px solid var(--pink) !important; border-radius: 8px !important; color: var(--pink) !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  INTRICATE GEOMETRIC STAR BACKGROUND OVERLAY
# ══════════════════════════════════════════════
st.markdown("""
<div aria-hidden="true" style="position:fixed; top:0; left:0; width:100vw; height:100vh; pointer-events:none; z-index:-1; overflow:hidden; opacity:0.65;">
  <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid slice">
    <defs>
      <radialGradient id="sg" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#ffafc1" stop-opacity="0.6"/>
        <stop offset="100%" stop-color="#ffafc1" stop-opacity="0"/>
      </radialGradient>
    </defs>
    
    <g fill="#ffafc1" fill-opacity="0.3">
      <path d="M 700,40 L 704,48 L 712,50 L 704,52 L 700,60 L 696,52 L 688,50 L 696,48 Z"/>
      <path d="M 200,80 L 202,84 L 206,85 L 202,86 L 200,90 L 198,86 L 194,85 L 198,84 Z"/>
      <path d="M 1200,90 L 1202,94 L 1206,95 L 1202,96 L 1200,100 L 1198,96 L 1194,95 L 1198,94 Z"/>
    </g>

    <g stroke="#ffafc1" stroke-opacity="0.15" stroke-width="0.8" fill="none">
      <line x1="60" y1="80" x2="140" y2="130"/><line x1="140" y1="130" x2="210" y2="90"/>
      <line x1="210" y1="90" x2="260" y2="155"/><line x1="60" y1="80" x2="95" y2="170"/>
      <line x1="95" y1="170" x2="140" y2="130"/><line x1="140" y1="130" x2="175" y2="200"/>
    </g>
    <g fill="#ffafc1" fill-opacity="0.5">
      <circle cx="60"  cy="80"  r="1.5"/><circle cx="140" cy="130" r="3.5"/>
      <circle cx="210" cy="90"  r="1.5"/><circle cx="260" cy="155" r="1.8"/>
    </g>
  </svg>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="site-header">
  <div>
    <div style="font-family:'DM Sans',sans-serif;font-size:0.68rem;color:#8880a0;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:4px;">✦ &nbsp;gcsim script translator</div>
    <h1 style="margin:0!important;padding:0!important">gcsim script translator by @dizzyy.x</h1>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("<h3 style='color:#ffafc1;'>Simulation Settings</h3>", unsafe_allow_html=True)
    
    active_char = st.text_input("Active Character", value="Skirk", help="First character on-field")
    iterations = st.number_input(
        "Iterations",
        min_value=100, 
        max_value=10000, 
        value=1000, 
        step=1,
        help="More iterations = higher accuracy, longer runtime. 1000 is a good default."
    )
    num_rotations = st.number_input("Rotations (i)", value=4, min_value=1)
    target_lvl = st.number_input("Target Level", value=100, min_value=1, max_value=100)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style="color:var(--pink);font-size:0.85rem;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;">Notation</div>
    <div style="font-size:0.76rem;color:#8880a0;line-height:1.8;">
      <span style="color:#ffafc1">n#</span> — normal attacks<br>
      <span style="color:#ffafc1">e</span> &nbsp;— skill<br>
      <span style="color:#ffafc1">he</span> — hold skill<br>
      <span style="color:#ffafc1">q</span> &nbsp;— burst<br>
      <span style="color:#ffafc1">c</span> &nbsp;— charge<br>
      <span style="color:#ffafc1">d</span> &nbsp;— dash<br>
    </div>
    """, unsafe_allow_html=True)

col_chars, col_code = st.columns([1.0, 1.2], gap="medium")
chars = []

def get_idx(lst, val): return lst.index(val.title()) if val.title() in lst else 0

with col_chars:
    st.markdown("<div style=\"color:var(--pink);font-size:0.85rem;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:8px;\">️ &nbsp;Rotation Sequence</div>", unsafe_allow_html=True)
    rot = st.text_area("Action List", value="skirk hEq n5d n2c n2d n2d n5d n5c", height=90, label_visibility="collapsed")
    st.markdown("<div style=\"color:var(--pink);font-size:0.85rem;letter-spacing:0.12em;text-transform:uppercase;margin:16px 0 8px 0;\">Team Builder</div>", unsafe_allow_html=True)

    tabs = st.tabs([" Slot 1", " Slot 2", "️ Slot 3", " Slot 4"])

    for i, tab in enumerate(tabs):
        with tab:
            d = DEFAULT_LOADOUTS[i] if i < len(DEFAULT_LOADOUTS) else DEFAULT_LOADOUTS[0]

            col_img_c, col_sel_c, col_img_w, col_sel_w = st.columns([0.15, 0.85, 0.15, 0.85])
            
            with col_sel_c: c_name = st.selectbox("Character", options=[n.title() for n in CHAR_LIST], index=get_idx([n.title() for n in CHAR_LIST], d["char"]), key=f"n{i}")
            with col_img_c: st.markdown(f'<div style="margin-top: 30px;"><img src="{get_local_asset_url(c_name, "characters")}" class="inline-img"></div>', unsafe_allow_html=True)
                
            with col_sel_w: c_weap = st.selectbox("Weapon", options=[w.title() for w in WEAPON_LIST], index=get_idx([w.title() for w in WEAPON_LIST], d["weap"]), key=f"w{i}")
            with col_img_w: st.markdown(f'<div style="margin-top: 30px;"><img src="{get_local_asset_url(c_weap, "weapons")}" class="inline-img"></div>', unsafe_allow_html=True)

            sl1, sl2, sl3 = st.columns(3)
            c_lvl  = sl1.number_input("Level", 1, 90, 90, key=f"l{i}")
            c_ref  = sl3.number_input("Refine", 1, 5, d["ref"], key=f"r{i}")
            with sl2: c_cons = st.number_input("Cons", 0, 6, d["cons"], key=f"con{i}")

            cd = load_local_constellation(c_name, c_cons)
            st.markdown(f"<div class='cons-panel'><div class='cons-title'>✦ {cd['name']}</div><div class='cons-desc'>{cd['description']}</div></div>", unsafe_allow_html=True)

            with st.expander(" Artifact Sets"):
                col_img_a1, col_sel_a1, col_count_a1 = st.columns([0.15, 0.65, 0.2])
                with col_sel_a1: c_s1 = st.selectbox("Primary Set", options=[a.title() for a in ARTIFACT_LIST], index=get_idx([a.title() for a in ARTIFACT_LIST], d["set"]), key=f"s1{i}")
                with col_img_a1: st.markdown(f'<div style="margin-top: 30px;"><img src="{get_local_asset_url(c_s1, "artifacts")}" class="inline-img"></div>', unsafe_allow_html=True)
                with col_count_a1: c_c1 = st.text_input("Count", value="4", key=f"c1{i}")
                
                if c_s1.lower().replace(" ", "") in FOUR_STAR_SETS:
                    st.markdown("""<div style='font-size:0.75rem; color:#ffafc1; padding-bottom:8px;'>✦ 4-star mainstats applied. Edit config for 5-star offpieces.</div>""", unsafe_allow_html=True)

                col_img_a2, col_sel_a2, col_count_a2 = st.columns([0.15, 0.65, 0.2])
                with col_sel_a2: c_s2 = st.selectbox("Secondary Set", options=[a.title() for a in ARTIFACT_LIST], index=len(ARTIFACT_LIST)-1, key=f"s2{i}")
                with col_img_a2: st.markdown(f'<div style="margin-top: 30px;"><img src="{get_local_asset_url(c_s2, "artifacts")}" class="inline-img"></div>', unsafe_allow_html=True)
                with col_count_a2: c_c2 = st.text_input("Count", value="0", key=f"c2{i}")

            with st.expander(" Mainstats"):
                slot_names = ["Flower", "Feather", "Sands", "Goblet", "Circlet"]
                m_cols = st.columns(5)
                c_mains = []
                main_options = list(MAINSTAT_DATA.keys())
                for idx in range(5):
                    def_main = d["mains"][idx]
                    m_idx = main_options.index(def_main) if def_main in main_options else 0
                    c_mains.append(m_cols[idx].selectbox(slot_names[idx], options=main_options, index=m_idx, key=f"ms{i}_{idx}"))

            with st.expander(" Substat Rolls"):
                sub_cols = st.columns(5)
                char_rolls = {}
                for idx, (stat, _) in enumerate(SUBSTAT_DATA.items()):
                    def_roll = d["rolls"].get(stat, 0)
                    char_rolls[stat] = sub_cols[idx % 5].number_input(stat, 0, 50, def_roll, key=f"{stat}{i}")

            chars.append({
                'name':  c_name.lower().replace(" ", ""), 'lvl': c_lvl, 'cons': c_cons,
                'weap':  c_weap.lower().replace(" ", ""), 'ref': c_ref,
                's1':    c_s1.lower().replace(" ", ""), 'c1': c_c1,
                's2':    c_s2.lower().replace(" ", ""), 'c2': c_c2,
                'mains': c_mains, 'rolls': char_rolls,
            })

with col_code:
    generated_code = generate_config(chars, active_char, rot, iterations, target_lvl, num_rotations)
    st.markdown("<div style=\"color:var(--pink);font-size:0.85rem;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:4px;\">Generated gcsim Config</div>", unsafe_allow_html=True)
    st.code(generated_code, language="go")

    if st.button(" Copy Config", use_container_width=True):
        st.toast("Config ready to paste into gcsim!")