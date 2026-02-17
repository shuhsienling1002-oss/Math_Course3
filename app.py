import streamlit as st
import random
import uuid
from dataclasses import dataclass, field
from typing import List, Dict

# ==========================================
# 0. 全局設定 (Global Config)
# ==========================================
MAX_LEVEL = 5

# ==========================================
# 1. 核心配置與 CSS (High Contrast Fix)
# ==========================================
st.set_page_config(
    page_title="整數大對決：歸零之戰 v2.1",
    page_icon="⚔️",
    layout="centered"
)

st.markdown("""
<style>
    /* [FIX] 全局背景改為更深的午夜藍，文字改為高亮白 */
    .stApp { background-color: #020617; color: #f8fafc; }
    
    /* 頂部進度條 */
    .stProgress > div > div > div > div {
        background-color: #60a5fa;
    }
    
    /* [FIX] 說明文字 (Caption) 強制增亮 */
    .stCaption { color: #94a3b8 !important; font-size: 1rem !important; }

    /* 戰場容器 (Visualizer) */
    .battlefield-box {
        background: #0f172a; /* 更深的背景 */
        border: 2px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 0 15px rgba(0,0,0,0.8); /* 增加陰影對比 */
        text-align: center;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* 粒子樣式 - 增加光暈邊框使其在深色背景更明顯 */
    .particle {
        display: inline-block;
        width: 24px; /* 稍微加大 */
        height: 24px;
        border-radius: 50%;
        margin: 3px;
        box-shadow: 0 0 8px rgba(255,255,255,0.2);
        transition: all 0.3s ease;
    }
    .p-pos { background: #3b82f6; border: 2px solid #93c5fd; } /* 亮藍配淺藍邊 */
    .p-neg { background: #ef4444; border: 2px solid #fca5a5; } /* 亮紅配淺紅邊 */
    .p-zero { background: #475569; border: 1px dashed #94a3b8; opacity: 0.5; }

    /* 卡牌按鈕 - 字體加粗增亮 */
    div.stButton > button {
        border-radius: 10px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 1.3rem !important;
        font-weight: 900 !important; /* 特粗體 */
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }
    div.stButton > button:active { transform: scale(0.96); }
    
    /* 狀態提示框 - 增加背景不透明度以提升文字可讀性 */
    .status-box {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 15px;
        color: #ffffff; /* 強制白字 */
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }
    .status-neutral { background: #1e293b; border: 1px solid #60a5fa; color: #60a5fa; }
    .status-warn { background: #422006; border: 1px solid #eab308; color: #facc15; }
    .status-error { background: #450a0a; border: 1px solid #f87171; color: #fca5a5; }
    .status-success { background: #052e16; border: 1px solid #4ade80; color: #4ade80; }

    /* [FIX] 數學公式顯示 - 黑底亮字，對比度最大化 */
    .math-display {
        font-size: 1.8rem;
        font-family: monospace;
        color: #ffffff; /* 純白 */
        background: #000000; /* 純黑背景 */
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #334155;
        border-left: 6px solid #a855f7;
        margin-top: 10px;
    }
    
    /* 數據標籤優化 */
    .label-text {
        color: #cbd5e1; /* 亮灰 */
        font-size: 1rem;
        margin-bottom: 5px;
        font-weight: bold;
    }
    .value-text {
        font-size: 2.5rem;
        font-weight: 900;
        text-shadow: 0 0 10px rgba(0,0,0,0.5);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 領域模型 (Domain Model)
# ==========================================

@dataclass
class IntegerCard:
    value: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def display_text(self) -> str:
        """按鈕顯示文字 - 增加 Emoji 辨識度"""
        if self.value > 0:
            return f"🔵 +{self.value}"
        else:
            return f"🔴 {self.value}" # 負數自帶負號

# ==========================================
# 3. 戰鬥引擎 (Logic Layer)
# ==========================================

class BattleEngine:
    
    @staticmethod
    def generate_level(level: int) -> dict:
        config = {
            1: {'target': 5, 'range': [1, 2, 3], 'allow_neg': False, 'title': "Level 1: 能量填充 (正數加法)"},
            2: {'target': -5, 'range': [-1, -2, -3], 'allow_neg': True, 'force_neg': True, 'title': "Level 2: 深淵潛航 (負數累加)"},
            3: {'target': 0, 'range': [-3, -2, -1, 1, 2, 3], 'allow_neg': True, 'title': "Level 3: 物質湮滅 (歸零練習)"},
            4: {'target': 3, 'range': [-4, -2, 2, 5], 'allow_neg': True, 'title': "Level 4: 混沌平衡 (混合運算)"},
            5: {'target': -8, 'range': [-5, -3, 2, 4, -9], 'allow_neg': True, 'title': "Level 5: 虛空領主 (高階運算)"}
        }
        cfg = config.get(level, config[5])
        
        target = cfg['target']
        hand = []
        
        # 確保至少有一組解
        steps = 3 + (level // 2)
        correct_path = []
        val = 0
        
        for _ in range(steps):
            if cfg.get('force_neg'):
                card_val = random.choice([x for x in cfg['range'] if x < 0])
            elif not cfg['allow_neg']:
                card_val = random.choice([x for x in cfg['range'] if x > 0])
            else:
                card_val = random.choice(cfg['range'])
                
            correct_path.append(IntegerCard(card_val))
            val += card_val
            
        if level != 3:
            target = val
        else:
            if val != 0:
                correct_path.append(IntegerCard(-val))

        distractors = [IntegerCard(random.choice(cfg['range'])) for _ in range(2)]
        hand = correct_path + distractors
        random.shuffle(hand)
        
        return {"target": target, "hand": hand, "title": cfg['title']}

    @staticmethod
    def calculate_current(history: List[IntegerCard]) -> int:
        return sum(card.value for card in history)

    @staticmethod
    def generate_particle_html(current: int, target: int) -> str:
        """[Visual Engine] 生成高對比度粒子"""
        html = '<div style="line-height: 30px;">'
        
        net_val = current
        abs_val = abs(net_val)
        particles = ""
        display_limit = 18
        
        if abs_val == 0:
            particles = '<span style="color:#94a3b8; font-weight:bold; font-size:1.2rem;">∅ (歸零/無電荷)</span>'
        else:
            p_class = "p-pos" if net_val > 0 else "p-neg"
            count = min(abs_val, display_limit)
            
            for _ in range(count):
                particles += f'<div class="particle {p_class}"></div>'
            
            if abs_val > display_limit:
                particles += f' <span style="color:#ffffff; font-weight:bold;">...(+{abs_val - display_limit})</span>'

        html += f'<div>{particles}</div>'
        html += '</div>'
        return html

    @staticmethod
    def generate_equation_latex(history: List[IntegerCard]) -> str:
        if not history: return "0"
        eq_str = "0"
        for card in history:
            val = card.value
            if val >= 0:
                eq_str += f" + {val}"
            else:
                eq_str += f" - {abs(val)}"
        return eq_str

# ==========================================
# 4. 狀態管理
# ==========================================

class GameState:
    def __init__(self):
        if 'level' not in st.session_state:
            self.init_game()
    
    def init_game(self):
        st.session_state.update({
            'level': 1,
            'history': [],
            'game_status': 'playing',
            'msg': '戰鬥開始！請部署粒子達到目標電荷。',
            'msg_type': 'neutral'
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
            st.session_state.msg = "↺ 時光倒流：已撤回上一次部署"
            st.session_state.msg_type = 'neutral'

    def retry(self):
        self.start_level(st.session_state.level)

    def _check_status(self):
        current = BattleEngine.calculate_current(st.session_state.history)
        target = st.session_state.target
        
        if current == target:
            st.session_state.game_status = 'won'
            st.session_state.msg = "✨ 完美！目標達成！"
            st.session_state.msg_type = 'success'
        elif not st.session_state.hand:
            st.session_state.game_status = 'lost'
            st.session_state.msg = "💀 能量耗盡，任務失敗。"
            st.session_state.msg_type = 'error'
        else:
            diff = target - current
            if diff > 0:
                st.session_state.msg = f"📉 能量不足：還差 +{diff} (需要藍色)"
                st.session_state.msg_type = 'neutral' # 改為中性色避免過度焦慮
            elif diff < 0:
                st.session_state.msg = f"📈 能量過載：超過 +{abs(diff)} (需要紅色抵銷)"
                st.session_state.msg_type = 'warn'
            else:
                st.session_state.msg = "運算中..."

    def next_level(self):
        if st.session_state.level >= MAX_LEVEL:
            st.session_state.game_status = 'completed'
        else:
            self.start_level(st.session_state.level + 1)
            
    def restart_game(self):
        self.init_game()

# ==========================================
# 5. UI 呈現層 (View Layer)
# ==========================================

def main():
    game = GameState()
    
    # --- Top Bar ---
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("⚔️ 整數大對決")
    with c2:
        if st.button("🔄 重置"):
            game.restart_game()
            st.rerun()

    progress = st.session_state.level / MAX_LEVEL
    st.progress(progress)
    st.caption(f"進度: {st.session_state.level} / {MAX_LEVEL}")

    # --- Game Completed ---
    if st.session_state.game_status == 'completed':
        st.balloons()
        st.markdown("""
        <div style="background:#0f172a; border:2px solid #fbbf24; padding:30px; border-radius:15px; text-align:center; color:white;">
            <h1 style="color:#fbbf24;">🏆 傳奇誕生！</h1>
            <p style="font-size:1.2rem;">你已完全掌握正負數抵銷的法則。</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎓 開啟新一輪試煉", use_container_width=True):
            game.restart_game()
            st.rerun()
        return

    # --- Dashboard (High Contrast) ---
    target = st.session_state.target
    current = BattleEngine.calculate_current(st.session_state.history)
    
    col_tgt, col_mid, col_cur = st.columns([1, 0.2, 1])
    
    with col_tgt:
        # [FIX] 顏色改為高亮螢光色
        t_color = "#60a5fa" if target > 0 else "#f87171" # 亮藍 vs 亮紅
        if target == 0: t_color = "#a3e635" # 萊姆綠
        t_sign = "+" if target > 0 else ""
        
        st.markdown(f"<div class='label-text' style='text-align:center;'>目標電荷</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='value-text' style='text-align:center; color:{t_color}'>{t_sign}{target}</div>", unsafe_allow_html=True)
        
    with col_mid:
        status_icon = "⚡"
        if current == target: status_icon = "✅"
        elif st.session_state.game_status == 'lost': status_icon = "💀"
        st.markdown(f"<div style='text-align:center; font-size:2rem; padding-top:20px; color:#ffffff;'>{status_icon}</div>", unsafe_allow_html=True)
        
    with col_cur:
        c_color = "#ffffff" # 預設白
        if current == target: c_color = "#4ade80" # 成功綠
        elif current > target: c_color = "#facc15" # 警告黃
        
        c_sign = "+" if current > 0 else ""
        st.markdown(f"<div class='label-text' style='text-align:center;'>當前電荷</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='value-text' style='text-align:center; color:{c_color}'>{c_sign}{current}</div>", unsafe_allow_html=True)

    # --- Status Message ---
    msg_cls = f"status-{st.session_state.msg_type}"
    st.markdown(f'<div class="status-box {msg_cls}">{st.session_state.msg}</div>', unsafe_allow_html=True)

    # --- Battlefield (Visualizer) ---
    st.markdown("**⚛️ 粒子反應爐：**")
    particle_html = BattleEngine.generate_particle_html(current, target)
    st.markdown(f'<div class="battlefield-box">{particle_html}</div>', unsafe_allow_html=True)
    
    # [FIX] 數學公式黑底白字
    latex_eq = BattleEngine.generate_equation_latex(st.session_state.history)
    st.markdown(f'<div class="math-display">{latex_eq} = {current}</div>', unsafe_allow_html=True)

    # --- Control Area ---
    if st.session_state.game_status == 'playing':
        st.write("👇 部署粒子：")
        hand = st.session_state.hand
        
        if hand:
            cols = st.columns(4)
            for i, card in enumerate(hand):
                with cols[i % 4]:
                    # 使用 type="primary" 來凸顯按鈕，Streamlit 會自動調整為主題色
                    # 但因為我們改了 CSS，這裡主要是為了結構
                    btn_type = "primary" if card.value > 0 else "secondary"
                    if st.button(card.display_text, key=f"card_{card.id}", type=btn_type, use_container_width=True):
                        game.play_card(i)
                        st.rerun()
        
        if st.session_state.history:
            st.markdown("---")
            if st.button("↩️ 撤回 (Undo)"):
                game.undo()
                st.rerun()

    # --- Result Actions ---
    elif st.session_state.game_status == 'won':
        if st.button("🚀 前往下一戰場", type="primary", use_container_width=True):
            game.next_level()
            st.rerun()
            
    elif st.session_state.game_status == 'lost':
        if st.button("💥 重啟反應爐 (Retry)", type="primary", use_container_width=True):
            game.retry()
            st.rerun()

if __name__ == "__main__":
    main()
