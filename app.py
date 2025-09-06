import streamlit as st
from llm_service import LLMService
from quiz_logic import QuizManager
from ui_components import (
    display_question, display_feedback, display_progress_bar,
    display_score_summary, display_pie_chart
)
from file_exporter import export_to_csv, export_to_docx
import warnings
warnings.filterwarnings('ignore', message='.*ScriptRunContext.*')

# Initialize services (can be cached for performance)
@st.cache_resource
def get_llm_service():
    return LLMService()

@st.cache_resource
def get_quiz_manager():
    return QuizManager()

def initialize_session_state():
    """Initialize all session state variables"""
    default_values = {
        'quiz_started': False,
        'feedback_shown': False,
        'selected_option': None,
        'answer_submitted': False,
        'show_next_button': False,
        'current_topic': '',
        'quiz_topic': '',
        'num_questions': 5  # Default number of questions
    }
    
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_quiz_state():
    """Reset quiz-related session states"""
    keys_to_reset = [
        'quiz_started', 'feedback_shown', 'selected_option', 
        'answer_submitted', 'show_next_button', 'current_topic'
    ]
    for key in keys_to_reset:
        if key in st.session_state:
            st.session_state[key] = False if 'button' in key or key.endswith('_shown') or key.endswith('_started') else None
    
    if 'current_topic' in st.session_state:
        st.session_state.current_topic = ''

def calculate_progress(quiz_manager):
    """Calculate progress based on answered questions, not current question index"""
    if not hasattr(quiz_manager, 'questions') or not quiz_manager.questions:
        return 0.0
    
    total_questions = len(quiz_manager.questions)
    answered_questions = len(quiz_manager.user_answers) if hasattr(quiz_manager, 'user_answers') else 0
    
    # Progress is based on answered questions, not current position
    progress = answered_questions / total_questions
    
    # Ensure progress is within [0.0, 1.0] range
    return max(0.0, min(1.0, progress))

def get_answer_value(answer, key_options):
    """Safely get answer value from different possible key names"""
    for key in key_options:
        if key in answer:
            return answer[key]
    return "N/A"  # Fallback if no key is found

def generate_questions_safely(llm_service, topic, num_questions):
    """Safely generate questions with fallback for different method signatures"""
    try:
        # Method 1: Try with keyword arguments (preferred method)
        return llm_service.generate_quiz_questions(topic=topic, num_questions=num_questions)
    except TypeError as e:
        if "unexpected keyword argument" in str(e):
            try:
                # Method 2: Try with positional arguments
                return llm_service.generate_quiz_questions(topic, num_questions)
            except TypeError as e2:
                # Check what parameters the method actually accepts
                import inspect
                sig = inspect.signature(llm_service.generate_quiz_questions)
                params = list(sig.parameters.keys())
                
                if len(params) == 1:
                    # Method only accepts topic, generate with topic only then truncate/extend
                    st.warning(f"⚠️ LLM Service only accepts topic parameter. Requesting {num_questions} questions but may get default amount.")
                    questions = llm_service.generate_quiz_questions(topic)
                    
                    if questions and len(questions) != num_questions:
                        if len(questions) > num_questions:
                            # Truncate to requested number
                            st.info(f"📝 Truncated to {num_questions} questions as requested.")
                            return questions[:num_questions]
                        else:
                            # We got fewer questions than requested
                            st.warning(f"⚠️ Only {len(questions)} questions generated (requested {num_questions}).")
                            return questions
                    return questions
                else:
                    # Re-raise the error if we can't handle it
                    raise e2
        else:
            # Re-raise if it's a different TypeError
            raise e
    except Exception as e:
        st.error(f"❌ Unexpected error generating questions: {e}")
        return None

def clear_cache_and_restart():
    """Clear Streamlit cache and force restart"""
    st.cache_resource.clear()
    st.rerun()

def generate_questions_with_retry(llm_service, topic, num_questions, max_retries=3):
    """Generate questions with retry logic and better error handling"""
    for attempt in range(max_retries):
        try:
            questions = generate_questions_safely(llm_service, topic, num_questions)
            
            if questions:
                # Validate we got the right number of questions
                if len(questions) == num_questions:
                    return questions
                elif len(questions) > num_questions:
                    st.info(f"📝 Generated {len(questions)} questions, using first {num_questions} as requested.")
                    return questions[:num_questions]
                else:
                    st.warning(f"⚠️ Generated {len(questions)} questions (requested {num_questions}). Using what was generated.")
                    return questions
            else:
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ Attempt {attempt + 1} failed, retrying...")
                    continue
                else:
                    st.error("❌ Failed to generate questions after multiple attempts.")
                    return None
                    
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"⚠️ Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                continue
            else:
                st.error(f"❌ Failed to generate questions after {max_retries} attempts: {str(e)}")
                return None
    
    return None

def main():
    # Configure page
    st.set_page_config(
        page_title="QuizMaster by Jaycobson",
        # page_icon="🧠",
        # layout="wide",
        # initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize services
    try:
        llm_service = get_llm_service()
        quiz_manager = get_quiz_manager()
    except Exception as e:
        st.error(f"Failed to initialize services: {e}")
        if st.button("🔄 Clear Cache and Restart"):
            clear_cache_and_restart()
        st.stop()
    
    # Compact Header
    st.markdown("""
    <div style='text-align: center; margin-bottom: 1rem;'>
        <h1> 🎯 QuizMaster </h1>
        <p style='margin: 0; color: #666;'><strong>AI-Powered Interactive Quiz Generation</strong> | <em>Created by jaycobson</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Quiz Controls")
        
        if st.button("🔄 Start New Quiz", use_container_width=True, type="secondary"):
            quiz_manager.reset_quiz()
            reset_quiz_state()
            st.rerun()
        

        st.divider()
        
        # Quiz Progress (only show if quiz is active)
        if st.session_state.quiz_started and hasattr(quiz_manager, 'questions'):
            st.subheader("📊 Progress")
            
            # Fixed progress calculation
            progress = calculate_progress(quiz_manager)
            st.progress(progress)
            
            # Progress text based on answered questions
            answered_count = len(quiz_manager.user_answers) if hasattr(quiz_manager, 'user_answers') else 0
            total_count = len(quiz_manager.questions)
            current_q_num = quiz_manager.current_question_index + 1
            
            if current_q_num > total_count:
                current_q_num = total_count

            st.write(f"Question {current_q_num} of {total_count}")
            st.write(f"Answered: {answered_count}/{total_count}")
            
            if hasattr(quiz_manager, 'user_answers') and quiz_manager.user_answers:
                correct_answers = sum(1 for answer in quiz_manager.user_answers if answer.get('is_correct', False))
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("✅ Correct", correct_answers)
                with col2:
                    st.metric("📝 Answered", len(quiz_manager.user_answers))
            
            st.divider()
        
        # About section
        with st.expander("ℹ️ About"):
            st.write("This quiz app uses AI to generate personalized questions on any topic you choose.")
            st.write("Perfect for studying, testing knowledge, or just having fun!")
    
    # --- Main Content Area ---
    
    # Step 1: Topic Selection
    if not st.session_state.quiz_started:
        # Center the topic selection
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.subheader("🎯 Choose Your Quiz Topic")
            
            # Topic input
            topic_input = st.text_input(
                "Enter a topic you'd like to be quizzed on:",
                placeholder="e.g. Python Programming, World History, Physics, Machine Learning...",
                help="Be specific but not too narrow! Examples: 'JavaScript Functions', 'Renaissance Art', 'Cell Biology'"
            )
            
            # Number of questions selector - with more options
            st.session_state.num_questions = st.selectbox(
                "Number of questions:",
                options=[3, 5, 7, 10, 15, 20, 25, 30],
                index=1,  # Default to 5 questions
                help="Choose how many questions you want in your quiz"
            )
            
            # Generate button
            st.write("")  # Add spacing
            if st.button(f"🚀 Generate {st.session_state.num_questions} Questions", use_container_width=True, type="primary"):
                if topic_input.strip():
                    st.session_state.current_topic = topic_input.strip()
                    
                    with st.spinner(f"🔮 Creating {st.session_state.num_questions} questions about '{st.session_state.current_topic}'..."):
                        try:
                            # Debug: Check if llm_service has the method
                            if not hasattr(llm_service, 'generate_quiz_questions'):
                                st.error("❌ LLM Service not properly initialized. Please restart the app.")
                                st.stop()
                            
                            # Use the improved generation function with retry logic
                            questions_data = generate_questions_with_retry(
                                llm_service, 
                                st.session_state.current_topic, 
                                st.session_state.num_questions
                            )
                            
                            if questions_data and len(questions_data) > 0:
                                quiz_manager.load_questions(questions_data)
                                st.session_state.quiz_started = True
                                reset_quiz_state()
                                st.session_state.quiz_started = True  # Set back to True
                                st.success(f"✨ {len(questions_data)} questions generated successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to generate questions. Please try a different topic or check your connection.")
                        except Exception as e:
                            st.error(f"❌ Error generating questions: {str(e)}")
                            st.write("Debug info:", type(e).__name__)
                            # Offer to clear cache
                            if st.button("🔄 Clear Cache and Try Again"):
                                clear_cache_and_restart()
                else:
                    st.warning("⚠️ Please enter a topic first.")
        
        # Popular topics section - more compact
        st.write("")
        
        with st.expander("💡 Or Choose a Popular Topic", expanded=False):
            example_topics = [
                ("🤖", "Artificial Intelligence"), ("🌍", "Climate Change"), 
                ("🚀", "Space Exploration"), ("📚", "Literature"), 
                ("⚛️", "Physics"), ("💻", "Programming")
            ]
            
            # Display topic buttons in rows of 3
            for i in range(0, len(example_topics), 3):
                cols = st.columns(3)
                for j, (icon, topic) in enumerate(example_topics[i:i+3]):
                    with cols[j]:
                        if st.button(f"{icon} {topic}", use_container_width=True, key=f"topic_{i+j}"):
                            st.session_state.current_topic = topic
                            
                            with st.spinner(f"🔮 Creating {st.session_state.num_questions} questions about '{topic}'..."):
                                try:
                                    # Use the improved generation function with retry logic
                                    questions_data = generate_questions_with_retry(
                                        llm_service, 
                                        topic, 
                                        st.session_state.num_questions
                                    )
                                    
                                    if questions_data and len(questions_data) > 0:
                                        quiz_manager.load_questions(questions_data)
                                        st.session_state.quiz_started = True
                                        reset_quiz_state()
                                        st.session_state.quiz_started = True
                                        st.success(f"✨ {len(questions_data)} questions generated successfully!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to generate questions. Please try again.")
                                except Exception as e:
                                    st.error(f"❌ Error generating questions: {str(e)}")
                                    if st.button(f"🔄 Clear Cache and Try Again", key=f"clear_cache_{i+j}"):
                                        clear_cache_and_restart()
    
    # Step 2: Quiz Questions
    elif st.session_state.quiz_started and not quiz_manager.is_quiz_finished():
        current_question = quiz_manager.get_current_question()
        
        if current_question:
            # Question header with progress
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"📝 Question {quiz_manager.current_question_index + 1}")
                st.caption(f"Topic: {st.session_state.current_topic}")
            with col2:
                # Fixed progress percentage calculation
                progress_pct = calculate_progress(quiz_manager)
                st.metric("Progress", f"{int(progress_pct * 100)}%")
            
            st.write("")
            
            # Question container
            with st.container():
                # Display question
                st.markdown(f"### {current_question['question']}")
                st.write("")
                
                # Answer options
                if not st.session_state.answer_submitted:
                    selected = st.radio(
                        "**Select your answer:**",
                        current_question['options'],
                        key=f"q_{quiz_manager.current_question_index}",
                        index=None
                    )
                    st.session_state.selected_option = selected
                else:
                    # Show the submitted answer
                    if st.session_state.selected_option:
                        try:
                            selected_index = current_question['options'].index(st.session_state.selected_option)
                        except ValueError:
                            # If exact match not found, find the closest match or default to None
                            selected_index = None
                            for i, option in enumerate(current_question['options']):
                                if option.strip() == st.session_state.selected_option.strip():
                                    selected_index = i
                                    break
                        
                        st.radio(
                            "**Your answer:**",
                            current_question['options'],
                            index=selected_index,
                            disabled=True,
                            key=f"q_{quiz_manager.current_question_index}_disabled"
                        )
                        
                        # Show what was actually selected
                        if selected_index is None:
                            st.caption(f"Selected: {st.session_state.selected_option}")
                    else:
                        st.info("No answer was submitted for this question.")
            
            st.write("")
            
            # Submit button (only when answer not submitted)
            if not st.session_state.answer_submitted:
                col1, col2, col3 = st.columns([2, 1, 2])
                with col2:
                    if st.button("✅ Submit", use_container_width=True, type="primary"):
                        if st.session_state.selected_option:
                            is_correct, explanation = quiz_manager.submit_answer(st.session_state.selected_option)
                            st.session_state.feedback_shown = True
                            st.session_state.last_feedback_is_correct = is_correct
                            st.session_state.last_feedback_explanation = explanation
                            st.session_state.answer_submitted = True
                            st.rerun()
                        else:
                            st.warning("⚠️ Please select an answer first.")
            
            # Show feedback after submission (prominently displayed)
            if st.session_state.feedback_shown:
                st.write("")
                # Create a prominent feedback section
                if st.session_state.last_feedback_is_correct:
                    st.success(f"🎉 **Correct!**\n\n{st.session_state.last_feedback_explanation}")
                else:
                    st.error(f"❌ **Incorrect!**\n\n{st.session_state.last_feedback_explanation}")
                
                # Next button appears after feedback is shown
                st.write("")
                col1, col2, col3 = st.columns([2, 1, 2])
                with col2:
                    if not quiz_manager.is_quiz_finished():
                        if st.button("➡️ Next Question", use_container_width=True, type="secondary"):
                            # Clear feedback states to show the next question
                            # (QuizManager already advanced to next question in submit_answer)
                            st.session_state.selected_option = None
                            st.session_state.answer_submitted = False
                            st.session_state.feedback_shown = False
                            st.rerun()
                    else:
                        if st.button("🏆 View Results", use_container_width=True, type="primary"):
                            st.rerun()
    
    # Step 3: Results
    elif quiz_manager.is_quiz_finished() and st.session_state.quiz_started:
        total, correct, incorrect = quiz_manager.get_score_summary()
        percentage = round((correct / total) * 100) if total > 0 else 0
        
        # Results header
        st.subheader("🏆 Quiz Results")
        st.caption(f"Topic: {st.session_state.current_topic}")
        
        # Score metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Score", f"{percentage}%")
        with col2:
            st.metric("✅ Correct", correct)
        with col3:
            st.metric("❌ Incorrect", incorrect)
        with col4:
            st.metric("📝 Total", total)
        
        st.write("")
        
        # Performance message
        if percentage >= 90:
            st.success("🌟 **Outstanding!** You're clearly an expert on this topic!")
        elif percentage >= 70:
            st.success("👏 **Great job!** You have a solid understanding!")
        elif percentage >= 50:
            st.info("👍 **Good effort!** A bit more study and you'll master this!")
        else:
            st.info("📚 **Keep learning!** Everyone starts somewhere - practice makes perfect!")
        
        st.divider()
        
        # Detailed results
        with st.expander("📋 **View Detailed Results**"):
            for i, answer in enumerate(quiz_manager.user_answers):
                st.subheader(f"Question {i+1} {'✅' if answer.get('is_correct', False) else '❌'}")
                st.write(f"**Q:** {answer.get('question', 'Question not available')}")
                
                # Handle different possible key names for user's selected answer
                user_answer = get_answer_value(answer, ['selected_option', 'user_answer', 'selected', 'answer'])
                st.write(f"**Your answer:** {user_answer}")
                
                # Handle different possible key names for correct answer
                correct_answer = get_answer_value(answer, ['correct_answer', 'correct_option', 'correct'])
                st.write(f"**Correct answer:** {correct_answer}")
                
                # Handle explanation
                explanation = answer.get('explanation', 'No explanation available')
                st.write(f"**Explanation:** {explanation}")
                
                if i < len(quiz_manager.user_answers) - 1:
                    st.divider()
        
        st.divider()
        
        # Download section
        st.subheader("📥 Download Results")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            csv_data = export_to_csv(quiz_manager.user_answers)
            st.download_button(
                "📊 CSV File",
                data=csv_data,
                file_name=f"quiz_{st.session_state.current_topic.replace(' ', '_').lower()}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            docx_data = export_to_docx(quiz_manager.user_answers)
            st.download_button(
                "📄 Word Doc",
                data=docx_data,
                file_name=f"quiz_{st.session_state.current_topic.replace(' ', '_').lower()}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        
        with col3:
            if st.button("🔄 New Quiz", use_container_width=True, type="primary"):
                quiz_manager.reset_quiz()
                reset_quiz_state()
                st.rerun()

if __name__ == "__main__":
    main()