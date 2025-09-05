class QuizManager:
    def __init__(self):
        self.questions = []
        self.current_question_index = 0
        self.user_answers = [] # Stores {'question_text', 'chosen_option', 'is_correct', 'explanation'}
        self.score = 0
        self.quiz_started = False

    def load_questions(self, questions_data: list):
        self.questions = questions_data
        self.current_question_index = 0
        self.user_answers = []
        self.score = 0
        self.quiz_started = True

    def get_current_question(self):
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None

    def submit_answer(self, chosen_option: str):
        if not self.questions:
            return None, None # No questions loaded

        current_q = self.get_current_question()
        if not current_q:
            return None, None

        correct_answer = current_q['correct_answer']
        is_correct = (chosen_option == correct_answer)

        if is_correct:
            self.score += 1

        self.user_answers.append({
            "question": current_q['question'],
            "options": current_q['options'],
            "chosen_answer": chosen_option,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": current_q['explanation']
        })

        self.current_question_index += 1
        return is_correct, current_q['explanation']

    def is_quiz_finished(self) -> bool:
        return self.current_question_index >= len(self.questions)

    def get_score_summary(self):
        total_questions = len(self.questions)
        correct_count = self.score
        incorrect_count = total_questions - self.score
        return total_questions, correct_count, incorrect_count

    def reset_quiz(self):
        self.questions = []
        self.current_question_index = 0
        self.user_answers = []
        self.score = 0
        self.quiz_started = False