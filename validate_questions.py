import json

def validate_questions(file_path):
    """Validate question quality and answer formats"""
    with open(file_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    print(f"Total Questions: {len(questions)}\n")
    
    # Check for duplicates
    question_texts = [q['question'] for q in questions]
    duplicates = len(question_texts) - len(set(question_texts))
    print(f"✅ Duplicate questions: {duplicates}")
    
    # Analyze answer formats
    who_questions = []
    how_many_questions = []
    other_questions = []
    
    problematic = []
    
    for i, q in enumerate(questions, 1):
        question_text = q['question'].lower()
        answer = str(q['answer'])
        
        if question_text.startswith("who ") or " who " in question_text:
            who_questions.append((i, q['question'], answer))
            # Check if answer is a valid name (has capital letter, not too long)
            if not any(c.isupper() for c in answer) or len(answer) > 50 or '.' in answer:
                problematic.append((i, q['question'], answer, "Invalid name format"))
        
        elif "how many" in question_text or "what amount" in question_text:
            how_many_questions.append((i, q['question'], answer))
            # Check if answer is a number
            try:
                float(answer.replace(',', ''))
                if any(c.isalpha() for c in answer):
                    problematic.append((i, q['question'], answer, "Number should not contain letters"))
            except:
                problematic.append((i, q['question'], answer, "Not a valid number"))
        else:
            other_questions.append((i, q['question'], answer))
            # Check if answer is too long
            if len(answer) > 100:
                problematic.append((i, q['question'], answer, "Answer too long"))
    
    print(f"✅ 'Who' questions: {len(who_questions)}")
    print(f"✅ 'How many' questions: {len(how_many_questions)}")
    print(f"✅ Other questions: {len(other_questions)}")
    print(f"\n{'='*80}")
    
    if problematic:
        print(f"\n⚠️  Found {len(problematic)} potentially problematic questions:\n")
        for num, q, a, reason in problematic:
            print(f"Q{num}: {q}")
            print(f"Answer: {a}")
            print(f"Issue: {reason}\n")
    else:
        print("\n✅ All questions passed validation!")
    
    # Sample some good examples
    print(f"\n{'='*80}")
    print("📊 Sample Questions by Type:\n")
    
    print("WHO Questions (5 samples):")
    for i, (num, q, a) in enumerate(who_questions[:5], 1):
        print(f"{i}. Q{num}: {q}")
        print(f"   Answer: {a}\n")
    
    print("\nHOW MANY Questions (5 samples):")
    for i, (num, q, a) in enumerate(how_many_questions[:5], 1):
        print(f"{i}. Q{num}: {q}")
        print(f"   Answer: {a}\n")
    
    print("\nOTHER Questions (5 samples):")
    for i, (num, q, a) in enumerate(other_questions[:5], 1):
        print(f"{i}. Q{num}: {q}")
        print(f"   Answer: {a}\n")
    
    # Category breakdown
    categories = {}
    for q in questions:
        cat = q.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n{'='*80}")
    print("📈 Category Distribution:\n")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} questions")

if __name__ == "__main__":
    validate_questions('quiz_questions.json')




