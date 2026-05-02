import streamlit as st
import re
import os

#load files for character artifacts and weapon names :
def load_data(filename, backup):
    path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            lines = [l.strip().lower() for l in f.readlines() if l.strip()]
            if lines: return sorted(list(set(lines)))
    return sorted(list(set([b.lower() for b in backup])))

# default list here if incase files fail to load :
CHARS_BK = ["raiden", "skirk", "xianyun", "sara"]
WEAPS_BK = ["engulfinglightning", "absolution", "thecatch"]
ARTS_BK = ["emblem", "viridescentvenerer", "none"]

CHAR_LIST = load_data("characters.txt", CHARS_BK)
WEAPON_LIST = load_data("weapons.txt", WEAPS_BK)
ARTIFACT_LIST = load_data("artifacts.txt", ARTS_BK)

# actions dictionary :
ACTIONS = {
    "e": "skill", "he": "skill[hold=1]", "te": "skill", "q": "burst", 
    "c": "charge", "d": "dash", "j": "jump", "aim": "aim", 
    "lp": "low_plunge", "hp": "high_plunge", "w": "walk"
}

# notation to rotation translator :
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
                if just_n: translated.append(f"attack:{just_n[1:]}")
                else:
                    if prefix: translated.append(f"attack:{prefix[1:]}")
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
                        if not found: i += 1
                current_chain.extend(translated)
    if current_chain:
        result.append(f"{current_chain[0]} " + ", ".join(current_chain[1:]) + ";")
    return "\n    ".join(result)

# artifact stats data :
MAINSTAT_DATA = {"None": 0, "hp": 4780, "atk": 311, "em": 187, "er": 0.518, "atk%": 0.466, "hp%": 0.466, "def%": 0.583, "cr": 0.311, "cd": 0.622, "pyro%": 0.466, "hydro%": 0.466, "cryo%": 0.466, "electro%": 0.466, "anemo%": 0.466, "geo%": 0.466, "dendro%": 0.466, "phys%": 0.583, "heal": 0.359}
SUBSTAT_DATA = {"hp": 253.94, "hp%": 0.0496, "atk": 16.54, "atk%": 0.0496, "def": 19.68, "def%": 0.062, "er": 0.0551, "em": 19.82, "cr": 0.0331, "cd": 0.0662}

# config :
def generate_config(chars, active_char, rotation, iterations, target_lvl):
    translated_rotation = translate_rotation(rotation, chars)
    config = ""
    seen = set()
    for c in chars:
        name = c['name'].lower()
        if not name or name in seen: continue
        seen.add(name)
        config += f'{name} lvl={c["lvl"]}/{c["lvl"]} cons={c["cons"]} talent=9,9,9;\n'
        config += f'{name} add weapon="{c["weap"]}" lvl=90/90 refine={c["ref"]};\n'
        config += f'{name} add set="{c["s1"]}" count={c["c1"]};\n'
        if str(c["c2"]).strip() != "0" and c["s2"] != "none":
            config += f'{name} add set="{c["s2"]}" count={c["c2"]};\n'
        m_parts = [f"{s}={MAINSTAT_DATA[s]}" for s in c["mains"] if s != "None"]
        if m_parts: config += f'{name} add stats {" ".join(m_parts)};\n'
        s_parts = [f"{s}={SUBSTAT_DATA[s]}*{r}" for s, r in c["rolls"].items() if r > 0] 
        if s_parts: config += f'{name} add stats {" ".join(s_parts)};\n'
        config += "\n"
    config += f"active {active_char.lower()};\ntarget lvl={target_lvl} resist=0.1 radius=2 pos=0,2.4 hp=999999999;\n"
    config += f"options iteration={iterations} swap_delay=12;\nenergy every interval=480,720 amount=1;\n"
    config += f"\n# rotation\nfor let i=0; i<4; i=i+1{{\n    {translated_rotation}\n}}"
    return config

st.set_page_config(page_title="s2c", layout="wide")
# css :
st.markdown ("""
<style>
.header-anchor {
    display: none !important;
    }

h1 {
    color: #ffafc1 !important;
    text-shadow: 0 0 35px rgba(255, 175, 193, 0.8) !important;
    margin-top: -40px !important; /* Moves title up */
    padding-bottom: 10px !important;
}

div[data-testid="stCodeBlock"] pre {
        height: 65vh !important; 
        overflow-y: auto !important;
        border: 1px solid #ffafc1 !important;
}

button[data-baseweb="tab"] p { 
    font-size: 16px !important; 
    font-weight: bold !important; 
    color: #ffafc1 !important; 
} 

label[data-testid="stWidgetLabel"] p { 
    color: #bbaaa9 !important; 
    font-weight: bold !important; 
} 

.stColumn{
    color: #ffafc1 !important;
}

.stExpander { 
    border: 1px solid #ffafc1 !important; 
    border-radius: 16px !important; 
    background-color: #1a1c24 !important; 
} 

.stExpander details summary p { 
    color: #ffafc1 !important; 
    font-weight: bold !important;
}
</style> 
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Global Settings")
    active_char = st.text_input("Active Character", value="Raiden")
    iterations = st.number_input("Iterations", 100, 10000, 1000)
    target_lvl = st.number_input("Target Level", 1, 100, 100)

st.title("**GCSIM code translator by dizzy**")
col1, col2 = st.columns([0.8, 1.4])

chars = []
with col1:
    tabs = st.tabs([f"Character {i}" for i in range(1, 5)])
    st.header("Rotation")
    rot = st.text_area("Action List", value="skirk hEq n5d n2c n2d n2d n5d n5c", height=200)
    for i, tab in enumerate(tabs):
        with tab:
            c1, c2 = st.columns(2)
            c_name = c1.selectbox("Character Name", options=[n.title() for n in CHAR_LIST], index=i if i < len(CHAR_LIST) else 0, key=f"n{i}")
            c_weap = c2.selectbox("Weapon", options=[w.title() for w in WEAPON_LIST], key=f"w{i}")
            sl1, sl2, sl3 = st.columns(3)
            c_lvl = sl1.number_input("Lvl", 1, 90, 90, key=f"l{i}")
            c_cons = sl2.number_input("Cons", 0, 6, 0, key=f"con{i}")
            c_ref = sl3.number_input("Refine", 1, 5, 1, key=f"r{i}")
            
            with st.expander("**artifacts**"):
                st.write("**Artifact Sets**")
                sc1, sc2 = st.columns(2)
                c_s1 = sc1.selectbox("Set 1", options=[a.title() for a in ARTIFACT_LIST], index=0, key=f"s1{i}")
                c_c1 = sc2.text_input("Count 1", value="4", key=f"c1{i}")
                st.write("")
                sc3, sc4 = st.columns(2)
                c_s2 = sc3.selectbox("Set 2", options=[a.title() for a in ARTIFACT_LIST], index=len(ARTIFACT_LIST)-1, key=f"s2{i}")
                c_c2 = sc4.text_input("Count 2", value="0", key=f"c2{i}")

            with st.expander("**mainstat editor**"):
                st.write("**Mainstats**")
                m_cols = st.columns(5)
                c_mains, defs = [], ["hp", "atk", "er", "electro%", "cr"]
                for idx in range(5):
                    m_choice = m_cols[idx].selectbox(f"Slot {idx+1}", options=list(MAINSTAT_DATA.keys()), index=list(MAINSTAT_DATA.keys()).index(defs[idx]), key=f"ms{i}_{idx}")
                    c_mains.append(m_choice)

            with st.expander("**substat editor**"):
                st.write("**Substat Rolls**")
                sub_cols, char_rolls = st.columns(5), {}
                for idx, (stat, _) in enumerate(SUBSTAT_DATA.items()):
                    char_rolls[stat] = sub_cols[idx % 5].number_input(f"{stat}", 0, 50, 2, key=f"{stat}{i}")
            
            chars.append({'name': c_name.lower().replace(" ", ""), 'lvl': c_lvl, 'cons': c_cons, 'weap': c_weap.lower().replace(" ", ""), 'ref': c_ref, 's1': c_s1.lower().replace(" ", ""), 'c1': c_c1, 's2': c_s2.lower().replace(" ", ""), 'c2': c_c2, 'mains': c_mains, 'rolls': char_rolls})

generated_code = generate_config(chars, active_char, rot, iterations, target_lvl)
with col2:
    st.header("generated code")
    st.code(generated_code, language="go")
    if st.button("copy"): st.toast("ready for CLI")