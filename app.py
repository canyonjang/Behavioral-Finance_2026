import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# 1. 과목 및 설정 (수정 포인트)
# ---------------------------------------------------------
SUBJECT_NAME = "행동재무학 퀴즈"
CURRENT_WEEK = "1주차" 
ADMIN_PASSWORD = "3383"

QUIZ_DATA = [
    {"q": "1. MIT Media Lab의 실험 결과는, AI 도구 사용 시 (__________) 사고가 중요함을 보여준다.", "a": "비판적"},
    {"q": "2. 질문독서법에서 (_________) 질문은 문맥과 맥락을 파악하는 질문이다.", "a": "추론적"},
    {"q": "3. 행동의 결과가 불확실한 상황에서 경제주체의 합리적 판단은 결과에 관한 효용기대치에 입각하여 이뤄진다고 설명하는 경제학 이론은? (_____________)", "a": "기대효용이론"},
    {"q": "4. 호모 이코노미쿠스(homo economicus)로서 인간이, 자기 이익을 추구하며, 자신의 환경에 대해 잘 알고, 계산 능력이 뛰어나며, 완벽한 정보를 가지고 있다고 주장하기 위해 필요한 개념은? (_____________)", "a": "무제한 합리성"},
    {"q": "5. 허버트 사이먼이 주장한 현실에서의 인간의 특성은? (_____________)", "a": "제한된 합리성"},
    {"q": "6. 카너먼과 트버스키가 주장한 행동경제학의 핵심 이론은? (__________)", "a": "전망이론"},
    {"q": "7. 카너먼과 트버스키가 합리성이 비현실적인 개념임을 주장하기 위해 연구한 두 가지 주제는? (_________), (____________)", "a": "휴리스틱, 바이어스"}
]

NUM_QUESTIONS = len(QUIZ_DATA)
# ---------------------------------------------------------

st.set_page_config(page_title=f"{SUBJECT_NAME}", layout="wide")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("Secrets 설정을 확인해주세요.")

if "submitted_on_this_device" not in st.session_state:
    st.session_state.submitted_on_this_device = False

# --- 메인 UI ---
st.title(f"📊 {SUBJECT_NAME}")

tab1, tab2, tab3 = st.tabs(["✍️ 퀴즈 제출", "🖥️ 제출자 명단 확인", "🔐 성적 분석(교수용)"])

# --- [TAB 1] 학생 제출 화면 (API 부하 최소화 버전) ---
with tab1:
    st.header("답안지")
    
    if st.session_state.submitted_on_this_device:
        st.warning("⚠️ 이 기기에서 제출이 완료되었습니다.")
    else:
        with st.form("quiz_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1: name = st.text_input("이름")
            with col2: student_id = st.text_input("학번")
            
            st.divider()
            
            user_responses = []
            for i, item in enumerate(QUIZ_DATA):
                st.markdown(f"**{item['q']}**")
                ans = st.text_input(f"{i+1}번 답안", key=f"q{i}")
                user_responses.append(ans)

            submitted = st.form_submit_button(f"제출하기 (총 {NUM_QUESTIONS}문항)")

            if submitted:
                if not name or not student_id:
                    st.error("이름과 학번을 입력하세요.")
                else:
                    try:
                        # [최적화] 데이터를 한 번만 읽어서 모든 검사와 저장을 처리
                        master_df = conn.read(worksheet="전체데이터", ttl=0)
                        
                        # 중복 체크
                        already_exists = master_df[(master_df['주차'] == CURRENT_WEEK) & (master_df['학번'] == student_id)]
                        
                        if not already_exists.empty:
                            st.error(f"❌ {name} 학생은 이미 제출했습니다.")
                        else:
                            # 채점
                            total_correct = 0
                            row_dict = {"주차": CURRENT_WEEK, "제출시간": datetime.now().strftime("%H:%M:%S"), "이름": name, "학번": student_id}
                            
                            for i, item in enumerate(QUIZ_DATA, 1):
                                s_ans_set = set(item['a'].replace(" ", "").split(","))
                                u_ans_set = set(user_responses[i-1].replace(" ", "").split(","))
                                is_correct = (s_ans_set == u_ans_set)
                                if is_correct: total_correct += 1
                                row_dict[f"q{i}_답"] = user_responses[i-1]
                                row_dict[f"q{i}_결과"] = "O" if is_correct else "X"
                            
                            row_dict["총점"] = total_correct
                            
                            # [최적화] '전체데이터'에만 딱 한 번 업데이트 (이중 저장 제거)
                            new_data = pd.concat([master_df, pd.DataFrame([row_dict])], ignore_index=True)
                            conn.update(worksheet="전체데이터", data=new_data)
                            
                            st.session_state.submitted_on_this_device = True
                            st.success(f"{name} 학생, 제출 성공!")
                            st.balloons()
                            st.rerun()
                    except:
                        st.error("⚠️ 일시적인 과부하입니다. 10초 후 다시 '제출하기'를 눌러주세요.")

# --- [TAB 2] 수동 새로고침 명단 ---
with tab2:
    st.subheader(f"📍 {CURRENT_WEEK} 제출 완료 명단")
    st.info("자동 새로고침이 꺼져 있습니다. 명단을 확인하려면 아래 버튼을 누르세요.")
    
    if st.button("🔄 명단 새로고침 (클릭)"):
        try:
            # 버튼을 누를 때만 API 호출
            data = conn.read(worksheet="전체데이터", ttl=0)
            today_list = data[data['주차'] == CURRENT_WEEK]
            
            if not today_list.empty:
                st.write(f"현재 총 {len(today_list)}명 제출 완료")
                cols = st.columns(6)
                for i, row in enumerate(today_list.itertuples()):
                    cols[i % 6].success(f"✅ {row.이름}")
            else:
                st.write("아직 제출자가 없습니다.")
        except:
            st.error("데이터를 불러오는 데 실패했습니다. 잠시 후 다시 시도하세요.")

# --- [TAB 3] 성적 분석 ---
with tab3:
    st.header("🔐 교수용 관리")
    if st.text_input("비밀번호", type="password") == ADMIN_PASSWORD:
        try:
            df = conn.read(worksheet="전체데이터", ttl=0)
            stats = df.groupby(['학번', '이름'])['총점'].mean().reset_index()
            stats['정답률(%)'] = (stats['총점'] / NUM_QUESTIONS * 100).round(1)
            st.dataframe(stats, use_container_width=True)
            st.download_button("엑셀 데이터 다운로드", data=df.to_csv(index=False).encode('utf-8-sig'), file_name=f"{SUBJECT_NAME}_결과.csv", mime="text/csv")
        except: st.write("데이터가 없습니다.")
