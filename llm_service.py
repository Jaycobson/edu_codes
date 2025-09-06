import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import streamlit as st
import re # Import the regular expression module

load_dotenv()


class LLMService:
    def __init__(self, model_name="gemini-2.5-flash-lite"): # Updated model name
        api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        print(f"INFO: Successfully initialized model: {self.model.model_name}")


    def generate_quiz_questions(self, topic: str, num_questions: int = 5) -> list:
        # Validate num_questions
        # if num_questions < 1:
        #     num_questions = 5
        # elif num_questions > 20:
        #     num_questions = 20
        
        # Create examples based on the number of questions requested
        example_questions = [
            {
                "question": "What is the capital of France?",
                "options": ["London", "Paris", "Rome", "Berlin"],
                "correct_answer": "Paris",
                "explanation": "Paris is the largest city and capital of France, known for its art, fashion, and culture."
            },
            {
                "question": "Which planet is known as the Red Planet?",
                "options": ["Earth", "Mars", "Jupiter", "Venus"],
                "correct_answer": "Mars",
                "explanation": "Mars is often called the Red Planet due to its reddish appearance, caused by iron oxide on its surface."
            },
            {
                "question": "Who painted the Mona Lisa?",
                "options": ["Vincent van Gogh", "Pablo Picasso", "Leonardo da Vinci", "Claude Monet"],
                "correct_answer": "Leonardo da Vinci",
                "explanation": "Leonardo da Vinci was an Italian polymath, who created the Mona Lisa, one of the most famous paintings in the world."
            },
            {
                "question": "What is the largest ocean on Earth?",
                "options": ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean", "Pacific Ocean"],
                "correct_answer": "Pacific Ocean",
                "explanation": "The Pacific Ocean is the largest and deepest of Earth's oceanic divisions, covering about a third of the surface."
            },
            {
                "question": "Which of these is a primate?",
                "options": ["Bear", "Elephant", "Monkey", "Kangaroo"],
                "correct_answer": "Monkey",
                "explanation": "Monkeys are a diverse group of primates, typically having tails and living in trees or on the ground."
            }
        ]
        
        # Use only the number of examples needed (or all if fewer than requested)
        examples_to_show = example_questions[:min(num_questions, len(example_questions))]
        examples_json = json.dumps(examples_to_show, indent=4)
        
        prompt = f"""
        Generate exactly {num_questions} multiple-choice questions about "{topic}".
        Each question should have 4 options and clearly indicate the correct answer.
        Also, provide a concise explanation for the correct answer.

        Make sure the questions are:
        - Relevant to the topic "{topic}"
        - Vary in difficulty (mix of easy, medium, and challenging)
        - Clear and unambiguous
        - Have only one correct answer among the 4 options

        Format the output exclusively as a JSON array of objects, like this example:
        {examples_json}

        IMPORTANT: 
        - Generate exactly {num_questions} questions
        - DO NOT include any conversational text or markdown formatting outside the JSON itself
        - Ensure the JSON is valid and properly formatted
        - Each question must be unique and relevant to "{topic}"
        """
        
        try:
            response = self.model.generate_content(prompt)
            raw_response_text = response.text
            print(f"DEBUG: Raw LLM response text:\n{raw_response_text}\n---")

            # Use regex to find the first JSON array in the text
            # This handles cases where the LLM might include markdown like ```json ... ```
            # or some introductory text.
            json_match = re.search(r'\[\s*{.*}\s*(?:,\s*{.*}\s*)*\]', raw_response_text, re.DOTALL)
            
            if json_match:
                json_string = json_match.group(0)
                # Sometimes the LLM might generate invalid JSON, like trailing commas
                # A common fix is to remove trailing commas before the closing bracket if they exist
                json_string = re.sub(r',\s*\]', ']', json_string)
                
                questions_data = json.loads(json_string)
                
                # Validate that we got the expected number of questions
                if len(questions_data) != num_questions:
                    print(f"WARNING: Expected {num_questions} questions but got {len(questions_data)}")
                    # If we got more than expected, trim to the requested number
                    if len(questions_data) > num_questions:
                        questions_data = questions_data[:num_questions]
                
                # Validate question structure
                validated_questions = []
                for i, q in enumerate(questions_data):
                    try:
                        # Check required fields
                        required_fields = ['question', 'options', 'correct_answer', 'explanation']
                        if all(field in q for field in required_fields):
                            # Validate options format
                            if isinstance(q['options'], list) and len(q['options']) == 4:
                                # Ensure correct_answer is in options
                                if q['correct_answer'] in q['options']:
                                    validated_questions.append(q)
                                else:
                                    print(f"WARNING: Question {i+1} correct answer not in options. Skipping.")
                            else:
                                print(f"WARNING: Question {i+1} doesn't have 4 options. Skipping.")
                        else:
                            print(f"WARNING: Question {i+1} missing required fields. Skipping.")
                    except Exception as e:
                        print(f"WARNING: Error validating question {i+1}: {e}")
                
                return validated_questions
            else:
                print("ERROR: No valid JSON array found in LLM response.")
                return []

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from LLM response: {e}")
            print(f"Problematic response text was:\n{raw_response_text}")
            return []
        except Exception as e:
            print(f"Error generating questions: {e}")
            return []

# Example of how to use (for testing)
if __name__ == "__main__":
    llm = LLMService()
    if llm.model:
        # Test with different numbers of questions
        for num_q in [3, 5, 7]:
            print(f"\n=== Testing with {num_q} questions ===")
            questions = llm.generate_quiz_questions("Nigeria", num_questions=num_q)
            if questions:
                print(f"Successfully generated {len(questions)} questions:")
                for i, q in enumerate(questions, 1):
                    print(f"\nQ{i}: {q['question']}")
                    print(f"Options: {q['options']}")
                    print(f"Correct: {q['correct_answer']}")
                    print(f"Explanation: {q['explanation']}")
            else:
                print("No questions generated. Check logs for errors.")
    else:
        print("LLMService failed to initialize. Cannot generate questions.")