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
# 1. 核心配置與 CSS
# ==========================================
st.set_page_config(
    page_title="整數大對決：歸零之戰",
    page_icon="⚔️",
    layout="centered"
)

st.markdown("""
<style>
    /* 全局深色戰鬥風格 */
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    
    /* 頂部進度條 */
    .stProgress > div > div > div > div {
        background-color: #7aa2f7;
    }

    /* 戰場容器 (Visualizer) */
    .battlefield-box {
        background: #24283b;
        border: 2px solid #414868;
        border-radius: 12px;
        padding: 15px;
        margin: 15px 0;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.6);
        text-align: center;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* 粒子樣式 */
    .particle {
        display: inline-block;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        margin: 2px;
        box-shadow: 0 0 5px rgba(255,255,255,0.3);
        transition: all 0.3s ease;
    }
    .p-pos { background: #7aa2f7; border: 1px solid #3d59a1; } /* 藍色正數 */
    .p-neg { background: #f7768e; border: 1px solid #db4b4b; } /* 紅色負數 */
    .p-zero { background: #565f89; border: 1px dashed #a9b1d6; opacity: 0.3; } /* 抵銷後的灰燼 */

    /* 卡牌按鈕 - 區分正負 */
    div.stButton > button {
        border-radius: 8px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        border: none !important;
        transition: transform 0.1s !important;
        color: white !important;
    }
    div.stButton > button:active { transform: scale(0.95); }
    
    /* 正數卡樣式 (透過 Python 邏輯無法直接注入 class 到 button，需依賴文字內容辨識或統一風格) 
       這裡我們使用統一風格，但依賴 emoji 區分
    */
    
    /* 狀態提示框 */
    .status-box {
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .status-neutral { background: rgba(122, 162, 247, 0.1); border: 1px solid #7aa2f7; color: #7aa2f7; }
    .status-warn { background: rgba(224, 175, 104, 0.1); border: 1px solid #e0af68; color: #e0af68; }
    .status-error { background: rgba(247, 118, 142, 0.1); border: 1px solid #f7768e; color: #f7768e; }
    .status-success { background: rgba(158, 206, 106, 0.1); border: 1px solid #9ece6a; color: #9ece6a; }

    /* 數學公式顯示 */
    .math-display {
        font-size: 1.5rem;
        font-family: monospace;
        color: #c0caf5;
        background: #16161e;
        padding: 10px;
        border-radius: 6px;
        border-left: 4px solid #bb9af7;
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
    def is_positive(self) -> bool:
        return self.value > 0

    @property
    def display_text(self) -> str:
        """按鈕顯示文字"""
        if self.value > 0:
            return f"🔵 +{self.value}"
        else:
            return f"🔴 {self.value}"

# ==========================================
# 3. 戰鬥引擎 (Logic Layer)
# ==========================================

class BattleEngine:
    
    @staticmethod
    def generate_level(level: int) -> dict:
        """
        難度曲線設計：
        L1: 純加法 (正數堆疊)
        L2: 純減法 (負數堆疊)
        L3: 歸零訓練 (正負抵銷) - 引入 Zero Pair 概念
        L4: 目標控制 (混合運算)
        L5: 精確打擊 (有限步數/大數字)
        """
        config = {
            1: {'target': 5, 'range': [1, 2, 3], 'allow_neg': False, 'title': "能量填充 (正數加法)"},
            2: {'target': -5, 'range': [-1, -2, -3], 'allow_neg': True, 'force_neg': True, 'title': "深淵潛航 (負數累加)"},
            3: {'target': 0, 'range': [-3, -2, -1, 1, 2, 3], 'allow_neg': True, 'title': "物質湮滅 (歸零練習)"},
            4: {'target': 3, 'range': [-4, -2, 2, 5], 'allow_neg': True, 'title': "混沌平衡 (混合運算)"},
            5: {'target': -8, 'range': [-5, -3, 2, 4, -9], 'allow_neg': True, 'title': "虛空領主 (高階運算)"}
        }
        cfg = config.get(level, config[5])
        
        target = cfg['target']
        hand = []
        
        # 確保至少有一組解 (簡單的隨機生成與校驗)
        current_val = 0
        steps = 3 + (level // 2)
        
        # 逆向生成路徑
        correct_path = []
        val = 0
        for _ in range(steps):
            # L2 強制只給負數
            if cfg.get('force_neg'):
                card_val = random.choice([x for x in cfg['range'] if x < 0])
            elif not cfg['allow_neg']:
                card_val = random.choice([x for x in cfg['range'] if x > 0])
            else:
                card_val = random.choice(cfg['range'])
                
            correct_path.append(IntegerCard(card_val))
            val += card_val
            
        # 設定目標為路徑總和 (除了 L3 固定為 0)
        if level != 3:
            target = val
        else:
            # L3 特殊處理：確保總和為 0
            # 如果隨機生成的不是 0，補一張卡讓它歸零
            if val != 0:
                correct_path.append(IntegerCard(-val))

        # 加入干擾項
        distractors = [IntegerCard(random.choice(cfg['range'])) for _ in range(2)]
        hand = correct_path + distractors
        random.shuffle(hand)
        
        return {"target": target, "hand": hand, "title": cfg['title']}

    @staticmethod
    def calculate_current(history: List[IntegerCard]) -> int:
        return sum(card.value for card in history)

    @staticmethod
    def generate_particle_html(current: int, target: int) -> str:
        """
        [Visual Engine] 生成粒子視覺化 HTML
        核心機制：顯示正負抵銷的過程
        """
        html = '<div style="line-height: 24px;">'
        
        # 1. 決定顯示的粒子數量
        # 我們不顯示歷史過程，只顯示「當前狀態」的物理本質
        # 但為了教學，我們可以顯示 "Net Value" (淨值)
        
        net_val = current
        abs_val = abs(net_val)
        
        particles = ""
        
        # 為了視覺效果，限制最大顯示數量，避免崩版
        display_limit = 20
        
        if abs_val == 0:
            particles = '<span style="color:#565f89; font-weight:bold;">∅ (歸零/無電荷)</span>'
        else:
            p_class = "p-pos" if net_val > 0 else "p-neg"
            count = min(abs_val, display_limit)
            
            for _ in range(count):
                particles += f'<div class="particle {p_class}"></div>'
            
            if abs_val > display_limit:
                particles += f' <span style="color:#a9b1d6">...(+{abs_val - display_limit})</span>'

        html += f'<div>{particles}</div>'
        
        # 顯示數值標籤
        color = "#7aa2f7" if net_val > 0 else "#f7768e"
        if net_val == 0: color = "#9ece6a"
        
        sign = "+" if net_val > 0 else ""
        html += f'<div style="margin-top:10px; font-size:1.5rem; font-weight:bold; color:{color};">{sign}{net_val}</div>'
        
        html += '</div>'
        return html

    @staticmethod
    def generate_equation_latex(history: List[IntegerCard]) -> str:
        if not history: return "0"
        
        # 生成： 0 + (+5) + (-3) = 2
        eq_str = "0"
        for card in history:
            val = card.value
            if val >= 0:
                eq_str += f" + {val}"
            else:
                eq_str += f" - {abs(val)}" # 顯示為 - 3 而不是 + (-3) 讓閱讀更直覺，或可選 + (-3)
                
        return eq_str

# ==========================================
# 4. 狀態管理 (State Management)
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
        st.session_state.msg = f"第 {level} 關：{data['title']}"
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
            st.session_state.msg = "時光倒流：撤回上一次部署"
            st.session_state.msg_type = 'neutral'

    def retry(self):
        self.start_level(st.session_state.level)

    def _check_status(self):
        current = BattleEngine.calculate_current(st.session_state.history)
        target = st.session_state.target
        
        if current == target:
            st.session_state.game_status = 'won'
            st.session_state.msg = "✨ 目標達成！電荷平衡！"
            st.session_state.msg_type = 'success'
        elif not st.session_state.hand:
            st.session_state.game_status = 'lost'
            st.session_state.msg = "🌑 能量耗盡，任務失敗。"
            st.session_state.msg_type = 'error'
        else:
            # 鷹架回饋 (Scaffolding)
            diff = target - current
            if diff > 0:
                st.session_state.msg = f"📉 能量不足：還差 +{diff} (需要藍色粒子)"
                st.session_state.msg_type = 'warn'
            elif diff < 0:
                st.session_state.msg = f"📈 能量過載：超過 +{abs(diff)} (需要紅色粒子抵銷)"
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
        if st.button("🔄 重置戰局"):
            game.restart_game()
            st.rerun()

    progress = st.session_state.level / MAX_LEVEL
    st.progress(progress)
    st.caption(f"Level {st.session_state.level}/{MAX_LEVEL}: {st.session_state.get('level_title', '')}")

    # --- Game Completed ---
    if st.session_state.game_status == 'completed':
        st.balloons()
        st.markdown("""
        <div style="background:linear-gradient(135deg,#7aa2f7,#3d59a1);padding:30px;border-radius:15px;text-align:center;color:white;">
            <h1>🏆 歸零大師！</h1>
            <p>你已參透正負數抵銷的物理法則。</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎓 開啟新一輪試煉", use_container_width=True):
            game.restart_game()
            st.rerun()
        return

    # --- Dashboard (Target vs Current) ---
    target = st.session_state.target
    current = BattleEngine.calculate_current(st.session_state.history)
    
    col_tgt, col_mid, col_cur = st.columns([1, 0.2, 1])
    
    with col_tgt:
        # 目標顯示
        t_color = "#7aa2f7" if target > 0 else "#f7768e"
        if target == 0: t_color = "#9ece6a"
        t_sign = "+" if target > 0 else ""
        st.markdown(f"<div style='text-align:center;color:#565f89;font-size:0.9rem;'>目標電荷</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;font-size:2rem;font-weight:bold;color:{t_color}'>{t_sign}{target}</div>", unsafe_allow_html=True)
        
    with col_mid:
        status_icon = "VS"
        if current == target: status_icon = "✅"
        elif st.session_state.game_status == 'lost': status_icon = "💀"
        st.markdown(f"<div style='text-align:center;font-size:1.5rem;padding-top:15px;color:#a9b1d6'>{status_icon}</div>", unsafe_allow_html=True)
        
    with col_cur:
        # 當前顯示 (純數值，視覺化在下方)
        c_sign = "+" if current > 0 else ""
        st.markdown(f"<div style='text-align:center;color:#565f89;font-size:0.9rem;'>當前電荷</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;font-size:2rem;font-weight:bold;color:#c0caf5'>{c_sign}{current}</div>", unsafe_allow_html=True)

    # --- Status Message ---
    msg_cls = f"status-{st.session_state.msg_type}"
    st.markdown(f'<div class="status-box {msg_cls}">{st.session_state.msg}</div>', unsafe_allow_html=True)

    # --- Battlefield (Visualizer) ---
    st.markdown("**⚛️ 粒子反應爐：**")
    
    # 生成粒子 HTML
    particle_html = BattleEngine.generate_particle_html(current, target)
    st.markdown(f'<div class="battlefield-box">{particle_html}</div>', unsafe_allow_html=True)
    
    # 顯示算式
    latex_eq = BattleEngine.generate_equation_latex(st.session_state.history)
    st.markdown(f'<div class="math-display">{latex_eq} = {current}</div>', unsafe_allow_html=True)

    # --- Control Area ---
    if st.session_state.game_status == 'playing':
        st.write("👇 部署粒子：")
        hand = st.session_state.hand
        
        if hand:
            # 自定義 CSS 讓按鈕變色 (Streamlit 按鈕顏色難以直接控制，這裡依賴 Global CSS 對 Emoji 的潛在渲染或接受統一色調)
            # 在 Streamlit 中，我們可以用 columns 來排列
            cols = st.columns(4)
            for i, card in enumerate(hand):
                with cols[i % 4]:
                    # 使用 type="primary" 為正數 (通常是強調色)，secondary 為負數 (預設色)
                    # 或是統一顏色，靠文字區分
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
