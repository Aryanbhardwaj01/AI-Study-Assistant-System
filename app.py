import json
import time
import streamlit as st
from openai import OpenAI
from database import create_tables, save_student, save_score, get_leaderboard

client = OpenAI(
    api_key="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",
    base_url="https://api.groq.com/openai/v1"
)

st.set_page_config(
    page_title="AI Study Assistant Ultra",
    page_icon="🚀",
    layout="wide"
)

create_tables()

default_state = {
    "page": "student",
    "student_name": "",
    "branch": "",
    "topic": "",
    "generated_notes": "",
    "quiz_data": [],
    "score": 0,
    "total": 0,
    "show_answers": False,
    "current_question": 0,
    "user_answers": {},
    "quiz_start_time": None,
    "quiz_duration": 180,
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at top left, rgba(56,189,248,0.18), transparent 25%),
        radial-gradient(circle at top right, rgba(99,102,241,0.20), transparent 30%),
        linear-gradient(135deg, #020617, #0f172a 45%, #111827);
    color: white;
}
.block-container {
    max-width: 1280px;
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
.main-title {
    font-size: 3.3rem;
    font-weight: 800;
    text-align: center;
    color: white;
    margin-bottom: 0.2rem;
}
.sub-title {
    text-align: center;
    font-size: 1.05rem;
    color: #cbd5e1;
    margin-bottom: 1.4rem;
}
.glass-card {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 22px;
    padding: 24px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.28);
    margin-bottom: 18px;
}
.section-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: white;
    margin-bottom: 8px;
}
.muted {
    color: #cbd5e1;
    font-size: 0.98rem;
}
.metric-pill {
    display: inline-block;
    padding: 10px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    color: white;
    font-size: 0.92rem;
    margin-right: 8px;
    margin-bottom: 8px;
}
.question-box {
    padding: 18px;
    border-radius: 18px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    margin-bottom: 14px;
}
.review-box {
    padding: 16px;
    border-radius: 16px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    margin-bottom: 12px;
}
.timer-box {
    padding: 12px 16px;
    border-radius: 14px;
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.30);
    color: white;
    font-weight: 700;
    text-align: center;
    margin-bottom: 14px;
}
.result-box {
    padding: 18px;
    border-radius: 18px;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.10);
    margin-top: 10px;
}
div.stButton > button {
    width: 100%;
    height: 3.1em;
    border-radius: 14px;
    border: none;
    font-size: 16px;
    font-weight: 700;
    color: white;
    background: linear-gradient(90deg, #38bdf8, #6366f1);
}
div.stButton > button:hover {
    color: white;
}
div[data-testid="stTextInput"] input {
    border-radius: 12px;
}
div[data-testid="stRadio"] label {
    color: white !important;
}
[data-testid="stSidebar"] {
    background: rgba(2, 6, 23, 0.92);
}
.sidebar-title {
    color: white;
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

def reset_app():
    for key, value in default_state.items():
        st.session_state[key] = value

def reset_quiz_only():
    st.session_state.quiz_data = []
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.show_answers = False
    st.session_state.current_question = 0
    st.session_state.user_answers = {}
    st.session_state.quiz_start_time = None

def get_step_number():
    page_map = {
        "student": 1,
        "topic": 2,
        "quiz": 3,
        "result": 4,
    }
    return page_map.get(st.session_state.page, 1)

def generate_notes(topic):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are an expert teacher. Generate simple, clean, exam-friendly notes with headings, bullet points, and short explanations."
            },
            {
                "role": "user",
                "content": f"Create high-quality study notes on: {topic}"
            }
        ]
    )
    return response.choices[0].message.content

def generate_quiz(topic):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "Create exactly 5 multiple choice questions in valid JSON only. "
                    "Return a JSON array. Each object must contain: "
                    "'question' (string), "
                    "'options' (array of exactly 4 strings), "
                    "'answer' (string matching one option exactly). "
                    "No markdown. No explanation. JSON only."
                )
            },
            {
                "role": "user",
                "content": f"Generate a quiz for this topic: {topic}"
            }
        ]
    )

    raw_text = response.choices[0].message.content.strip()

    try:
        return json.loads(raw_text)
    except Exception:
        pass

    try:
        cleaned = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception:
        return []

def submit_quiz():
    score = 0
    total = len(st.session_state.quiz_data)

    for i, q in enumerate(st.session_state.quiz_data):
        selected = st.session_state.user_answers.get(i, "").strip()
        correct = q["answer"].strip()
        if selected == correct:
            score += 1

    st.session_state.score = score
    st.session_state.total = total
    st.session_state.show_answers = True

    save_score(
        st.session_state.student_name,
        st.session_state.branch,
        st.session_state.topic,
        score,
        total
    )

    st.session_state.page = "result"
    st.rerun()

with st.sidebar:
    st.markdown('<div class="sidebar-title">📍 App Progress</div>', unsafe_allow_html=True)
    st.progress(get_step_number() / 4)

    steps = [
        ("1", "Student Details"),
        ("2", "Topic Selection"),
        ("3", "Quiz Attempt"),
        ("4", "Final Result"),
    ]

    for number, label in steps:
        current = get_step_number()
        n = int(number)
        status = "✅" if n < current else ("🔵" if n == current else "⚪")
        st.write(f"{status} Step {number}: {label}")

    st.markdown("---")
    st.write(f"**Student:** {st.session_state.student_name or 'Not set'}")
    st.write(f"**Branch:** {st.session_state.branch or 'Not set'}")
    st.write(f"**Topic:** {st.session_state.topic or 'Not selected'}")

    if st.button("🔄 Reset App"):
        reset_app()
        st.rerun()

st.markdown('<div class="main-title">🚀 AI Study Assistant Ultra</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Notes • Timed Quiz • Review • Leaderboard</div>', unsafe_allow_html=True)

if st.session_state.page == "student":
    st.markdown("""
    <div class="glass-card">
        <div class="section-title">Welcome to the Ultra Study Dashboard</div>
        <div class="muted">
            Enter your details, choose a topic, generate notes, attempt a timed quiz,
            and review your performance like a premium learning app.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1.15, 0.85])

    with c1:
        st.markdown("""
        <div class="glass-card">
            <div class="section-title">Student Details</div>
            <div class="muted">Fill in your information to continue.</div>
        </div>
        """, unsafe_allow_html=True)

        name = st.text_input("Enter your full name")
        branch = st.text_input("Enter your branch")

        if st.button("Continue to Topic Selection"):
            if name.strip() and branch.strip():
                st.session_state.student_name = name.strip()
                st.session_state.branch = branch.strip()
                save_student(name.strip(), branch.strip())
                st.session_state.page = "topic"
                st.rerun()
            else:
                st.error("Please fill in both name and branch.")

    with c2:
        st.markdown("""
        <div class="glass-card">
            <div class="section-title">Premium Features</div>
            <div class="muted">
                • AI notes generation<br>
                • Timed one-by-one MCQ quiz<br>
                • Instant scoring<br>
                • Full answer review<br>
                • Leaderboard tracking
            </div>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.page == "topic":
    st.markdown(f"""
    <div class="glass-card">
        <div class="section-title">Hello, {st.session_state.student_name}</div>
        <div class="muted">Choose a topic, revise notes, and then start your quiz.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f"""
        <span class="metric-pill">👤 {st.session_state.student_name}</span>
        <span class="metric-pill">🎓 {st.session_state.branch}</span>
        """,
        unsafe_allow_html=True
    )

    topic = st.text_input(
        "Enter your study topic",
        value=st.session_state.topic,
        placeholder="Example: Artificial Intelligence"
    )

    b1, b2, b3 = st.columns(3)

    with b1:
        if st.button("Generate Notes"):
            if topic.strip():
                st.session_state.topic = topic.strip()
                with st.spinner("Generating notes..."):
                    try:
                        st.session_state.generated_notes = generate_notes(topic.strip())
                    except Exception as e:
                        st.error(f"Error generating notes: {e}")
            else:
                st.warning("Please enter a topic first.")

    with b2:
        if st.button("Start Timed Quiz"):
            if topic.strip():
                st.session_state.topic = topic.strip()
                with st.spinner("Creating quiz..."):
                    try:
                        quiz_data = generate_quiz(topic.strip())
                        if quiz_data and isinstance(quiz_data, list):
                            reset_quiz_only()
                            st.session_state.quiz_data = quiz_data
                            st.session_state.quiz_start_time = time.time()
                            st.session_state.page = "quiz"
                            st.rerun()
                        else:
                            st.error("Quiz could not be generated. Please try again.")
                    except Exception as e:
                        st.error(f"Error generating quiz: {e}")
            else:
                st.warning("Please enter a topic first.")

    with b3:
        if st.button("Back to Student Page"):
            st.session_state.page = "student"
            st.rerun()

    if st.session_state.generated_notes:
        st.markdown("""
        <div class="glass-card">
            <div class="section-title">Generated Notes</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("View Notes", expanded=True):
            st.write(st.session_state.generated_notes)

elif st.session_state.page == "quiz":
    if not st.session_state.quiz_data:
        st.error("No quiz data found. Please go back and generate the quiz again.")
        if st.button("Go Back"):
            st.session_state.page = "topic"
            st.rerun()
    else:
        total_questions = len(st.session_state.quiz_data)
        current_index = st.session_state.current_question

        elapsed = 0
        if st.session_state.quiz_start_time:
            elapsed = int(time.time() - st.session_state.quiz_start_time)

        remaining = max(st.session_state.quiz_duration - elapsed, 0)
        minutes = remaining // 60
        seconds = remaining % 60

        if remaining == 0:
            st.warning("Time is over. Your quiz has been auto-submitted.")
            submit_quiz()

        progress_value = (current_index + 1) / total_questions

        st.markdown(f"""
        <div class="glass-card">
            <div class="section-title">Timed Quiz Dashboard</div>
            <div class="muted">Topic: {st.session_state.topic}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="timer-box">⏳ Time Left: {minutes:02d}:{seconds:02d}</div>', unsafe_allow_html=True)
        st.progress(progress_value)
        st.write(f"**Question {current_index + 1} of {total_questions}**")

        q = st.session_state.quiz_data[current_index]
        saved_answer = st.session_state.user_answers.get(current_index)

        st.markdown('<div class="question-box">', unsafe_allow_html=True)
        st.markdown(f"### {q['question']}")

        selected = st.radio(
            "Choose your answer",
            q["options"],
            index=q["options"].index(saved_answer) if saved_answer in q["options"] else 0,
            key=f"radio_{current_index}"
        )

        st.session_state.user_answers[current_index] = selected
        st.markdown('</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button("Previous"):
                if current_index > 0:
                    st.session_state.current_question -= 1
                    st.rerun()

        with c2:
            if current_index < total_questions - 1:
                if st.button("Next Question"):
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                if st.button("Submit Quiz"):
                    submit_quiz()

        with c3:
            if st.button("Back to Topic"):
                st.session_state.page = "topic"
                st.rerun()

elif st.session_state.page == "result":
    percentage = 0
    if st.session_state.total > 0:
        percentage = round((st.session_state.score / st.session_state.total) * 100)

    st.markdown("""
    <div class="glass-card">
        <div class="section-title">Final Result</div>
        <div class="muted">Your timed quiz has been completed successfully.</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Score", f"{st.session_state.score}/{st.session_state.total}")
    c2.metric("Percentage", f"{percentage}%")
    c3.metric("Topic", st.session_state.topic)

    if st.session_state.score == st.session_state.total:
        st.balloons()
        st.success("Outstanding performance! You answered everything correctly.")
    elif percentage >= 60:
        st.success("Great work! Your performance is strong.")
    else:
        st.warning("Good attempt. Review the notes and try again for a better score.")

    st.markdown("""
    <div class="result-box">
        <b>Performance Insight:</b><br>
    </div>
    """, unsafe_allow_html=True)

    if percentage >= 80:
        st.write("You have a strong understanding of this topic.")
    elif percentage >= 50:
        st.write("You understand the basics, but revision can improve your result.")
    else:
        st.write("You should revise the notes once more before reattempting this topic.")

    if st.session_state.show_answers:
        st.markdown("### ✅ Answer Review")
        for i, q in enumerate(st.session_state.quiz_data):
            selected = st.session_state.user_answers.get(i, "Not answered")
            correct = q["answer"]

            st.markdown('<div class="review-box">', unsafe_allow_html=True)
            st.markdown(f"**Q{i + 1}. {q['question']}**")
            st.write(f"**Your Answer:** {selected}")
            st.write(f"**Correct Answer:** {correct}")

            if selected == correct:
                st.success("Correct")
            else:
                st.error("Incorrect")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 🏆 Leaderboard")
    leaderboard = get_leaderboard()

    if leaderboard:
        for i, row in enumerate(leaderboard, start=1):
            student_name, branch_name, topic_name, score, total = row
            st.write(f"**{i}.** {student_name} | {branch_name} | {topic_name} | {score}/{total}")
    else:
        st.info("No quiz results found yet.")

    d1, d2 = st.columns(2)

    with d1:
        if st.button("Try Another Topic"):
            st.session_state.topic = ""
            st.session_state.generated_notes = ""
            reset_quiz_only()
            st.session_state.page = "topic"
            st.rerun()

    with d2:
        if st.button("Restart Full App"):
            reset_app()
            st.rerun()