import streamlit as st
import pandas as pd
import json
from collections import defaultdict
from generate_quiz_questions import QuizQuestionGenerator
import io

# Page configuration
st.set_page_config(
    page_title="Quiz Question Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main styling */
    .main {
        padding: 2rem;
    }
    
    /* Header styling */
    .title-container {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .title-container h1 {
        color: white !important;
        margin: 0;
        font-size: 3rem;
        font-weight: 700;
    }
    
    .title-container p {
        color: #f0f0f0;
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }
    
    /* Category badge styling */
    .category-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Question card styling */
    .question-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    
    .question-text {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .answer-text {
        color: #27ae60;
        font-weight: 600;
        padding-left: 1rem;
    }
    
    /* Stats box styling */
    .stats-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .stats-number {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
    }
    
    .stats-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    /* Upload section */
    .upload-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #667eea;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-size: 1.1rem;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        border: none;
    }
    
    /* Download button styling */
    .stDownloadButton>button {
        background: #27ae60;
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
    }
    
    .stDownloadButton>button:hover {
        background: #229954;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #f8f9fa;
        border-radius: 8px;
        font-weight: 600;
        color: #2c3e50;
    }
    
    /* Info box */
    .info-box {
        background: #e8f4f8;
        border-left: 4px solid #3498db;
        padding: 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
    
    /* Success box */
    .success-box {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'questions' not in st.session_state:
    st.session_state.questions = None
if 'generated' not in st.session_state:
    st.session_state.generated = False

# Title
st.markdown("""
<div class="title-container">
    <h1>🎯 Quiz Question Generator</h1>
    <p>Generate intelligent quiz questions from employee recognition data using AI</p>
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    # API Key input
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        help="Enter your Google Gemini API key",
        placeholder="AIzaSy..."
    )
    
    st.markdown("---")
    
    # Number of questions slider
    st.markdown("### 📊 Question Settings")
    num_questions = st.slider(
        "Target Number of Questions",
        min_value=50,
        max_value=200,
        value=135,
        step=5,
        help="Approximate number of questions to generate"
    )
    
    # Calculate limits based on target
    # Factual questions (~25 fixed) + all other types should sum to target
    # Account for ~20% filtering loss
    base_factual = 25  # Fixed factual questions
    remaining_target = num_questions - base_factual
    
    # Distribute remaining with multiplier for filtering
    multiplier = 1.2  # Generate 20% more to account for filtering
    
    comment_limit = max(5, int(remaining_target * 0.20 * multiplier))
    scenario_limit = max(8, int(remaining_target * 0.12 * multiplier))
    ai_advanced_limit = max(10, int(remaining_target * 0.30 * multiplier))
    relationship_limit = max(10, int(remaining_target * 0.18 * multiplier))
    
    st.info(f"""
📝 Generation targets (before filtering):
- Comment-based: ~{comment_limit} questions
- Scenario-based: ~{scenario_limit} questions
- AI advanced: ~{ai_advanced_limit} questions
- Relationships: ~{relationship_limit} questions

Expected final output: ~{num_questions} questions after quality filtering
""")
    
    st.markdown("---")
    
    # Info section
    st.markdown("### ℹ️ About")
    st.markdown("""
    This tool uses **LangChain** and **Google Gemini AI** to generate intelligent quiz questions from your employee recognition data.
    
    **Features:**
    - AI-powered question generation
    - Multiple question categories
    - Strict answer validation
    - Duplicate detection
    - Download in JSON & TXT formats
    """)
    
    st.markdown("---")
    st.markdown("**Built with ❤️ using Streamlit**")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📤 Upload Recognition Data")
    
    uploaded_file = st.file_uploader(
        "Upload your CSV file containing employee recognition data",
        type=['csv'],
        help="The CSV should contain columns: Program Name, Date Received, Recipient Name, Giver Name, Award Amount, Award Type, Submitter Comments"
    )
    
    if uploaded_file is not None:
        # Show preview
        try:
            df_preview = pd.read_csv(uploaded_file)
            st.success(f"✅ File loaded successfully! Found **{len(df_preview)}** recognition records.")
            
            with st.expander("👀 Preview Data (first 5 rows)"):
                st.dataframe(df_preview.head(), use_container_width=True)
            
            # Reset file pointer for processing
            uploaded_file.seek(0)
            
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            uploaded_file = None

with col2:
    st.markdown("### 📋 Requirements")
    st.markdown("""
    **Required CSV Columns:**
    - Program Name
    - Date Received
    - Recipient Name
    - Giver Name
    - Award Amount
    - Award Type
    - Submitter Comments
    
    **Date Format:** MM/DD/YYYY
    """)

# Generate button
if uploaded_file is not None:
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("🚀 Generate Quiz Questions", use_container_width=True)
    
    if generate_button:
        if not api_key:
            st.error("⚠️ Please enter your Gemini API key in the sidebar!")
        else:
            # Reset file pointer
            uploaded_file.seek(0)
            
            with st.spinner("🤖 Generating questions with AI... This may take a few minutes."):
                try:
                    # Create progress indicators
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Initialize generator
                    status_text.text("📊 Analyzing data...")
                    progress_bar.progress(10)
                    
                    generator = QuizQuestionGenerator(
                        uploaded_file=uploaded_file,
                        api_key=api_key
                    )
                    
                    # Set generation limits
                    # Set generation limits for all question types
                    generator.set_generation_limits(
                        comment_questions=comment_limit,
                        scenario_questions=scenario_limit,
                        ai_advanced_questions=ai_advanced_limit,
                        relationship_questions=relationship_limit
                    )
                    
                    progress_bar.progress(20)
                    
                    # Generate questions
                    status_text.text("🎯 Generating factual questions...")
                    progress_bar.progress(30)
                    
                    status_text.text("🤝 Generating relationship questions...")
                    progress_bar.progress(50)
                    
                    status_text.text("🤖 Using AI to analyze comments...")
                    progress_bar.progress(70)
                    
                    status_text.text("✨ Finalizing and validating questions...")
                    questions = generator.generate_all_questions()
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Complete!")
                    
                    # Store in session state
                    st.session_state.questions = questions
                    st.session_state.generated = True
                    
                    st.success(f"🎉 Successfully generated **{len(questions)}** unique quiz questions!")
                    
                except Exception as e:
                    st.error(f"❌ Error generating questions: {str(e)}")
                    st.exception(e)

# Display results
if st.session_state.generated and st.session_state.questions:
    questions = st.session_state.questions
    
    st.markdown("---")
    st.markdown("## 📊 Generated Questions")
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    # Count by category
    categories = defaultdict(int)
    for q in questions:
        categories[q.get('category', 'General')] += 1
    
    with col1:
        st.markdown(f"""
        <div class="stats-box">
            <p class="stats-number">{len(questions)}</p>
            <p class="stats-label">Total Questions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-box">
            <p class="stats-number">{len(categories)}</p>
            <p class="stats-label">Categories</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Count who/how many questions
    who_count = sum(1 for q in questions if q['question'].lower().startswith('who '))
    how_many_count = sum(1 for q in questions if 'how many' in q['question'].lower())
    
    with col3:
        st.markdown(f"""
        <div class="stats-box">
            <p class="stats-number">{who_count}</p>
            <p class="stats-label">"Who" Questions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stats-box">
            <p class="stats-number">{how_many_count}</p>
            <p class="stats-label">"How Many" Questions</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Download buttons
    st.markdown("### 💾 Download Questions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON download
        json_str = json.dumps(questions, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download as JSON",
            data=json_str,
            file_name="quiz_questions.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # TXT download
        txt_content = f"QUIZ QUESTIONS - TOTAL: {len(questions)}\n"
        txt_content += "=" * 80 + "\n\n"
        
        # Group by category
        by_category = defaultdict(list)
        for q in questions:
            by_category[q.get('category', 'General')].append(q)
        
        question_num = 1
        for category, qs in sorted(by_category.items()):
            txt_content += f"\n{'=' * 80}\n"
            txt_content += f"CATEGORY: {category.upper()} ({len(qs)} questions)\n"
            txt_content += f"{'=' * 80}\n\n"
            
            for q in qs:
                txt_content += f"Q{question_num}: {q['question']}\n"
                txt_content += f"Answer: {q['answer']}\n\n"
                question_num += 1
        
        st.download_button(
            label="📥 Download as TXT",
            data=txt_content,
            file_name="quiz_questions.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Category-based display
    st.markdown("### 📂 Questions by Category")
    st.markdown("Click on a category below to expand and view questions")
    
    # Group questions by category
    by_category = defaultdict(list)
    for q in questions:
        by_category[q.get('category', 'General')].append(q)
    
    # Display categories in columns
    categories_list = sorted(by_category.items(), key=lambda x: -len(x[1]))
    
    for category, category_questions in categories_list:
        with st.expander(f"**{category}** ({len(category_questions)} questions)", expanded=False):
            for i, q in enumerate(category_questions, 1):
                st.markdown(f"""
                <div class="question-card">
                    <div class="question-text">Q{i}: {q['question']}</div>
                    <div class="answer-text">✓ Answer: {q['answer']}</div>
                </div>
                """, unsafe_allow_html=True)
else:
    # Welcome message when no questions generated
    st.markdown("---")
    st.markdown("""
    <div class="info-box">
        <h3>👋 Welcome to Quiz Question Generator!</h3>
        <p>To get started:</p>
        <ol>
            <li>Enter your Gemini API key in the sidebar</li>
            <li>Upload your employee recognition CSV file</li>
            <li>Configure the number of questions (optional)</li>
            <li>Click "Generate Quiz Questions"</li>
        </ol>
        <p>The AI will analyze your data and create intelligent, validated quiz questions that you can use for office competitions!</p>
    </div>
    """, unsafe_allow_html=True)




