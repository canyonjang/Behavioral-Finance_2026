import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="금융과 노후설계 퀴즈 시스템", layout="wide")

# 2. 구글 시트 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("구글 시트 연결 설정이 필요합니다.")

# 3. 이번 주 퀴즈 데이터 (매주 이 부분의 문제와 정답만 수정하세요)
QUIZ_DATA = [
    {"q": "1. 투자설계란, 투자목표와 (_____________)을 파악하여 투자자의 위험수준에 적정한 투자전략을 수립, 실행하고 이를 모니터링하는 과정이다.", "a": "투자기간"},
    {"q": "2. 돈의 심리학 저자인 모건 하우절은 '(_________)란 수많은 사람이 한정된 정보를 가지고 자신의 행복에 엄청난 영향을 미칠 사안에 대해 불완전한 의사결정을 내리는 일'이라고 설명한다.", "a": "투자"},
    {"q": "3. Stein(1998)의 노년기의 생활 기능 변화에 따른 3단계 모델은, (_______________), slow-go단계, no-go단계 등으로 구성된다.", "a": "go-go 단계"},
    {"q": "4. 주된 일자리에서 (_____________)을 갖는 부분은퇴 단계를 거쳐 완전은퇴 단계에 도달하는 경우가 많아지고 있다.", "a": "가교직업"},
    {"q": "5. 은퇴 이후의 생활에서는 재무적 측면(소득 감소)과 비재무적 측면(_____, 대인관계, 시간관리, 주거생활의 변화 등)을 함께 생각해야 한다.", "a": "건강"},
    {"q": "6. (__________________)는 생산연령인구 중 수입이 있는 일에 종사하고 있는 사람(취업자)과 취업을 위해 구직활동 중인 사람(실업자)을 가리킨다.", "a": "경제활동인구"},
    {"q": "7. 우리나라 노후소득보장제도는 노후생계를 유지할 수 있도록 도와주는 사회보장적 성격의 (____________), 근로자의 퇴직급여를 바탕으로 한 퇴직연금, 개인이 추가적으로 저축하는 개인연금으로 구성된다.", "a": "공적연금"}
]

st.title("📝 금융과 노후설계 주차별 퀴즈")

tab1, tab2, tab3 = st.tabs(["✍️ 퀴즈 제출", "🖥️ 실시간 제출자 명단", "📊 성적 분석(교사용)"])

# --- [TAB 1] 학생 제출 화면 ---
with tab1:
    st.header("오늘의 퀴즈")
    with st.form("quiz_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("이름", placeholder="성함을 입력하세요")
        with col2:
            student_id = st.text_input("학번", placeholder="학번을 입력하세요")
        
        st.divider()
        
        user_responses = []
        for i, item in enumerate(QUIZ_DATA):
            st.markdown(f"**{item['q']}**")
            ans = st.text_input(f"{i+1}번 답안 입력", key=f"q{i}")
            user_responses.append(ans)

        submitted = st.form_submit_button("답안 제출하고 퇴실하기")

        if submitted:
            if not name or not student_id:
                st.error("이름과 학번을 모두 입력해 주세요.")
            else:
                row_data = {
                    "제출시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "이름": name,
                    "학번": student_id,
                }
                
                total_correct = 0
                for i, item in enumerate(QUIZ_DATA, 1):
                    # 공백 제거 후 채점 (유연한 채점)
                    u_ans = user_responses[i-1].strip().replace(" ", "")
                    s_ans = item['a'].strip().replace(" ", "")
                    
                    is_correct = (u_ans == s_ans)
                    if is_correct:
                        total_correct += 1
                    
                    row_data[f"q{i}_답"] = user_responses[i-1]
                    row_data[f"q{i}_결과"] = "O" if is_correct else "X"
                
                row_data["총점"] = total_correct
                
                try:
                    df = conn.read()
                    new_row = pd.DataFrame([row_data])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(data=updated_df)
                    
                    st.success(f"제출 완료! {name} 학생, 수고하셨습니다. (총점: {total_correct}/7)")
                    st.balloons()
                except:
                    st.error("데이터 저장에 실패했습니다. 구글 시트 연결을 확인하세요.")

# --- [TAB 2] 강의실 화면용 명단 ---
with tab2:
    st.header("🖥️ 실시간 제출 확인 (이름이 뜨면 퇴실 가능)")
    if st.button("명단 새로고침"):
        try:
            data = conn.read()
            today = datetime.now().strftime("%Y-%m-%d")
            today_data = data[data['제출시간'].str.contains(today)]
            
            if not today_data.empty:
                st.write(f"현재 총 {len(today_data)}명이 제출을 완료했습니다.")
                cols = st.columns(6)
                for i, row in enumerate(today_data.itertuples()):
                    cols[i % 6].info(f"✅ {row.이름}")
            else:
                st.info("아직 제출자가 없습니다.")
        except:
            st.warning("데이터를 불러올 수 없습니다.")

# --- [TAB 3] 통계 확인 ---
with tab3:
    st.header("📊 누적 성적 및 분석")
    try:
        data = conn.read()
        if not data.empty:
            data['제출시간'] = pd.to_datetime(data['제출시간'])
            # 중간고사 기간 설정 (예: 4월 20일)
            midterm_date = pd.Timestamp("2026-04-20")
            data['학기구분'] = data['제출시간'].apply(lambda x: '중간전' if x < midterm_date else '중간후')
            
            summary = data.groupby(['학번', '이름', '학기구분'])['총점'].mean().reset_index()
            summary['정답률(%)'] = (summary['총점'] / 7 * 100).round(1)
            
            st.subheader("학생별 평균 정답률")
            st.dataframe(summary)
            
            st.divider()
            st.subheader("문항별 정답 현황")
            for i in range(1, 8):
                correct_n = len(data[data[f"q{i}_결과"] == "O"])
                st.write(f"{i}번 문제 정답자: {correct_n}명 / 전체: {len(data)}명")
        else:
            st.write("데이터가 아직 없습니다.")
    except:
        st.write("데이터 연결 확인이 필요합니다.")