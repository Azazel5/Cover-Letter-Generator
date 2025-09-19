import os
import argparse
import pyperclip 
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables

load_dotenv()

# Configure Gemini API
try:
    genai.configure(api_key=os.environ["GEMINI_API"])
except KeyError:
    print("Error: GEMINI_API environment variable not set.")
    print("Set it with: export GEMINI_API='your_api_key'")
    exit(1)


def extract_text(full_text, start_tag, end_tag):
    """Extract text between start and end tags."""

    try:
        start_index = full_text.index(start_tag) + len(start_tag)
        end_index = full_text.index(end_tag)
        return full_text[start_index:end_index].strip()
    except ValueError:
        return None


def read_file_content(filepath):
    """Reads and returns the content of a file."""

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        exit()
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        exit()


def generate_custom_content(resume_text, job_desc_text):
    """Uses the Gemini API to generate four distinct cover letter components."""

    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt_template = read_file_content('master_prompt.txt')
    prompt = prompt_template.format(
        resume_text=resume_text, job_desc_text=job_desc_text)

    try:
        print("Generating content with Gemini...")
        response = model.generate_content(prompt)
        ai_response_text = response.text

        # Extract the four sections
        content = {
            "ai_hook_insight": extract_text(ai_response_text, "[HOOK_INSIGHT_START]", "[HOOK_INSIGHT_END]"),
            "ai_skill_alignment_paragraph": extract_text(ai_response_text, "[SKILL_ALIGNMENT_START]", "[SKILL_ALIGNMENT_END]"),
            "ai_quantifiable_achievement_paragraph": extract_text(ai_response_text, "[QUANTIFIABLE_ACHIEVEMENT_START]", "[QUANTIFIABLE_ACHIEVEMENT_END]"),
            "ai_culture_fit_paragraph": extract_text(ai_response_text, "[CULTURE_FIT_START]", "[CULTURE_FIT_END]"),
        }

        # Validate all sections were extracted
        missing_sections = [key for key, value in content.items() if not value]
        if missing_sections:
            print(f"Error: Failed to parse sections: {missing_sections}")
            print("\n🔍 AI Raw Response:", ai_response_text)
            return None

        # Display generated content for review
        print("\n📝 Generated Content:")
        for key, value in content.items():
            print(f"  {key}: {value[:100]}{'...' if len(value) > 100 else ''}")

        return content

    except Exception as e:
        print(f"An error occurred with the API call: {e}")
        return None


# --- Main Execution: Build the PDF from Scratch ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a custom PDF cover letter from scratch.")
    parser.add_argument("company", help="The name of the company.")
    parser.add_argument("job_title", help="The title of the job.")
    parser.add_argument("--addr", dest="company_address",
                        default="", help="Optional: Company's mailing address.")
    args = parser.parse_args()

    # 1. Get content from files and AI
    resume = ""
    job_description = ""
    try:
        with open('resume.txt', 'r', encoding='utf-8') as f:
            resume = f.read()
        with open('job_description.txt', 'r', encoding='utf-8') as f:
            job_description = f.read()
    except FileNotFoundError as e:
        print(f"Error reading file: {e}")
        exit()

    print("Calling Gemini to generate custom content...")
    ai_content = generate_custom_content(resume, job_description)

    if not ai_content:
        print("Could not generate cover letter content. Exiting.")
        exit()

    cover_letter_string = f"""
    Dear Hiring Team,

        
        Having followed your company's pioneering work in the field, I was particularly impressed by {ai_content['ai_hook_insight']}. This commitment to pushing boundaries resonates deeply with my own professional journey. My career has been a deliberate pursuit of deep expertise - from seeking a wealth of experiences in consulting to now pursuing a Master's degree to bridge the gap between complex business challenges and core machine learning engineering. This personal drive for constant improvement and excellence is why I am confident my skills are perfectly aligned with the challenges of the {args.job_title} position.

        {ai_content['ai_skill_alignment_paragraph']}

        {ai_content['ai_quantifiable_achievement_paragraph']}

        Beyond my technical skills, I am deeply drawn to the culture at {args.company}. {ai_content['ai_culture_fit_paragraph']} I am not just looking for another role; I am looking to join a team where my values of excellence and collaboration can contribute to a meaningful vision, and I believe your company is the ideal place for that.

        I am eager to discuss how my unique background and skills in software engineering can bring a valuable perspective to your team. Thank you for your time and consideration.

        
    With gratitude
    """

    # 3. Copy the final string to the clipboard
    pyperclip.copy(cover_letter_string)

    print("Success! The cover letter text has been generated and copied to your clipboard.")
    print("You can now paste it into any application.")
