import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------
# 1. 과목 및 설정
# ---------------------------------------------------------
SUBJECT_NAME = "행동재무학 퀴즈"
CURRENT_WEEK = "7주차" 
ADMIN_PASSWORD = "3383"

QUIZ_DATA = [
    {"q": "1. 원래 500달러인데 난 400달러에 샀으니 100달러 이득이야라는 만족감이 소비의 고통을 완전히 덮어버리는 상황은 (____________)에 집중하는 것이다.", "a": "거래효용"},
    {"q": "2. 월급이 찔끔 올랐을 때보다 기름값이 내려갔을 때 사람들이 고급 휘발유에 쉽게 지출하는 것은 (____________)의 마법이 작동하기 때문이다.", "a": "심리계좌"},
    {"q": "3. 지수형 할인의 할인율(r)은 시간(d)에 상관없이 비교적 일정하다. (맞음 또는 틀림 중 하나로 답하세요)", "a": "틀림"},
    {"q": "4. 시간과 보상 시뮬레이터의 결과, 1만원 세트와 100만원 세트의 k값은 차이가 없다. (맞음 또는 틀림 중 하나로 답하세요)", "a": "틀림"},
    {"q": "5. 쌍곡형 할인은 현재라는 차원과 미래라는 차원 중에서 현재가 부각되면서 할인 시점들 사이에 발생하는 (______________)이다.", "a": "선호역전"},
    {"q": "6. 쌍곡형 할인에는 인내, 유혹, (____________) 등이 수반된다.", "a": "자기통제"},
    {"q": "7. 시점 간 선택은 가구의 소비가 소득에 따라 어떻게 달라지는지 말해주는 (_____________)의 이론적 근간을 이룬다.", "a": "소비함수"}
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
