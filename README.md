# Quiz Question Generator

An AI-powered quiz question generator that creates engaging quiz questions from employee recognition data using LangChain and Google's Gemini AI.

## Features

- AI-Powered Generation - Uses Google Gemini AI to create intelligent questions
- Multiple Question Types - Recognition counts, relationships, awards, timeframes, and more
- Web Interface - Beautiful Streamlit UI for easy use
- Multiple Formats - Export as JSON or formatted text
- Quality Validated - Removes duplicates and ensures proper answer formats
- Category Organization - Questions grouped by type for easy navigation

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Get Your API Key

1. Visit https://ai.google.dev/
2. Sign in and create an API key
3. Copy your API key

## Usage

### Option 1: Web Interface (Recommended)

```bash
streamlit run streamlit_app.py
```

Then:
1. Enter your Gemini API key in the sidebar
2. Upload your CSV file
3. Click "Generate Quiz Questions"
4. Download your questions in JSON or TXT format

### Option 2: Command Line

Update the API key in `generate_quiz_questions.py`, then:

```bash
python generate_quiz_questions.py
```

## Input Data Format

Your CSV file should have these columns:

- Program Name - Recognition program type
- Date Received - Date (MM/DD/YYYY format)
- Recipient Name - Person who received recognition
- Giver Name - Person who gave recognition
- Award Amount - Award value (if applicable)
- Award Type - Type of award (BPs, cash, etc.)
- Submitter Comments - Details about the recognition

## Question Categories

The generator creates diverse question types:

- Comment-Based - AI extracts specific details from recognition comments
- Giver-Recipient Relationship - Who recognized whom and how many times
- Recognition Count - Statistics about recognition patterns
- Award Amounts - Questions about award values
- Timeframe - Monthly and quarterly recognition patterns
- Program Types - Recognition program usage
- Statistical Analysis - Comparative and analytical questions

## Output

### JSON Format

Perfect for importing into quiz platforms like Kahoot or Quizlet:

```json
[
  {
    "question": "Who received the highest number of recognitions?",
    "answer": "John Doe",
    "category": "Recognition Count"
  }
]
```

### TXT Format

Human-readable format for printing or manual review.

## Tech Stack

- Python 3.8+ - Core language
- LangChain - AI framework
- Google Gemini AI - Question generation
- Pandas - Data analysis
- Streamlit - Web interface

## Example Questions

**Q:** Who received the highest number of recognitions?
**A:** Ballary Javid Hussain

**Q:** How many recognitions were given in April 2025?
**A:** 23

**Q:** Who gave the highest number of recognitions?
**A:** Sailaja Perumalla

**Q:** What was the highest total award amount received?
**A:** 700

## Validation

Run the validation script to check question quality:

```bash
python validate_questions.py
```

This checks for:
- Duplicate questions
- Proper answer formats
- Question quality

## Note

The free tier of Gemini API has rate limits (10 requests/minute). The generator includes automatic retry logic to handle this gracefully.

## License

Open source - use and modify as needed for your organization.

---

Made with love for creating engaging employee recognition quizzes
