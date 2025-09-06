
![App](image.png)

# QuizMaster

An AI-powered quiz generator that creates personalized multiple-choice questions on any topic using Google's Gemini AI.

## What it does

Simply enter any topic and QuizMaster will generate engaging quiz questions with explanations. Perfect for studying, testing knowledge, or just having fun learning something new.

**Key features:**
- Generate 3-30 questions on any subject
- Instant feedback with detailed explanations  
- Export results to CSV or Word documents
- Clean, responsive web interface
- Progress tracking and performance analytics

## Getting started

**Prerequisites:**
- Python 3.8+
- Google AI API key 

**Setup:**
```bash
git clone https://github.com/Jaycobson/topic_quiz_generator.git
cd topic_quiz_generator
pip install -r requirements.txt


**Run:**
```bash
streamlit run app.py
```

Open http://localhost:8501 and start creating quizzes!

## How it works

1. **Choose a topic** - Anything from "Python functions" to "Medieval history"
2. **Select question count** - Pick between 3-30 questions
3. **Take the quiz** - Answer questions with instant feedback
4. **Review results** - See detailed explanations and export your results

## Project structure

```
├── main.py              # Streamlit web app
├── llm_service.py       # Google AI integration
├── quiz_logic.py        # Quiz state management
├── ui_components.py     # Reusable UI elements
├── file_exporter.py     # CSV/Word export
└── requirements.txt     # Dependencies
```

## Built with

- **Streamlit** for the web interface
- **Google Gemini AI** for question generation
- **Python-docx** for Word document exports

## Contributing

Feel free to open issues or submit pull requests. This is a learning project and contributions are welcome!


*Created by jaycobson*