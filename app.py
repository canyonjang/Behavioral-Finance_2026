import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="행동재무학 퀴즈", layout="wide")

# 2. 구글 시트 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("구글 시트 연결 설정(Secrets)이 필요합니다.")

# 3. 이번 주 설정 (매주 문제만 수정하세요)
CURRENT_WEEK = "2주차" 

QUIZ_DATA = [
    {"q": "1. 투자설계란, 투자목표와 (_____________)을 파악하여 투자자의 위험수준에 적정한 투자전략을 수립하는 과정이다.", "a": "투자기간"},
    {"q": "2. 모건 하우절은 '(_________)란 수많은 사람이 한정된 정보를 가지고 불완전한 의사결정을 내리는 일'이라 했다.", "a": "투자"},
    {"q": "3. Stein(1998)의 노년기 3단계 모델은 (_______________), slow-go, no-go 단계로 구성된다.", "a": "go-go 단계"},
    {"q": "4. 주된 일자리에서 (_____________)을 갖는 부분은퇴 단계를 거쳐 완전은퇴에 도달한다.", "a": "가교직업"},
    {"q": "5. 은퇴 이후에는 재무적 측면과 비재무적 측면(_____, 대인관계 등)을 함께 생각해야 한다.", "a": "건강"},
    {"q": "6. 취업자와 실업자를 합쳐서 부르는 말은 (__________________)이다.", "a": "경제활동인구"},
    {"q": "7. 사회보장적 성격의 (____________), 퇴직연금, 개인연금으로 노후소득보장제도가 구성된다.", "a": "공적연금"}
]

# --- [기능] 실시간 명단 자동 업데이트 프래그먼트 ---
@st.fragment(run_every="10s")
def live_attendance_view():
    st.subheader("📍 실시간 제출 완료 명단 (10초 자동 갱신)")
    try:
        # ttl=0으로 설정해야 즉시 반영됩니다.
        all_data = conn.read(worksheet="전체데이터", ttl=0)
        today_list = all_data[all_data['주차'] == CURRENT_WEEK]
        
        if not today_list.empty:
            st.write(f"현재 총 {len(today_list)}명 제출 완료")
            cols = st.columns(6)
            for i, row in enumerate(today_list.itertuples()):
                cols[i % 6].success(f"✅ {row.이름}")
        else:
            st.info("학생들이 제출을 시작하면 이름이 여기에 나타납니다.")
    except:
        st.warning("데이터 연결 확인 중...")

# --- 메인 화면 UI ---
st.title("📊 행동재무학 퀴즈") # '시스템' 글자 삭제

tab1, tab2, tab3 = st.tabs(["✍️ 퀴즈 제출", "🖥️ 실시간 제출자 명단", "🔐 성적 분석(교수용)"])

# --- [TAB 1] 학생 제출 화면 ---
with tab1:
    st.header("답안지") # '2주차' 글자 삭제
    with st.form("quiz_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("이름", placeholder="성함")
        with col2:
            student_id = st.text_input("학번", placeholder="학번")
        
        st.divider()
        
        user_responses = []
        for i, item in enumerate(QUIZ_DATA):
            st.markdown(f"**{item['q']}**")
            ans = st.text_input(f"{i+1}번 답안", key=f"q{i}")
            user_responses.append(ans)

        submitted = st.form_submit_button("답안 제출하고 확인받기")

        if submitted:
            if not name or not student_id:
                st.error("이름과 학번을 입력해 주세요.")
            else:
                row_dict = {
                    "주차": CURRENT_WEEK,
                    "제출시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "이름": name,
                    "학번": student_id
                }
                
                total_correct = 0
                for i, item in enumerate(QUIZ_DATA, 1):
                    u_ans = user_responses[i-1].strip().replace(" ", "")
                    s_ans = item['a'].strip().replace(" ", "")
                    is_correct = (u_ans == s_ans)
                    if is_correct: total_correct += 1
                    row_dict[f"q{i}_답"] = user_responses[i-1]
                    row_dict[f"q{i}_결과"] = "O" if is_correct else "X"
                
                row_dict["총점"] = total_correct
                new_row = pd.DataFrame([row_dict])

                try:
                    # 전체데이터 탭에 저장
                    master_df = conn.read(worksheet="전체데이터", ttl=0)
                    updated_master = pd.concat([master_df, new_row], ignore_index=True)
                    conn.update(worksheet="전체데이터", data=updated_master)
                    
                    st.success(f"{name} 학생, 제출 완료! 명단 탭에서 이름을 확인하세요.")
                    st.balloons()
                except Exception as e:
                    st.error(f"저장 실패. 구글 시트 권한(Service Account)을 확인하세요.")

# --- [TAB 2] 실시간 명단 ---
with tab2:
    live_attendance_view()

# --- [TAB 3] 비밀번호 잠금 성적 분석 ---
with tab3:
    st.header("🔐 관리자 인증")
    # 비밀번호 입력창 (type="password"로 설정하여 글자 숨김)
    admin_pw = st.text_input("비밀번호를 입력하세요", type="password")
    
    if admin_pw == "3383": # <--- 선생님이 원하시는 비밀번호로 변경하세요!
        st.success("인증에 성공했습니다.")
        st.divider()
        try:
            data = conn.read(worksheet="전체데이터", ttl=0)
            if not data.empty:
                st.subheader("학생별 누적 성적")
                stats = data.groupby(['학번', '이름'])['총점'].mean().reset_index()
                stats['정답률(%)'] = (stats['총점'] / 7 * 100).round(1)
                st.dataframe(stats, use_container_width=True)
                
                st.divider()
                st.subheader("전체 데이터 보기")
                st.write(data)
            else:
                st.info("표시할 성적 데이터가 없습니다.")
        except:
            st.error("데이터를 불러오는 데 실패했습니다.")
    elif admin_pw != "":
        st.error("비밀번호가 틀렸습니다.")
