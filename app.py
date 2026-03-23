import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------
# 1. 과목 및 설정
# ---------------------------------------------------------
SUBJECT_NAME = "행동재무학 퀴즈"
CURRENT_WEEK = "4주차" 
ADMIN_PASSWORD = "3383"

QUIZ_DATA = [
    {"q": "1. 95%에서 100%로가, 60%에서 65%로보다 크게 인식되는 것을 (___________) 효과라고 한다.", "a": "확실성"},
    {"q": "2. 사건이 일어나고 나서 결과가 그렇게 될 것임을 알고 있었다고 생각하는 것은 (_____________) 편향이다.", "a": "사후 판단"},
    {"q": "3. 사람들이 가질 수 있지만 아직 소유하지 않은 것보다 이미 자기 자산의 일부가 된 것을 더욱 가치 있게 평가하는 것을 탈러는 (_______) 효과라고 명명했다.", "a": "소유"},
    {"q": "4. 도모노 노리오는 보유효과는 (___________)를 구체적으로 드러낸 사례라고 했다.", "a": "손실회피"},
    {"q": "5. 부존자원효과는 주로 내구성이 있는 (__________)에서 발생한다.", "a": "소비재"},
    {"q": "6. 스벅 아아 배지는, 커피 그 자체가 아니라, 커피로 교환할 수 있는 쿠폰이며, 쿠폰은 사용하기 전까지는 내구적 (_______)로 볼 수 있다. (한글만 적으세요)", "a": "권리"},
    {"q": "7. 복권 or 3달러 실험에서 피실험자들이 복권이나 3달러를 그대로 보유하는 것은 (__________) 편향과 관련된다.", "a": "현상유지"}
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

# --- [TAB 1] 학생 제출 화면 ---
with tab1:
    st.header("답안지")
    
    if st.session_state.submitted_on_this_device:
        st.warning("⚠️ 이 기기에서 제출이 완료되었습니다. 응시는 더 이상 불가능합니다.")
    else:
        with st.form("quiz_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1: name = st.text_input("이름", placeholder="이름")
            with col2: student_id = st.text_input("학번", placeholder="학번")
            
            st.divider()
            
            user_responses = []
            for i, item in enumerate(QUIZ_DATA):
                st.markdown(f"**{item['q']}**")
                ans = st.text_input(f"{i+1}번 답안", key=f"q{i}")
                user_responses.append(ans)

            # 1. 제출 버튼 문구 수정
            submitted = st.form_submit_button("답안 제출하고 확인받기 (기기당 답안 제출은 1회만 가능하니, 신중하게 검토하고 버튼 누르세요)")

            if submitted:
                if not name or not student_id:
                    st.error("이름과 학번을 입력해 주세요.")
                else:
                    try:
                        master_df = conn.read(worksheet="전체데이터", ttl=0)
                        
                        already_exists = master_df[(master_df['주차'] == CURRENT_WEEK) & (master_df['학번'] == student_id)]
                        
                        if not already_exists.empty:
                            st.error(f"❌ {name} 학생은 이미 제출했습니다.")
                        else:
                            total_correct = 0
                            # 2. 제출 시간 포맷 수정 (한국 시간 KST 기준 적용)
                            kst = timezone(timedelta(hours=9))
                            now_time = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
                            
                            row_dict = {"주차": CURRENT_WEEK, "제출시간": now_time, "이름": name, "학번": student_id}
                            
                            for i, item in enumerate(QUIZ_DATA, 1):
                                s_ans_set = set(item['a'].replace(" ", "").split(","))
                                u_ans_set = set(user_responses[i-1].replace(" ", "").split(","))
                                is_correct = (s_ans_set == u_ans_set)
                                if is_correct: total_correct += 1
                                row_dict[f"q{i}_답"] = user_responses[i-1]
                                row_dict[f"q{i}_결과"] = "O" if is_correct else "X"
                            
                            row_dict["총점"] = total_correct
                            
                            new_data = pd.concat([master_df, pd.DataFrame([row_dict])], ignore_index=True)
                            conn.update(worksheet="전체데이터", data=new_data)
                            
                            st.session_state.submitted_on_this_device = True
                            st.success(f"{name} 학생, 제출 성공!")
                            st.balloons()
                            st.rerun()
                    except:
                        # 3. 과부하 안내 문구 삭제 (pass로 처리하여 아무 메시지 출력 안 함)
                        pass

# --- [TAB 2] 수동 새로고침 명단 ---
with tab2:
    st.subheader(f"📍 {CURRENT_WEEK} 제출 완료 명단")
    st.info("명단을 확인하려면 아래 버튼을 누르세요.")
    
    if st.button("🔄 명단 새로고침 (클릭)"):
        try:
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
            st.error("데이터를 불러오는 데 실패했습니다.")

# --- [TAB 3] 성적 분석 ---
with tab3:
    st.header("🔐 관리자 인증")
    if st.text_input("비밀번호를 입력하세요", type="password") == ADMIN_PASSWORD:
        try:
            df = conn.read(worksheet="전체데이터", ttl=0)
            if not df.empty:
                st.subheader("학생별 평균 정답률")
                stats = df.groupby(['학번', '이름'])['총점'].mean().reset_index()
                stats['정답률(%)'] = (stats['총점'] / NUM_QUESTIONS * 100).round(1)
                st.dataframe(stats, use_container_width=True)
                st.divider()
                st.download_button("엑셀 데이터 다운로드", data=df.to_csv(index=False).encode('utf-8-sig'), file_name=f"{SUBJECT_NAME}_결과.csv", mime="text/csv")
        except: st.write("데이터가 없습니다.")


