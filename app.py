import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# 1. 과목 및 설정 (새 과목을 만드실 때 이 부분만 수정하세요)
# ---------------------------------------------------------
SUBJECT_NAME = "행동재무학 퀴즈"  # 과목 제목
CURRENT_WEEK = "1주차"          # 해당 주차
ADMIN_PASSWORD = "3383"         # 선생님용 비밀번호

# 퀴즈 데이터 (문제 개수는 마음대로 조절하세요)
QUIZ_DATA = [
    {"q": "1. MIT Media Lab의 실험 결과는, AI 도구 사용 시 (__________) 사고가 중요함을 보여준다.", "a": "비판적"},
    {"q": "2. 질문독서법에서 (_________) 질문은 문맥과 맥락을 파악하는 질문이다.", "a": "추론적"},
    {"q": "3. 행동의 결과가 불확실한 상황에서 경제주체의 합리적 판단은 결과에 관한 효용기대치에 입각하여 이뤄진다고 설명하는 경제학 이론은? (_____________)", "a": "기대효용이론"},
    {"q": "4. 호모 이코노미쿠스(homo economicus)로서 인간이, 자기 이익을 추구하며, 자신의 환경에 대해 잘 알고, 계산 능력이 뛰어나며, 완벽한 정보를 가지고 있다고 주장하기 위해 필요한 개념은? (_____________)", "a": "무제한 합리성"},
    {"q": "5. 허버트 사이먼이 주장한 현실에서의 인간의 특성은? (_____________)", "a": "제한된 합리성"},
    {"q": "6. 카너먼과 트버스키가 주장한 행동경제학의 핵심 이론은? (__________)", "a": "전망이론"},
    {"q": "7. 카너먼과 트버스키가 합리성이 비현실적인 개념임을 주장하기 위해 연구한 두 가지 주제는? (_________), (____________)", "a": "휴리스틱, 바이어스"}
]

# 문항 수를 자동으로 계산합니다.
NUM_QUESTIONS = len(QUIZ_DATA) 
# ---------------------------------------------------------

# 페이지 설정
st.set_page_config(page_title=f"{SUBJECT_NAME}", layout="wide")

# 구글 시트 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("구글 시트 연결 설정(Secrets)이 필요합니다.")

# [세션 상태] 기기별 제출 여부 메모리
if "submitted_on_this_device" not in st.session_state:
    st.session_state.submitted_on_this_device = False

# [기능] 실시간 명단 자동 업데이트
@st.fragment(run_every="10s")
def live_attendance_view():
    st.subheader(f"📍 {CURRENT_WEEK} 실시간 제출 완료 명단 (10초 자동 갱신)")
    try:
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

# 메인 화면 UI
st.title(f"📊 {SUBJECT_NAME}")

tab1, tab2, tab3 = st.tabs(["✍️ 퀴즈 제출", "🖥️ 실시간 제출자 명단", "🔐 성적 분석(교수용)"])

# --- [TAB 1] 학생 제출 화면 ---
with tab1:
    st.header("답안지")
    
    if st.session_state.submitted_on_this_device:
        st.warning("⚠️ 이 기기에서 제출이 완료되었습니다. 응시는 더 이상 불가능합니다.")
    else:
        with st.form("quiz_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("이름", placeholder="이름")
            with col2:
                student_id = st.text_input("학번", placeholder="학번")
            
            st.divider()
            
            user_responses = []
            for i, item in enumerate(QUIZ_DATA):
                st.markdown(f"**{item['q']}**")
                ans = st.text_input(f"{i+1}번 답안", key=f"q{i}")
                user_responses.append(ans)

            submitted = st.form_submit_button(f"답안 제출하고 확인받기 (기기당 답안 제출은 1회만 가능하니, 신중하게 검토하고 버튼 누르세요)")

            if submitted:
                if not name or not student_id:
                    st.error("이름과 학번을 입력해 주세요.")
                else:
                    try:
                        master_data = conn.read(worksheet="전체데이터", ttl=0)
                        already_exists = master_data[
                            (master_data['주차'] == CURRENT_WEEK) & 
                            (master_data['학번'] == student_id)
                        ]

                        if not already_exists.empty:
                            st.error(f"❌ {name} 학생은 이미 이번 주 답안을 제출했습니다.")
                        else:
                            row_dict = {
                                "주차": CURRENT_WEEK,
                                "제출시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "이름": name,
                                "학번": student_id
                            }
                            
                            # 채점 및 데이터 생성 (순서 무관 채점 방식 적용)
                            total_correct = 0
                            for i, item in enumerate(QUIZ_DATA, 1):
                                # 띄어쓰기 제거 및 집합 비교
                                s_ans_set = set(item['a'].replace(" ", "").split(","))
                                u_ans_set = set(user_responses[i-1].replace(" ", "").split(","))
                                
                                is_correct = (s_ans_set == u_ans_set)
                                if is_correct: total_correct += 1
                                
                                row_dict[f"q{i}_답"] = user_responses[i-1]
                                row_dict[f"q{i}_결과"] = "O" if is_correct else "X"
                            
                            row_dict["총점"] = total_correct
                            new_row = pd.DataFrame([row_dict])

                            # 이중 저장
                            updated_master = pd.concat([master_data, new_row], ignore_index=True)
                            conn.update(worksheet="전체데이터", data=updated_master)
                            try:
                                week_data = conn.read(worksheet=CURRENT_WEEK, ttl=0)
                                updated_week = pd.concat([week_data, new_row], ignore_index=True)
                                conn.update(worksheet=CURRENT_WEEK, data=updated_week)
                            except: pass
                            
                            st.session_state.submitted_on_this_device = True
                            st.success(f"{name} 학생, 제출 성공! ({total_correct}/{NUM_QUESTIONS})")
                            st.balloons()
                            st.rerun() 
                            
                    except Exception as e:
                        st.error("저장 실패. 구글 시트 탭 이름을 확인하세요.")

# --- [TAB 2] 실시간 명단 ---
with tab2:
    live_attendance_view()

# --- [TAB 3] 비밀번호 잠금 성적 분석 ---
with tab3:
    st.header("🔐 관리자 인증")
    admin_pw = st.text_input("비밀번호를 입력하세요", type="password")
    
    if admin_pw == ADMIN_PASSWORD:
        st.success("인증 성공")
        try:
            data = conn.read(worksheet="전체데이터", ttl=0)
            if not data.empty:
                st.subheader("학생별 평균 정답률")
                stats = data.groupby(['학번', '이름'])['총점'].mean().reset_index()
                # 문항 수(NUM_QUESTIONS)를 기준으로 정답률을 자동 계산합니다.
                stats['정답률(%)'] = (stats['총점'] / NUM_QUESTIONS * 100).round(1)
                st.dataframe(stats, use_container_width=True)
                st.divider()
                st.subheader("누적 데이터 전체 보기")
                st.write(data)
            else:
                st.info("데이터가 없습니다.")
        except:
            st.error("데이터 로드 실패")
    elif admin_pw != "":
        st.error("비밀번호 불일치")

