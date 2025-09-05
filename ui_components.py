import streamlit as st
import plotly.express as px
import pandas as pd

def display_question(question_data: dict, question_number: int, total_questions: int):
    st.header(f"Question {question_number + 1}/{total_questions}")
    st.subheader(question_data['question'])

    options = question_data['options']
    selected_option = st.radio(
        f"Choose an answer for Q{question_number + 1}",
        options,
        key=f"q{question_number}_radio"
    )
    return selected_option

def display_feedback(is_correct: bool, explanation: str):
    if is_correct:
        st.success("🎉 Correct!")
    else:
        st.error("❌ Incorrect!")
    st.info(f"**Explanation:** {explanation}")

def display_progress_bar(current_index: int, total_questions: int):
    progress_percentage = (current_index / total_questions)
    st.progress(progress_percentage, text=f"Progress: {current_index}/{total_questions} questions answered")

def display_score_summary(total: int, correct: int, incorrect: int):
    st.header("Quiz Complete!")
    st.subheader(f"Your Score: {correct}/{total}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Correct Answers", correct)
    with col2:
        st.metric("Incorrect Answers", incorrect)

def display_pie_chart(correct: int, incorrect: int):
    df = pd.DataFrame({
        'Category': ['Correct', 'Incorrect'],
        'Count': [correct, incorrect]
    })
    fig = px.pie(df, values='Count', names='Category',
                 title='Performance Breakdown',
                 color_discrete_map={'Correct': 'green', 'Incorrect': 'red'})
    st.plotly_chart(fig)