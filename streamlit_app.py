import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
from datetime import datetime
import json

# ──────────────────────────────────────────────
# 페이지 기본 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI 투자 상담사",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# 커스텀 CSS — 전문적인 금융 UI 톤앤매너
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* 전체 배경 & 기본 텍스트 */
    .stApp {
        background: linear-gradient(180deg, #0b1220 0%, #101a2c 100%);
    }
    html, body, [class*="css"] {
        font-size: 16px;
        line-height: 1.65;
    }
    /* 본문 전반의 텍스트 색상을 밝게 — 가독성 강화 */
    .stMarkdown, .stMarkdown p, .stMarkdown li,
    [data-testid="stChatMessageContent"], [data-testid="stChatMessageContent"] p {
        color: #f5f7fa !important;
        font-size: 16.5px !important;
        line-height: 1.7 !important;
    }

    /* 메인 타이틀 영역 */
    .hero-header {
        padding: 28px 32px;
        border-radius: 16px;
        background: linear-gradient(135deg, #1a2b4d 0%, #0e1730 100%);
        border: 1px solid rgba(99, 179, 237, 0.35);
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        margin-bottom: 20px;
    }
    .hero-title {
        font-size: 34px;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        text-shadow: 0 1px 12px rgba(99,179,237,0.35);
    }
    .hero-subtitle {
        color: #d7dee8;
        font-size: 16px;
        font-weight: 500;
        margin-top: 8px;
    }

    /* 지표 카드 */
    .metric-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.14);
        border-radius: 12px;
        padding: 14px 16px;
        text-align: center;
    }
    .metric-label {
        color: #cbd5e0;
        font-size: 12.5px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .metric-value {
        color: #ffffff;
        font-size: 20px;
        font-weight: 800;
        margin-top: 4px;
    }

    /* 채팅 메시지 버블 — 배경을 넣어 텍스트와 대비를 확실히 */
    [data-testid="stChatMessage"] {
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 10px;
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(255,255,255,0.09);
    }
    [data-testid="stChatMessageContent"] strong {
        color: #90cdf4;
    }
    [data-testid="stChatMessageContent"] code {
        color: #f6ad55;
        background: rgba(255,255,255,0.08);
    }

    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background: #0e1730;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #90cdf4;
        font-weight: 800;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #eef2f7 !important;
        font-size: 15px !important;
        font-weight: 500;
    }

    /* 예시 질문 버튼 및 일반 버튼 텍스트 */
    .stButton button {
        color: #f5f7fa !important;
        font-weight: 600 !important;
        border: 1px solid rgba(255,255,255,0.16) !important;
    }

    /* 경고/디스클레이머 박스 */
    .disclaimer-box {
        background: rgba(237, 137, 54, 0.12);
        border-left: 3px solid #ed8936;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 13.5px;
        font-weight: 500;
        color: #ffe8cf;
        margin-top: 16px;
    }

    /* 입력창 */
    .stChatInputContainer {
        border-radius: 12px;
    }
    [data-testid="stChatInput"] textarea {
        color: #f5f7fa !important;
        font-size: 16px !important;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 음성 읽어주기 기능 (브라우저 내장 TTS 사용 — 추가 비용 없음)
# ──────────────────────────────────────────────
def render_tts_button(text: str, key: str, rate: float = 1.0, autoplay: bool = False):
    """assistant 답변 아래에 '읽어주기 / 정지' 버튼을 렌더링한다.
    브라우저의 Web Speech API(SpeechSynthesis)를 사용하므로 별도 API 호출이나 비용이 들지 않는다.
    """
    text_json = json.dumps(text)  # 따옴표/줄바꿈 등을 안전하게 이스케이프
    autoplay_js = "speakNow();" if autoplay else ""
    html_code = f"""
    <div style="display:flex; align-items:center; gap:8px; margin: 2px 0 10px 0; font-family: sans-serif;">
      <button id="play-{key}" onclick="speakNow()" style="
          background: rgba(99,179,237,0.15);
          color:#90cdf4;
          border:1px solid rgba(99,179,237,0.4);
          border-radius:8px;
          padding:5px 12px;
          font-size:13px;
          font-weight:600;
          cursor:pointer;
      ">🔊 읽어주기</button>
      <button id="stop-{key}" onclick="stopNow()" style="
          background: rgba(255,255,255,0.06);
          color:#cbd5e0;
          border:1px solid rgba(255,255,255,0.16);
          border-radius:8px;
          padding:5px 12px;
          font-size:13px;
          font-weight:600;
          cursor:pointer;
      ">⏹ 정지</button>
      <span id="status-{key}" style="color:#a0aec0; font-size:12px;"></span>
    </div>
    <script>
      const ttsText_{key} = {text_json};
      function speakNow() {{
        if (!window.speechSynthesis) {{
          document.getElementById('status-{key}').innerText = '이 브라우저는 음성 읽기를 지원하지 않습니다.';
          return;
        }}
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(ttsText_{key});
        utter.lang = 'ko-KR';
        utter.rate = {rate};
        utter.onstart = () => document.getElementById('status-{key}').innerText = '재생 중...';
        utter.onend = () => document.getElementById('status-{key}').innerText = '';
        window.speechSynthesis.speak(utter);
      }}
      function stopNow() {{
        if (window.speechSynthesis) {{
          window.speechSynthesis.cancel();
          document.getElementById('status-{key}').innerText = '';
        }}
      }}
      {autoplay_js}
    </script>
    """
    components.html(html_code, height=40)


# ──────────────────────────────────────────────
# 히어로 헤더
# ──────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <p class="hero-title">📈 AI 투자 상담사</p>
    <p class="hero-subtitle">GPT 기반 개인 맞춤형 투자 어드바이저 · 시장 분석 · 포트폴리오 전략 상담</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 사이드바 — API 키 & 투자자 프로필 설정
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 상담 설정")

    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="https://platform.openai.com/account/api-keys 에서 발급받을 수 있습니다.",
    )

    st.markdown("---")
    st.markdown("### 👤 투자자 프로필")

    risk_profile = st.select_slider(
        "위험 성향",
        options=["안정형", "안정추구형", "위험중립형", "적극투자형", "공격투자형"],
        value="위험중립형",
    )

    horizon = st.radio(
        "투자 기간",
        ["단기 (1년 이내)", "중기 (1~3년)", "장기 (3년 이상)"],
        index=1,
    )

    market_focus = st.multiselect(
        "관심 시장",
        ["국내 주식 (코스피/코스닥)", "미국 주식", "채권", "ETF", "원자재/금", "암호화폐"],
        default=["국내 주식 (코스피/코스닥)", "미국 주식"],
    )

    model_choice = st.selectbox(
        "모델 선택",
        ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        index=0,
    )

    st.markdown("---")
    st.markdown("### 🔊 음성 읽기")
    auto_read = st.toggle("답변 자동으로 읽어주기", value=False)
    speech_rate = st.slider("읽는 속도", min_value=0.5, max_value=1.5, value=1.0, step=0.1)

    st.markdown("---")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("""
    <div class="disclaimer-box">
        ⚠️ 본 챗봇은 정보 제공 목적이며 투자 자문이 아닙니다.
        투자 판단과 그 결과에 대한 책임은 투자자 본인에게 있습니다.
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 상단 요약 지표 (프로필 확인용)
# ──────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">위험 성향</div>
    <div class="metric-value">{risk_profile}</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">투자 기간</div>
    <div class="metric-value">{horizon.split(" ")[0]}</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">관심 시장</div>
    <div class="metric-value">{len(market_focus)}개 선택</div></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">오늘 날짜</div>
    <div class="metric-value">{datetime.now().strftime("%Y-%m-%d")}</div></div>""", unsafe_allow_html=True)

st.write("")

# ──────────────────────────────────────────────
# API 키 미입력 시 안내
# ──────────────────────────────────────────────
if not openai_api_key:
    st.info("👈 왼쪽 사이드바에 OpenAI API 키를 입력하면 상담을 시작할 수 있습니다.", icon="🗝️")
else:
    client = OpenAI(api_key=openai_api_key)

    # 투자 상담사 페르소나 시스템 프롬프트 (프로필 반영)
    system_prompt = f"""당신은 신중하고 전문적인 금융/투자 상담 AI입니다.
사용자의 투자 성향은 '{risk_profile}', 투자 기간은 '{horizon}', 관심 시장은 '{", ".join(market_focus) if market_focus else "미지정"}'입니다.
이 프로필을 참고하여 답변하되, 다음 원칙을 지키세요:
1. 특정 종목의 '매수/매도'를 단정적으로 지시하지 말고, 근거와 리스크를 함께 제시할 것
2. 데이터나 최신 시황을 알 수 없는 경우 그 한계를 명확히 밝힐 것
3. 항상 분산투자, 리스크 관리의 중요성을 상기시킬 것
4. 답변은 한국어로, 이해하기 쉽되 전문 용어는 간단히 풀어서 설명할 것
5. 확정적인 수익 예측이나 보장을 하지 말 것
6. 이 상담은 정보 제공 목적이며 법적 투자자문이 아님을 필요시 안내할 것
"""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 기존 대화 표시
    for idx, message in enumerate(st.session_state.messages):
        avatar = "🧑‍💼" if message["role"] == "user" else "📊"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                render_tts_button(message["content"], key=f"hist_{idx}", rate=speech_rate)

    # 대화가 없을 때 예시 질문 제시
    if not st.session_state.messages:
        st.markdown("##### 💡 이런 질문으로 시작해보세요")
        example_cols = st.columns(3)
        examples = [
            "지금 제 성향에 맞는 자산배분 전략을 알려줘",
            "코스피 변동성이 클 때 리밸런싱은 어떻게 해야 해?",
            "ETF와 개별주 투자의 장단점을 비교해줘",
        ]
        clicked = None
        for c, ex in zip(example_cols, examples):
            with c:
                if st.button(ex, use_container_width=True):
                    clicked = ex
        if clicked:
            st.session_state.messages.append({"role": "user", "content": clicked})
            st.rerun()

    # 채팅 입력
    if prompt := st.chat_input("투자 관련 질문을 입력하세요 (예: 지금 채권 비중을 늘려야 할까요?)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="📊"):
            stream = client.chat.completions.create(
                model=model_choice,
                messages=[{"role": "system", "content": system_prompt}]
                + [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
                temperature=0.4,
            )
            response = st.write_stream(stream)
            render_tts_button(
                response,
                key=f"live_{len(st.session_state.messages)}",
                rate=speech_rate,
                autoplay=auto_read,
            )

        st.session_state.messages.append({"role": "assistant", "content": response})
