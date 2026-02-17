import streamlit as st
import random
import uuid
from dataclasses import dataclass, field
from typing import List, Dict

# ==========================================
# 0. 全局設定 (Global Config)
# ==========================================
MAX_LEVEL = 10  # 擴展至 10 關

# ==========================================
# 1. 核心配置與 CSS (High Contrast Dark Mode)
# ==========================================
st.set_page_config(
    page_title="整數大對決：歸零之戰 v3.0",
    page_icon="⚔️",
    layout="centered"
)

st.markdown("""
<style>
    /* 全局背景與文字 */
    .stApp { background-color: #020617; color: #f8fafc; }
    
    /* 進度條 */
    .stProgress > div > div > div > div {
        background-color: #60a5fa;
    }
    .stCaption { color: #94a3b8 !important; font-size: 1rem !important; }

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
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* 粒子樣式 */
    .particle {
        display: inline-block;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        margin: 2px;
        box-shadow: 0 0 8px rgba(255,255,255,0.2);
        transition: all 0.3s ease;
    }
    .p-pos { background: #3b82f6; border: 2px solid #93c5fd; } /* 藍 */
    .p-neg { background: #ef4444; border: 2px solid #fca5a5; } /* 紅 */
    
    /* 按鈕優化 */
    div.stButton > button {
        border-radius: 10px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 1.2rem !important;
        font-weight: 900 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }
    div.stButton > button:active { transform: scale(0.96); }

    /* 狀態提示框 */
    .status-box {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 15px;
        color: #ffffff;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }
    .status-neutral { background: #1e293b; border: 1px solid #60a5fa; color: #60a5fa; }
    .status-warn { background: #422006; border: 1px solid #eab308; color: #facc15; }
    .status-error { background: #450a0a; border: 1px solid #f87171; color: #fca5a5; }
    .status-success { background: #052e16; border: 1px solid #4ade80; color: #4ade80; }

    /* 數學顯示 */
    .math-display {
        font-size: 1.6rem;
        font-family: monospace;
        color: #ffffff;
        background: #000000;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #334155;
        border-left: 6px solid #a855f7;
        margin-top: 10px;
    }
    
    /* 數據標籤 */
    .label-text { color: #cbd5e1; font-size: 0.9rem; margin-bottom: 5px; font-weight: bold; }
    .value-text { font-size: 2.2rem; font-weight: 900; text-shadow: 0 0 10px rgba(0,0,0,0.5); }
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
            return f"🔴 {self.value}"

# ==========================================
# 3. 戰鬥引擎 (Logic Layer)
# ==========================================

class BattleEngine:
    
    @staticmethod
    def generate_level(level: int) -> dict:
        """
        10關循序漸進設計：
        1. 正數加法 (基礎)
        2. 負數加法 (方向感)
        3. 簡單抵銷 (歸零入門)
        4. 正數目標 (混合運算)
        5. 負數目標 (混合運算)
        6. 中型數字 (擴大範圍)
        7. 歸零挑戰 (多步抵銷)
        8. 三步運算 (策略組合)
        9. 大型數字 (複雜混合)
        10. 最終試煉 (高精度)
        """
        config = {
            1: {'range': [1, 2, 3], 'type': 'pos_only', 'steps': 2, 'title': "L1: 能量填充 (正數)"},
            2: {'range': [-1, -2, -3], 'type': 'neg_only', 'steps': 2, 'title': "L2: 深淵潛航 (負數)"},
            3: {'range': [-1, 1], 'type': 'zero', 'steps': 2, 'title': "L3: 物質湮滅 (歸零)"},
            4: {'range': [-2, -1, 1, 2, 3], 'type': 'mixed_pos', 'steps': 3, 'title': "L4: 混沌平衡 I (偏正)"},
            5: {'range': [-3, -2, -1, 1, 2], 'type': 'mixed_neg', 'steps': 3, 'title': "L5: 混沌平衡 II (偏負)"},
            6: {'range': [2, 3, 4, 5], 'type': 'pos_mid', 'steps': 3, 'title': "L6: 能量過載 (進階加法)"},
            7: {'range': [-5, -3, 3, 5], 'type': 'zero_mid', 'steps': 4, 'title': "L7: 虛空迴路 (進階歸零)"},
            8: {'range': [-4, -2, 3, 6], 'type': 'mixed_step3', 'steps': 3, 'title': "L8: 三重奏 (策略運算)"},
            9: {'range': [-8, -5, 4, 7, 9], 'type': 'chaos', 'steps': 4, 'title': "L9: 亂流風暴 (大數混合)"},
            10: {'range': [-10, -7, -3, 5, 8, 12], 'type': 'boss', 'steps': 5, 'title': "L10: 虛空領主 (最終試煉)"}
        }
        cfg = config.get(level, config[10])
        
        # --- 動態生成邏輯 (保證有解) ---
        correct_path = []
        current_sum = 0
        
        # 1. 生成正確路徑
        for _ in range(cfg['steps']):
            # 根據類型篩選候選數字
            pool = cfg['range']
            if cfg['type'] == 'pos_only':
                pool = [x for x in pool if x > 0]
            elif cfg['type'] == 'neg_only':
                pool = [x for x in pool if x < 0]
            
            val = random.choice(pool)
            correct_path.append(IntegerCard(val))
            current_sum += val
            
        # 2. 設定目標 (L3/L7 強制歸零)
        target = current_sum
        if 'zero' in cfg['type']:
            # 如果隨機沒歸零，補一張卡讓它歸零，並把這張卡加入手牌
            if current_sum != 0:
                fix_card = IntegerCard(-current_sum)
                correct_path.append(fix_card)
                target = 0
        
        # 3. 混入干擾項 (Distractors)
        # 難度越高，干擾項越多
        distractor_count = 2
        if level >= 6: distractor_count = 3
        if level >= 9: distractor_count = 4
        
        distractors = []
        for _ in range(distractor_count):
            distractors.append(IntegerCard(random.choice(cfg['range'])))
            
        hand = correct_path + distractors
        random.shuffle(hand)
        
        return {"target": target, "hand": hand, "title": cfg['title']}

    @staticmethod
    def calculate_current(history: List[IntegerCard]) -> int:
        return sum(card.value for card in history)

    @staticmethod
    def generate_particle_html(current: int, target: int) -> str:
        """[Visual Engine] 粒子視覺化"""
        html = '<div style="line-height: 28px;">'
        
        net_val = current
        abs_val = abs(net_val)
        particles = ""
        # 隨等級增加顯示上限，避免 L10 炸版
        display_limit = 20 
        
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
                st.session_state.msg_type = 'neutral'
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
            <p>10 層試煉全部通關！</p>
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
        # 顏色邏輯：亮藍(正) / 亮紅(負) / 萊姆綠(零)
        t_color = "#60a5fa" if target > 0 else "#f87171"
        if target == 0: t_color = "#a3e635"
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

    # --- Battlefield ---
    st.markdown("**⚛️ 粒子反應爐：**")
    particle_html = BattleEngine.generate_particle_html(current, target)
    st.markdown(f'<div class="battlefield-box">{particle_html}</div>', unsafe_allow_html=True)
    
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
