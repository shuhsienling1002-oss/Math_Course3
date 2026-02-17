import streamlit as st
import random
import uuid
from dataclasses import dataclass, field
from typing import List, Dict

# ==========================================
# 0. 全局設定
# ==========================================
MAX_LEVEL = 10

# ==========================================
# 1. 核心配置與 CSS (Fix: Button Contrast)
# ==========================================
st.set_page_config(
    page_title="整數大對決 v3.1",
    page_icon="⚔️",
    layout="centered"
)

st.markdown("""
<style>
    /* 全局背景 */
    .stApp { background-color: #020617; color: #f8fafc; }
    
    /* 進度條 */
    .stProgress > div > div > div > div { background-color: #60a5fa; }
    .stCaption { color: #94a3b8 !important; }

    /* 戰場容器 */
    .battlefield-box {
        background: #0f172a;
        border: 2px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 0 15px rgba(0,0,0,0.8);
        text-align: center;
        min-height: 120px;
    }

    /* 粒子樣式 */
    .particle {
        display: inline-block;
        width: 22px; height: 22px;
        border-radius: 50%; margin: 2px;
        box-shadow: 0 0 5px rgba(255,255,255,0.3);
    }
    .p-pos { background: #3b82f6; border: 2px solid #93c5fd; } /* 藍 */
    .p-neg { background: #ef4444; border: 2px solid #fca5a5; } /* 紅 */
    
    /* [CRITICAL FIX] 按鈕樣式強制覆蓋 */
    /* 基礎按鈕設定 */
    div.stButton > button {
        border-radius: 10px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 1.3rem !important;
        font-weight: 900 !important;
        border: 2px solid rgba(255,255,255,0.2) !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        height: auto !important;
        padding: 10px 5px !important;
        transition: all 0.2s !important;
    }

    /* 正數按鈕 (Primary): 藍底白字 */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(145deg, #2563eb, #1d4ed8) !important;
        color: #ffffff !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #3b82f6 !important;
        transform: translateY(-2px);
    }

    /* 負數按鈕 (Secondary): 紅底白字 (修復了白底問題) */
    div.stButton > button[kind="secondary"] {
        background: linear-gradient(145deg, #dc2626, #b91c1c) !important;
        color: #ffffff !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background: #ef4444 !important;
        transform: translateY(-2px);
    }
    
    div.stButton > button:active { transform: scale(0.95); }

    /* 狀態提示框 */
    .status-box {
        padding: 15px; border-radius: 10px;
        text-align: center; font-weight: bold; font-size: 1.1rem;
        margin-bottom: 15px; color: #ffffff;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }
    .status-neutral { background: #1e293b; border: 1px solid #60a5fa; color: #60a5fa; }
    .status-warn { background: #422006; border: 1px solid #eab308; color: #facc15; }
    .status-error { background: #450a0a; border: 1px solid #f87171; color: #fca5a5; }
    .status-success { background: #052e16; border: 1px solid #4ade80; color: #4ade80; }

    /* 數學顯示 */
    .math-display {
        font-size: 1.6rem; font-family: monospace;
        color: #ffffff; background: #000000;
        padding: 12px; border-radius: 8px;
        border: 1px solid #334155; border-left: 6px solid #a855f7;
        margin-top: 10px;
    }
    
    .label-text { color: #cbd5e1; font-size: 0.9rem; font-weight: bold; }
    .value-text { font-size: 2.2rem; font-weight: 900; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 領域模型
# ==========================================

@dataclass
class IntegerCard:
    value: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def display_text(self) -> str:
        if self.value > 0:
            return f"+{self.value}" # 藍色按鈕不需Emoji，顏色已區分
        else:
            return f"{self.value}" # 負數自帶負號

# ==========================================
# 3. 戰鬥引擎
# ==========================================

class BattleEngine:
    @staticmethod
    def generate_level(level: int) -> dict:
        config = {
            1: {'range': [1, 2, 3], 'type': 'pos_only', 'steps': 2, 'title': "L1: 能量填充 (正數)"},
            2: {'range': [-1, -2, -3], 'type': 'neg_only', 'steps': 2, 'title': "L2: 深淵潛航 (負數)"},
            3: {'range': [-1, 1], 'type': 'zero', 'steps': 2, 'title': "L3: 物質湮滅 (歸零)"},
            4: {'range': [-2, -1, 1, 2, 3], 'type': 'mixed_pos', 'steps': 3, 'title': "L4: 混沌平衡 I (偏正)"},
            5: {'range': [-3, -2, -1, 1, 2], 'type': 'mixed_neg', 'steps': 3, 'title': "L5: 混沌平衡 II (偏負)"},
            6: {'range': [2, 3, 4, 5], 'type': 'pos_mid', 'steps': 3, 'title': "L6: 能量過載 (進階)"},
            7: {'range': [-5, -3, 3, 5], 'type': 'zero_mid', 'steps': 4, 'title': "L7: 虛空迴路 (歸零)"},
            8: {'range': [-4, -2, 3, 6], 'type': 'mixed_step3', 'steps': 3, 'title': "L8: 三重奏 (策略)"},
            9: {'range': [-8, -5, 4, 7, 9], 'type': 'chaos', 'steps': 4, 'title': "L9: 亂流風暴 (大數)"},
            10: {'range': [-10, -7, -3, 5, 8, 12], 'type': 'boss', 'steps': 5, 'title': "L10: 虛空領主"}
        }
        cfg = config.get(level, config[10])
        
        correct_path = []
        current_sum = 0
        
        # 生成邏輯
        for _ in range(cfg['steps']):
            pool = cfg['range']
            if cfg['type'] == 'pos_only': pool = [x for x in pool if x > 0]
            elif cfg['type'] == 'neg_only': pool = [x for x in pool if x < 0]
            
            val = random.choice(pool)
            correct_path.append(IntegerCard(val))
            current_sum += val
            
        target = current_sum
        if 'zero' in cfg['type']:
            if current_sum != 0:
                fix_card = IntegerCard(-current_sum)
                correct_path.append(fix_card)
                target = 0
        
        distractor_count = 2
        if level >= 6: distractor_count = 3
        if level >= 9: distractor_count = 4
        
        distractors = [IntegerCard(random.choice(cfg['range'])) for _ in range(distractor_count)]
        hand = correct_path + distractors
        random.shuffle(hand)
        
        return {"target": target, "hand": hand, "title": cfg['title']}

    @staticmethod
    def calculate_current(history: List[IntegerCard]) -> int:
        return sum(card.value for card in history)

    @staticmethod
    def generate_particle_html(current: int, target: int) -> str:
        html = '<div style="line-height: 28px;">'
        net_val = current
        abs_val = abs(net_val)
        particles = ""
        display_limit = 20
        
        if abs_val == 0:
            particles = '<span style="color:#94a3b8; font-weight:bold; font-size:1.2rem;">∅ (歸零/無電荷)</span>'
        else:
            p_class = "p-pos" if net_val > 0 else "p-neg"
            count = min(abs_val, display_limit)
            for _ in range(count):
                particles += f'<div class="particle {p_class}"></div>'
            if abs_val > display_limit:
                particles += f' <span style="color:#ffffff;">...(+{abs_val - display_limit})</span>'
        html += f'<div>{particles}</div></div>'
        return html

    @staticmethod
    def generate_equation_latex(history: List[IntegerCard]) -> str:
        if not history: return "0"
        eq_str = "0"
        for card in history:
            if card.value >= 0: eq_str += f" + {card.value}"
            else: eq_str += f" - {abs(card.value)}"
        return eq_str

# ==========================================
# 4. 狀態管理
# ==========================================

class GameState:
    def __init__(self):
        if 'level' not in st.session_state: self.init_game()
    
    def init_game(self):
        st.session_state.update({
            'level': 1, 'history': [], 'game_status': 'playing',
            'msg': '戰鬥開始！請部署粒子。', 'msg_type': 'neutral'
        })
        self.start_level(1)

    def start_level(self, level):
        st.session_state.level = level
        data = BattleEngine.generate_level(level)
        st.session_state.target = data['target']
        st.session_state.hand = data['hand']
        st.session_state.level_title = data['title']
        st.session_state.history = []
        st.session_state.game_status = 'playing'
        st.session_state.msg = f"⚔️ {data['title']}"
        st.session_state.msg_type = 'neutral'

    def play_card(self, card_idx):
        hand = st.session_state.hand
        if 0 <= card_idx < len(hand):
            card = hand.pop(card_idx)
            st.session_state.history.append(card)
            self._check_status()

    def undo(self):
        if st.session_state.history:
            card = st.session_state.history.pop()
            st.session_state.hand.append(card)
            st.session_state.game_status = 'playing'
            st.session_state.msg = "↺ 撤回部署"

    def retry(self):
        self.start_level(st.session_state.level)

    def _check_status(self):
        current = BattleEngine.calculate_current(st.session_state.history)
        target = st.session_state.target
        if current == target:
            st.session_state.game_status = 'won'
            st.session_state.msg = "✨ 目標達成！"
            st.session_state.msg_type = 'success'
        elif not st.session_state.hand:
            st.session_state.game_status = 'lost'
            st.session_state.msg = "💀 能量耗盡"
            st.session_state.msg_type = 'error'
        else:
            diff = target - current
            if diff > 0:
                st.session_state.msg = f"📉 不足 +{diff} (需藍色)"
                st.session_state.msg_type = 'neutral'
            elif diff < 0:
                st.session_state.msg = f"📈 超過 +{abs(diff)} (需紅色)"
                st.session_state.msg_type = 'warn'
            else:
                st.session_state.msg = "運算中..."

    def next_level(self):
        if st.session_state.level >= MAX_LEVEL:
            st.session_state.game_status = 'completed'
        else: self.start_level(st.session_state.level + 1)
    
    def restart_game(self): self.init_game()

# ==========================================
# 5. UI 呈現
# ==========================================

def main():
    game = GameState()
    
    c1, c2 = st.columns([3, 1])
    with c1: st.title("⚔️ 整數大對決")
    with c2:
        if st.button("🔄 重置"): game.restart_game(); st.rerun()

    progress = st.session_state.level / MAX_LEVEL
    st.progress(progress)
    st.caption(f"Lv {st.session_state.level} / {MAX_LEVEL}")

    if st.session_state.game_status == 'completed':
        st.balloons()
        st.success("🏆 全數通關！傳奇誕生！")
        if st.button("🎓 再玩一次", use_container_width=True): game.restart_game(); st.rerun()
        return

    # Dashboard
    target = st.session_state.target
    current = BattleEngine.calculate_current(st.session_state.history)
    
    col_tgt, col_mid, col_cur = st.columns([1, 0.2, 1])
    with col_tgt:
        t_color = "#60a5fa" if target > 0 else "#f87171"
        if target == 0: t_color = "#a3e635"
        st.markdown(f"<div class='label-text' style='text-align:center;'>目標電荷</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='value-text' style='text-align:center; color:{t_color}'>{target:+d}</div>", unsafe_allow_html=True)
        
    with col_mid:
        icon = "✅" if current == target else "⚡"
        if st.session_state.game_status == 'lost': icon = "💀"
        st.markdown(f"<div style='text-align:center; font-size:2rem; padding-top:20px;'>{icon}</div>", unsafe_allow_html=True)
        
    with col_cur:
        c_color = "#ffffff"
        if current == target: c_color = "#4ade80"
        elif current > target: c_color = "#facc15"
        st.markdown(f"<div class='label-text' style='text-align:center;'>當前電荷</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='value-text' style='text-align:center; color:{c_color}'>{current:+d}</div>", unsafe_allow_html=True)

    # Status & Visuals
    msg_cls = f"status-{st.session_state.msg_type}"
    st.markdown(f'<div class="status-box {msg_cls}">{st.session_state.msg}</div>', unsafe_allow_html=True)

    st.markdown("**⚛️ 粒子反應爐：**")
    particle_html = BattleEngine.generate_particle_html(current, target)
    st.markdown(f'<div class="battlefield-box">{particle_html}</div>', unsafe_allow_html=True)
    
    latex_eq = BattleEngine.generate_equation_latex(st.session_state.history)
    st.markdown(f'<div class="math-display">{latex_eq} = {current}</div>', unsafe_allow_html=True)

    # Controls
    if st.session_state.game_status == 'playing':
        st.write("👇 部署粒子：")
        hand = st.session_state.hand
        if hand:
            cols = st.columns(4)
            for i, card in enumerate(hand):
                with cols[i % 4]:
                    # [Core Fix] 明確指定 type
                    btn_type = "primary" if card.value > 0 else "secondary"
                    if st.button(card.display_text, key=f"card_{card.id}", type=btn_type, use_container_width=True):
                        game.play_card(i)
                        st.rerun()
        if st.session_state.history:
            st.markdown("---")
            if st.button("↩️ 撤回"): game.undo(); st.rerun()

    elif st.session_state.game_status == 'won':
        if st.button("🚀 下一戰場", type="primary", use_container_width=True): game.next_level(); st.rerun()
    elif st.session_state.game_status == 'lost':
        if st.button("💥 重試", type="primary", use_container_width=True): game.retry(); st.rerun()

if __name__ == "__main__":
    main()
