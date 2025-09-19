import os
import argparse
from fpdf import FPDF
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
        print("🤖 Generating content with Gemini...")
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

    print("🤖 Calling Gemini to generate custom content...")
    ai_content = generate_custom_content(resume, job_description)

    if not ai_content:
        print("Could not generate cover letter content. Exiting.")
        exit()

    # 2. Setup PDF document
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=20, top=15, right=20)

    # 3. Set Font (Using a standard, clean sans-serif font)
    # For custom fonts, you would need the .ttf file and use pdf.add_font()
    # But Helvetica is a professional and safe choice.
    pdf.set_font("Helvetica", size=10)

    # 4. Write the content to the PDF
    # The `multi_cell` function automatically handles text wrapping.
    # `ln()` creates a line break. The value determines the height.

    # -- Your Info Header (You can add your name, etc. here) --
    pdf.cell(0, 5, "Subhanga Upadhyay", align='L')
    pdf.cell(0, 5, args.job_title, align='R')
    pdf.ln(10)  # Add a 10mm break

    # -- Company Info Header --
    pdf.multi_cell(0, 5, f"{args.company}\n{args.company_address}")
    pdf.ln(10)

    # -- Body of the Letter --
    pdf.multi_cell(0, 5, "Dear Hiring Team,")
    pdf.ln(20)

    # Combine static text with the AI-generated hook
    opening_paragraph = (
        f"Having followed your company's pioneering work in the field, I was particularly impressed by {ai_content['ai_hook_insight']}"
        "This commitment to pushing boundaries resonates deeply with my own professional journey. "
        "My career has been a deliberate pursuit of deep expertise - from seeking a wealth of experiences in consulting to now pursuing a Master's degree to bridge the gap between complex business challenges and core machine learning engineering. "
        f"This personal drive for constant improvement and excellence is why I am confident my skills are perfectly aligned with the challenges of the {args.job_title} position."
    )
    pdf.multi_cell(0, 5, opening_paragraph)
    pdf.ln(5)

    pdf.multi_cell(0, 5, ai_content['ai_skill_alignment_paragraph'])
    pdf.ln(5)

    pdf.multi_cell(0, 5, ai_content['ai_quantifiable_achievement_paragraph'])
    pdf.ln(5)

    closing_paragraph = (
        f"Beyond my technical skills, I am deeply drawn to the culture at {args.company}. {ai_content['ai_culture_fit_paragraph']}"
        "I am not just looking for another role; I am looking to join a team where my values of excellence and collaboration can contribute to a meaningful vision, and I believe your company is the ideal place for that."
    )
    pdf.multi_cell(0, 5, closing_paragraph)
    pdf.ln(5)

    pdf.multi_cell(0, 5, "I am eager to discuss how my unique background and skills in software engineering can bring a valuable perspective to your team. Thank you for your time and consideration.")
    pdf.ln(20)

    pdf.multi_cell(0, 5, "With gratitude,")
    pdf.ln(10)
    pdf.multi_cell(0, 5, "Subhanga Upadhyay")

    # 5. Save the PDF
    output_filename = f"Subhanga_Cover_Letter_{args.company.replace(' ', '_')}.pdf"
    pdf.output(output_filename)

    print(
        f"Success! Your new PDF cover letter is ready: {output_filename}")
