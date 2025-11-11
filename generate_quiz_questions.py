import pandas as pd
import json
from datetime import datetime
from collections import Counter, defaultdict
import google.generativeai as genai
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

class QuizQuestionGenerator:
    def __init__(self, csv_path=None, uploaded_file=None, api_key=None):
        # Support both file path and uploaded file object
        if uploaded_file is not None:
            self.df = pd.read_csv(uploaded_file)
        elif csv_path is not None:
            self.df = pd.read_csv(csv_path)
        else:
            raise ValueError("Either csv_path or uploaded_file must be provided")
        
        # Set default generation limits (accounting for filtering)
        self.comment_limit = 30
        self.scenario_limit = 40
        self.ai_advanced_limit = 40
        self.relationship_limit = 30
        
        self.prepare_data()
        
        # Use provided API key or environment variable
        gemini_key = api_key if api_key else GEMINI_API_KEY
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=0.7,
            google_api_key=gemini_key
        )
        
    def prepare_data(self):
        """Prepare and analyze the data"""
        # Parse dates
        self.df['Date Received'] = pd.to_datetime(self.df['Date Received'], format='%m/%d/%Y')
        self.df['Month'] = self.df['Date Received'].dt.month
        self.df['Year'] = self.df['Date Received'].dt.year
        self.df['Quarter'] = self.df['Date Received'].dt.quarter
        self.df['MonthName'] = self.df['Date Received'].dt.strftime('%B')
        
        # Clean data
        self.df['Award Amount'] = pd.to_numeric(self.df['Award Amount'], errors='coerce').fillna(0)
    
    def set_generation_limits(self, comment_questions=30, scenario_questions=40, 
                             ai_advanced_questions=40, relationship_questions=30):
        """Set limits for the number of questions to generate"""
        self.comment_limit = comment_questions
        self.scenario_limit = scenario_questions
        self.ai_advanced_limit = ai_advanced_questions
        self.relationship_limit = relationship_questions
        
    def analyze_data(self):
        """Analyze data to extract insights for question generation"""
        analysis = {
            'total_records': len(self.df),
            'unique_recipients': self.df['Recipient Name'].nunique(),
            'unique_givers': self.df['Giver Name'].nunique(),
            'unique_programs': self.df['Program Name'].nunique(),
            
            # Top recipients
            'top_recipients': self.df['Recipient Name'].value_counts().head(10).to_dict(),
            
            # Top givers
            'top_givers': self.df['Giver Name'].value_counts().head(10).to_dict(),
            
            # Award types
            'award_types': self.df['Award Type'].value_counts().to_dict(),
            
            # Programs
            'programs': self.df['Program Name'].value_counts().to_dict(),
            
            # Time-based analysis
            'monthly_distribution': self.df.groupby(['Year', 'MonthName']).size().to_dict(),
            'quarterly_distribution': self.df.groupby(['Year', 'Quarter']).size().to_dict(),
            
            # Award amount analysis
            'total_award_amount': self.df['Award Amount'].sum(),
            'avg_award_amount': self.df['Award Amount'].mean(),
            'top_earners': self.df.groupby('Recipient Name')['Award Amount'].sum().sort_values(ascending=False).head(10).to_dict(),
            
            # Unique giver-recipient pairs
            'unique_pairs': len(self.df[['Giver Name', 'Recipient Name']].drop_duplicates()),
        }
        
        # Most unique givers per recipient
        unique_givers_per_recipient = self.df.groupby('Recipient Name')['Giver Name'].nunique().sort_values(ascending=False)
        analysis['recipients_with_most_unique_givers'] = unique_givers_per_recipient.head(10).to_dict()
        
        # Consecutive months recipients
        recipients_by_month = self.df.groupby(['Recipient Name', 'Year', 'Month']).size().reset_index()
        analysis['recipients_all_q1_months'] = self._find_consecutive_months_recipients(recipients_by_month)
        
        return analysis
    
    def _find_consecutive_months_recipients(self, recipients_by_month):
        """Find recipients who received awards in consecutive months"""
        q1_2025 = recipients_by_month[(recipients_by_month['Year'] == 2025) & 
                                       (recipients_by_month['Month'].isin([1, 2, 3]))]
        
        recipient_months = q1_2025.groupby('Recipient Name')['Month'].apply(list).to_dict()
        consecutive = {}
        for name, months in recipient_months.items():
            if len(months) >= 2:
                consecutive[name] = sorted(months)
        return consecutive
    
    def generate_factual_questions(self, analysis):
        """Generate factual questions based on data analysis"""
        questions = []
        
        # Top recipient questions
        top_recipient = list(analysis['top_recipients'].keys())[0]
        top_recipient_count = analysis['top_recipients'][top_recipient]
        questions.append({
            'question': f"Who received the highest number of recognitions?",
            'answer': top_recipient,
            'category': 'Recognition Count'
        })
        
        questions.append({
            'question': f"How many recognitions did {top_recipient} receive?",
            'answer': str(top_recipient_count),
            'category': 'Recognition Count'
        })
        
        # Top giver questions
        top_giver = list(analysis['top_givers'].keys())[0]
        top_giver_count = analysis['top_givers'][top_giver]
        questions.append({
            'question': f"Who gave the highest number of recognitions?",
            'answer': top_giver,
            'category': 'Recognition Count'
        })
        
        questions.append({
            'question': f"How many recognitions did {top_giver} give?",
            'answer': str(top_giver_count),
            'category': 'Recognition Count'
        })
        
        # Unique givers per recipient
        top_unique = list(analysis['recipients_with_most_unique_givers'].keys())[0]
        unique_count = analysis['recipients_with_most_unique_givers'][top_unique]
        questions.append({
            'question': f"Which recipient has the most unique givers?",
            'answer': top_unique,
            'category': 'Unique Relationships'
        })
        
        questions.append({
            'question': f"How many unique givers did {top_unique} receive recognitions from?",
            'answer': str(unique_count),
            'category': 'Unique Relationships'
        })
        
        # Award amount questions
        top_earner = list(analysis['top_earners'].keys())[0]
        top_amount = analysis['top_earners'][top_earner]
        questions.append({
            'question': f"Who received the highest total award amount?",
            'answer': top_earner,
            'category': 'Award Amount'
        })
        
        questions.append({
            'question': f"What was the total award amount received by {top_earner}?",
            'answer': str(int(top_amount)),
            'category': 'Award Amount'
        })
        
        # Program type questions
        top_program = list(analysis['programs'].keys())[0]
        program_count = analysis['programs'][top_program]
        questions.append({
            'question': f"Which recognition program was used the most?",
            'answer': top_program,
            'category': 'Program Type'
        })
        
        questions.append({
            'question': f"How many times was the '{top_program}' program used?",
            'answer': str(program_count),
            'category': 'Program Type'
        })
        
        # Generate more recipient-specific questions
        for i, (recipient, count) in enumerate(list(analysis['top_recipients'].items())[1:6]):
            questions.append({
                'question': f"How many recognitions did {recipient} receive?",
                'answer': str(count),
                'category': 'Recognition Count'
            })
        
        # Generate more giver-specific questions
        for i, (giver, count) in enumerate(list(analysis['top_givers'].items())[1:6]):
            questions.append({
                'question': f"How many recognitions did {giver} give?",
                'answer': str(count),
                'category': 'Recognition Count'
            })
        
        # Award type questions
        for award_type, count in analysis['award_types'].items():
            if pd.notna(award_type) and award_type != '':
                questions.append({
                    'question': f"How many recognitions included '{award_type}' as the award type?",
                    'answer': str(count),
                    'category': 'Award Type'
                })
        
        # Time-based questions
        questions.append({
            'question': f"How many recognitions were given in April 2025?",
            'answer': str(len(self.df[(self.df['Month'] == 4) & (self.df['Year'] == 2025)])),
            'category': 'Timeframe'
        })
        
        questions.append({
            'question': f"How many recognitions were given in March 2025?",
            'answer': str(len(self.df[(self.df['Month'] == 3) & (self.df['Year'] == 2025)])),
            'category': 'Timeframe'
        })
        
        questions.append({
            'question': f"How many recognitions were given in Q1 2025?",
            'answer': str(len(self.df[(self.df['Quarter'] == 1) & (self.df['Year'] == 2025)])),
            'category': 'Timeframe'
        })
        
        return questions
    
    def generate_relationship_questions(self):
        """Generate questions about giver-recipient relationships"""
        questions = []
        
        # Specific giver-recipient pairs
        pairs = self.df.groupby(['Giver Name', 'Recipient Name']).size().reset_index(name='count')
        pairs = pairs.sort_values('count', ascending=False)
        
        pair_limit = min(int(self.relationship_limit * 0.3), len(pairs))
        for idx, row in pairs.head(pair_limit).iterrows():
            if row['count'] > 1:
                questions.append({
                    'question': f"How many times did {row['Giver Name']} recognize {row['Recipient Name']}?",
                    'answer': str(row['count']),
                    'category': 'Giver-Recipient Relationship'
                })
        
        # Who received from whom
        date_limit = min(int(self.relationship_limit * 0.7), len(self.df))
        for idx, row in self.df.head(date_limit).iterrows():
            questions.append({
                'question': f"Who gave a recognition to {row['Recipient Name']} on {row['Date Received'].strftime('%B %d, %Y')}?",
                'answer': row['Giver Name'],
                'category': 'Giver-Recipient Relationship'
            })
        
        return questions
    
    def generate_ai_questions_from_comments(self):
        """Use AI to generate questions from submitter comments"""
        questions = []
        
        # Get unique, meaningful comments
        comments_df = self.df[self.df['Submitter Comments'].notna()].copy()
        comments_df = comments_df[comments_df['Submitter Comments'].str.len() > 50]
        
        prompt_template = PromptTemplate(
            input_variables=["comment", "recipient", "giver", "program"],
            template="""Based on the following recognition information, generate 3 unique, interesting and challenging quiz questions that test specific knowledge from the comment. 

IMPORTANT RULES FOR ANSWERS:
1. If the question asks "Who" or involves a person, the answer MUST be an employee name from the recognition data.
2. If the question asks "How many", "What amount", or involves a count/number, the answer MUST be ONLY a number.
3. For achievement/task questions, answer should be a specific achievement name or task name (short and concise).
4. Avoid generic or boring questions - make them specific and interesting.
5. Focus on unique achievements, specific numbers, and notable accomplishments.

Recognition Details:
- Program: {program}
- Recipient: {recipient}
- Giver: {giver}
- Comment: {comment}

Generate exactly 3 questions in JSON format. Each question should have these fields:
- "question": The quiz question (make it specific and interesting)
- "answer": The correct answer (MUST be either: employee name, OR number only, OR specific achievement/task name)
- "category": "Comment-Based"

Good Examples:
[
    {{"question": "Who received the best blogger award for Q3 2024?", "answer": "Gunender Kumar Prem Chand", "category": "Comment-Based"}},
    {{"question": "How many CBR-supported services got MFA integration?", "answer": "42", "category": "Comment-Based"}},
    {{"question": "What automation capability did Pavan implement?", "answer": "RULE PARAMETER VERSIONING", "category": "Comment-Based"}}
]

Bad Examples (avoid these):
- Questions with long sentence answers
- Generic questions without specific details
- Questions that can't be answered from the data

Return ONLY a valid JSON array with 3 question objects.
"""
        )
        
        # Process comments in batches to generate questions
        for idx, row in comments_df.head(self.comment_limit).iterrows():  # Use configurable limit
            try:
                prompt = prompt_template.format(
                    comment=row['Submitter Comments'][:1000],  # Limit comment length
                    recipient=row['Recipient Name'],
                    giver=row['Giver Name'],
                    program=row['Program Name']
                )
                
                response = self.llm.invoke(prompt)
                response_text = response.content
                
                # Parse JSON response
                # Clean the response to extract JSON
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]
                
                generated_questions = json.loads(response_text.strip())
                questions.extend(generated_questions)
                
            except Exception as e:
                print(f"Error generating questions for comment {idx}: {e}")
                continue
        
        return questions
    
    def generate_advanced_ai_questions(self, analysis):
        """Use AI to generate advanced analytical questions"""
        questions = []
        
        data_summary = f"""
Employee Recognition Data Summary:
- Total Records: {analysis['total_records']}
- Unique Recipients: {analysis['unique_recipients']}
- Unique Givers: {analysis['unique_givers']}
- Top 5 Recipients: {list(analysis['top_recipients'].items())[:5]}
- Top 5 Givers: {list(analysis['top_givers'].items())[:5]}
- Programs: {list(analysis['programs'].keys())}
- Award Types: {list(analysis['award_types'].keys())}
- Total Award Amount: {analysis['total_award_amount']}
- Recipients with Most Unique Givers: {list(analysis['recipients_with_most_unique_givers'].items())[:5]}
"""
        
        prompt_template = PromptTemplate(
            input_variables=["data_summary", "num_questions"],
            template="""Based on the following employee recognition data summary, generate {num_questions} unique, interesting and challenging quiz questions that test various aspects of the data.

{data_summary}

CRITICAL ANSWER FORMAT RULES:
1. If the question asks "Who" - answer MUST be an employee name ONLY (e.g., "Pavan Kumar Manda")
2. If the question asks "How many" or involves counting - answer MUST be a number ONLY (e.g., "5")
3. If the question asks about amounts - answer MUST be a number ONLY (e.g., "700")
4. NO long sentences or explanations in answers
5. Make questions interesting and challenging, not generic

Generate questions in these categories:
1. Comparative questions (who has more/less, differences in numbers)
2. Statistical questions (totals, counts, rankings)
3. Relationship questions (who recognized whom)
4. Temporal questions (monthly/quarterly patterns)
5. Award-specific questions (amounts, types)

IMPORTANT: 
- Avoid boring/generic questions like "What is the total number of X?"
- Focus on interesting comparisons and specific achievements
- Make questions that require thinking, not just data lookup

Return ONLY a valid JSON array with {num_questions} question objects. Each object should have:
- "question": The quiz question (specific and interesting)
- "answer": The correct answer (MUST be: employee name OR number only)
- "category": The question category

Good Examples:
[
    {{"question": "Who received more recognitions - Pavan Kumar Manda or Nagesh Raghupatruni?", "answer": "Pavan Kumar Manda", "category": "Comparative"}},
    {{"question": "How many recognitions did Sailaja Perumalla give?", "answer": "16", "category": "Statistical"}},
    {{"question": "Who gave the most BluePoints awards?", "answer": "Sailaja Perumalla", "category": "Award-specific"}}
]

Bad Examples (avoid):
- Questions with sentence answers
- Generic questions without interesting context
- Questions that are too easy or obvious
"""
        )
        
        try:
            prompt = prompt_template.format(
                data_summary=data_summary,
                num_questions=self.ai_advanced_limit
            )
            response = self.llm.invoke(prompt)
            response_text = response.content
            
            # Clean the response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            generated_questions = json.loads(response_text.strip())
            questions.extend(generated_questions)
            
        except Exception as e:
            print(f"Error generating advanced questions: {e}")
        
        return questions
    
    def generate_specific_scenario_questions(self):
        """Generate specific scenario-based questions"""
        questions = []
        
        # Divide scenario_limit among 3 question types
        award_limit = int(self.scenario_limit * 0.4)  # 40% for award amount questions
        giver_limit = int(self.scenario_limit * 0.3)  # 30% for giver questions
        recipient_limit = int(self.scenario_limit * 0.3)  # 30% for recipient questions
        
        # Questions about specific awards/programs
        count = 0
        for idx, row in self.df.head(min(award_limit * 2, len(self.df))).iterrows():
            if pd.notna(row['Award Amount']) and row['Award Amount'] > 0 and count < award_limit:
                questions.append({
                    'question': f"What award amount did {row['Recipient Name']} receive from {row['Giver Name']} on {row['Date Received'].strftime('%B %d, %Y')}?",
                    'answer': str(int(row['Award Amount'])),
                    'category': 'Specific Award'
                })
                count += 1
        
        # Questions about who gave recognition on specific dates (more variety)
        if giver_limit > 0 and len(self.df) > 0:
            sample_size = min(giver_limit, len(self.df))
            for idx, row in self.df.sample(sample_size).iterrows():
                questions.append({
                    'question': f"Who gave a recognition to {row['Recipient Name']} on {row['Date Received'].strftime('%B %d, %Y')}?",
                    'answer': row['Giver Name'],
                    'category': 'Giver-Recipient Relationship'
                })
        
        # Questions about who received from whom
        if recipient_limit > 0 and len(self.df) > 0:
            sample_size = min(recipient_limit, len(self.df))
            for idx, row in self.df.sample(sample_size).iterrows():
                questions.append({
                    'question': f"Who received a {row['Program Name']} from {row['Giver Name']} in {row['Date Received'].strftime('%B %Y')}?",
                    'answer': row['Recipient Name'],
                    'category': 'Recognition Details'
                })
        
        return questions
    
    def is_valid_answer_format(self, question_text, answer):
        """Validate that answer follows the format rules"""
        question_lower = question_text.lower()
        
        # Check if answer is not empty
        if not answer or str(answer).strip() == "":
            return False
        
        answer_str = str(answer).strip()
        
        # If question asks "who", answer should be a name (has at least one capital letter, not a sentence)
        if question_lower.startswith("who ") or " who " in question_lower:
            # Check if answer looks like a name (has capital letters, not overly long)
            # Accept both single names and full names
            if any(c.isupper() for c in answer_str) and len(answer_str) < 50:
                # Reject if it looks like a sentence (has multiple sentences or too many words)
                if answer_str.count('.') > 0 or len(answer_str.split()) > 6:
                    return False
                return True
            return False
        
        # If question asks "how many" or "what amount", answer should be just a number
        if "how many" in question_lower or "what amount" in question_lower or question_lower.startswith("how much"):
            # Answer should be a number (possibly with commas)
            try:
                # Remove commas and check if it's a valid number
                float(answer_str.replace(',', ''))
                # Make sure it doesn't contain letters (except maybe currency symbols)
                if not any(c.isalpha() for c in answer_str):
                    return True
            except:
                pass
            return False
        
        # For other questions, answer should be concise (not a long sentence)
        if len(answer_str) > 100 or answer_str.count('.') > 1:
            return False
        
        return True
    
    def is_interesting_question(self, question):
        """Filter out boring or generic questions"""
        question_text = question['question'].lower()
        answer = str(question['answer']).lower()
        
        # Filter out overly generic questions
        boring_patterns = [
            "what is the total number",
            "list all",
            "name all",
        ]
        
        for pattern in boring_patterns:
            if pattern in question_text:
                return False
        
        # Answer should not be too long (sentence answers are boring)
        if len(answer) > 150:
            return False
        
        # Question should not be too similar to common patterns
        # (These checks help ensure variety)
        
        return True
    
    def deduplicate_questions(self, questions):
        """Remove duplicate and similar questions"""
        unique_questions = []
        seen_questions = set()
        seen_answers = defaultdict(set)
        
        for q in questions:
            question_text = q['question'].strip()
            answer = str(q['answer']).strip()
            
            # Skip exact duplicates
            if question_text in seen_questions:
                continue
            
            # Skip if same answer appears too many times with similar question
            # Allow up to 3 questions with the same answer
            question_key = question_text.lower().split()[:5]  # First 5 words
            question_signature = ' '.join(question_key)
            
            if answer in seen_answers and len(seen_answers[answer]) >= 3:
                # Check if question is too similar to existing ones with same answer
                skip = False
                for existing_sig in seen_answers[answer]:
                    if existing_sig in question_signature or question_signature in existing_sig:
                        skip = True
                        break
                if skip:
                    continue
            
            seen_questions.add(question_text)
            seen_answers[answer].add(question_signature)
            unique_questions.append(q)
        
        return unique_questions
    
    def generate_all_questions(self):
        """Generate all types of questions"""
        print("Analyzing data...")
        analysis = self.analyze_data()
        
        all_questions = []
        
        print("Generating factual questions...")
        all_questions.extend(self.generate_factual_questions(analysis))
        
        print("Generating relationship questions...")
        all_questions.extend(self.generate_relationship_questions())
        
        print("Generating AI-powered questions from comments...")
        all_questions.extend(self.generate_ai_questions_from_comments())
        
        print("Generating advanced AI questions...")
        all_questions.extend(self.generate_advanced_ai_questions(analysis))
        
        print("Generating specific scenario questions...")
        all_questions.extend(self.generate_specific_scenario_questions())
        
        # Validate answer formats
        print("Validating answer formats...")
        valid_questions = []
        invalid_count = 0
        for q in all_questions:
            if self.is_valid_answer_format(q['question'], q['answer']):
                valid_questions.append(q)
            else:
                invalid_count += 1
        
        if invalid_count > 0:
            print(f"Filtered out {invalid_count} questions with invalid answer formats")
        
        # Filter out uninteresting questions
        print("Filtering interesting questions...")
        interesting_questions = []
        for q in valid_questions:
            if self.is_interesting_question(q):
                interesting_questions.append(q)
        
        filtered_out = len(valid_questions) - len(interesting_questions)
        if filtered_out > 0:
            print(f"Filtered out {filtered_out} uninteresting questions")
        
        # Remove duplicates with improved logic
        print("Removing duplicates...")
        unique_questions = self.deduplicate_questions(interesting_questions)
        
        duplicates_removed = len(interesting_questions) - len(unique_questions)
        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate questions")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 Generation Summary:")
        print(f"   Total generated (raw): {len(all_questions)} questions")
        print(f"   After validation: {len(valid_questions)} questions")
        print(f"   After filtering: {len(interesting_questions)} questions")
        print(f"   Final unique: {len(unique_questions)} questions")
        print(f"   Total removed: {len(all_questions) - len(unique_questions)} questions")
        print(f"{'='*60}\n")
        
        return unique_questions
    
    def save_questions(self, questions, output_file='quiz_questions.json'):
        """Save questions to a JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Saved {len(questions)} questions to {output_file}")
    
    def save_questions_formatted(self, questions, output_file='quiz_questions_formatted.txt'):
        """Save questions in a readable format"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"QUIZ QUESTIONS - TOTAL: {len(questions)}\n")
            f.write("=" * 80 + "\n\n")
            
            # Group by category
            by_category = defaultdict(list)
            for q in questions:
                by_category[q.get('category', 'General')].append(q)
            
            question_num = 1
            for category, qs in sorted(by_category.items()):
                f.write(f"\n{'=' * 80}\n")
                f.write(f"CATEGORY: {category.upper()} ({len(qs)} questions)\n")
                f.write(f"{'=' * 80}\n\n")
                
                for q in qs:
                    f.write(f"Q{question_num}: {q['question']}\n")
                    f.write(f"Answer: {q['answer']}\n\n")
                    question_num += 1
        
        print(f"✅ Saved formatted questions to {output_file}")


def main():
    csv_path = "/Users/faridshaik/Desktop/Projects/quiz-ques-gen/Recognition_cleaned - Results.csv"
    
    print("🚀 Starting Quiz Question Generation...")
    print(f"📊 Reading data from: {csv_path}\n")
    
    generator = QuizQuestionGenerator(csv_path)
    questions = generator.generate_all_questions()
    
    print(f"\n🎯 Generated {len(questions)} unique questions!")
    print(f"\nBreakdown by category:")
    
    by_category = defaultdict(int)
    for q in questions:
        by_category[q.get('category', 'General')] += 1
    
    for category, count in sorted(by_category.items()):
        print(f"  - {category}: {count} questions")
    
    # Save questions
    generator.save_questions(questions, 'quiz_questions.json')
    generator.save_questions_formatted(questions, 'quiz_questions_formatted.txt')
    
    print("\n✨ Quiz question generation complete!")
    print(f"📁 Output files:")
    print(f"  - quiz_questions.json (JSON format)")
    print(f"  - quiz_questions_formatted.txt (readable format)")


if __name__ == "__main__":
    main()

