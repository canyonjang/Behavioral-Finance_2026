import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------
# 1. 과목 및 설정
# ---------------------------------------------------------
SUBJECT_NAME = "행동재무학 퀴즈"
CURRENT_WEEK = "9주차" 
ADMIN_PASSWORD = "3383"

QUIZ_DATA = [
    {"q": "1. (_________)은 주식의 수익변동을 자주 관찰하고 이에 대응하는 것이다.", "a": "근시안"},
    {"q": "2. 주식 프리미엄 퍼즐이 발생하는 이유는 대다수 투자자가 (________)을 이기지 못해 주식을 팔아버리기 때문이다.", "a": "열정"},
    {"q": "3. 보유주식에 대한 평가기간이 짧아 평가가 자주 일어날수록 주가의 등락을 예민하게 받아들이게 되고, 그로 인해 주식에 대한 (______)가 줄어들고 채권 (_______)가 늘어난다. (   )에는 같은 단어가 들어갑니다.", "a": "수요"},
    {"q": "4. 탈러는, 투자 자문을 할 때 젊은층은 주식 비중을 높이고 (_______)에서 스포츠를 제외한 것은 절대 보지 말라고 조언한다.", "a": "뉴스"},
    {"q": "5. 시간적으로 멀리 있는 대상에 대해서는 추상적, 본질적, 핵심적인 점에 착안해 (상위/하위) 수준의 해석을 한다. (상위와 하위 중 맞는 것을 적으세요)", "a": "상위"},
    {"q": "6. 심리적 거리 중 (_________) 거리가 대표적이다.", "a": "시간적"},
    {"q": "7. 심리적 거리 중 (__________) 거리는 나와 타인, 혹은 내 집단과 외 집단 간의 거리를 의미한다.", "a": "사회적"}
]



NUM_QUESTIONS = len(QUIZ_DATA)
# ---------------------------------------------------------

st.set_page_config(page_title=f"{SUBJECT_NAME}", layout="wide")

# Supabase 연결 설정
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
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

            submitted = st.form_submit_button("답안 제출하고 확인받기 (기기당 답안 제출은 1회만 가능하니, 신중하게 검토하고 버튼 누르세요)")

            if submitted:
                if not name or not student_id:
                    st.error("이름과 학번을 입력해 주세요.")
                else:
                    try:
                        # 이미 제출한 내역이 있는지 수파베이스에서 조회
                        existing_data = supabase.table("quiz_results").select("*").eq("주차", CURRENT_WEEK).eq("학번", student_id).execute()
                        
                        if existing_data.data: # 데이터가 존재하면(리스트가 비어있지 않으면)
                            st.error(f"❌ {name} 학생은 이미 제출했습니다.")
                        else:
                            total_correct = 0
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
                            
                            # 수파베이스에 새로운 데이터 삽입(Insert)
                            supabase.table("quiz_results").insert(row_dict).execute()
                            
                            st.session_state.submitted_on_this_device = True
                            st.success(f"{name} 학생, 제출 성공!")
                            st.balloons()
                            st.rerun()
                    except:
                        pass

# --- [TAB 2] 수동 새로고침 명단 ---
with tab2:
    st.subheader(f"📍 {CURRENT_WEEK} 제출 완료 명단")
    st.info("명단을 확인하려면 아래 버튼을 누르세요.")
    
    if st.button("🔄 명단 새로고침 (클릭)"):
        try:
            # 해당 주차의 데이터만 수파베이스에서 필터링해서 가져옴
            response = supabase.table("quiz_results").select("*").eq("주차", CURRENT_WEEK).execute()
            today_list = pd.DataFrame(response.data)
            
            if not today_list.empty:
                st.write(f"현재 총 {len(today_list)}명 제출 완료")
                cols = st.columns(6)
                for i, row in enumerate(today_list.itertuples()):
                    cols[i % 6].success(f"✅ {row.이름}")
            else:
                st.write("아직 제출자가 없습니다.")
        except Exception as e:
            st.error("데이터를 불러오는 데 실패했습니다.")

# --- [TAB 3] 성적 분석 ---
with tab3:
    st.header("🔐 관리자 인증")
    if st.text_input("비밀번호를 입력하세요", type="password") == ADMIN_PASSWORD:
        try:
            # 전체 데이터를 가져와서 분석
            response = supabase.table("quiz_results").select("*").execute()
            df = pd.DataFrame(response.data)
            
            if not df.empty:
                st.subheader("학생별 평균 정답률")
                stats = df.groupby(['학번', '이름'])['총점'].mean().reset_index()
                stats['정답률(%)'] = (stats['총점'] / NUM_QUESTIONS * 100).round(1)
                st.dataframe(stats, use_container_width=True)
                st.divider()
                st.download_button("엑셀 데이터 다운로드", data=df.to_csv(index=False).encode('utf-8-sig'), file_name=f"{SUBJECT_NAME}_결과.csv", mime="text/csv")
            else:
                st.write("제출된 데이터가 없습니다.")
        except Exception as e: 
            st.write("데이터를 불러오는 중 오류가 발생했습니다.")
