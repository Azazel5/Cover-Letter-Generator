import google.generativeai as genai
from pypdf import PdfReader, PdfWriter

# Configure Gemini API
# try:
#     genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
# except KeyError:
#     print("Error: GOOGLE_API_KEY environment variable not set.")
#     print("Set it with: export GOOGLE_API_KEY='your_api_key'")
#     exit(1)


def inspect_pdf_fields(pdf_path):
    """Inspect what field names actually exist in your PDF"""

    try:
        reader = PdfReader(pdf_path)
        fields = reader.get_fields()

        print(f"📋 Found {len(fields)} fields in your PDF:")
        for field_name, _ in fields.items():
            print(f"   Field: '{field_name}'")

        return list(fields.keys())

    except Exception as e:
        print(f"❌ Error reading PDF fields: {e}")
        return []


def extract_text(full_text, start_tag, end_tag):
    """Extract text between start and end tags."""

    try:
        start_index = full_text.index(start_tag) + len(start_tag)
        end_index = full_text.index(end_tag)
        return full_text[start_index:end_index].strip()
    except ValueError:
        return None


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
            print(f"❌ Error: Failed to parse sections: {missing_sections}")
            print("\n🔍 AI Raw Response:", ai_response_text)
            return None

        # Display generated content for review
        print("\n📝 Generated Content:")
        for key, value in content.items():
            print(f"  {key}: {value[:100]}{'...' if len(value) > 100 else ''}")

        return content

    except Exception as e:
        print(f"❌ An error occurred with the API call: {e}")
        return None


def read_file_content(filepath):
    """Reads and returns the content of a file."""

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: The file '{filepath}' was not found.")
        exit(1)
    except Exception as e:
        print(f"❌ Error reading file '{filepath}': {e}")
        exit(1)


def fill_pdf_form(template_pdf_path, output_pdf_path, field_data):
    """
    Fill a PDF form with provided data

    Args:
        template_pdf_path: Path to PDF with form fields
        output_pdf_path: Where to save the filled PDF
        field_data: Dictionary with field_name: text_content pairs
    """
    try:
        reader = PdfReader(template_pdf_path)
        writer = PdfWriter()
        writer.append(reader)

        # Fill the form fields
        if '/AcroForm' in reader.trailer['/Root'] and '/Fields' in reader.trailer['/Root']['/AcroForm']:
            for field_ref in reader.trailer['/Root']['/AcroForm']['/Fields']:
                field = field_ref.get_object()
                if '/DA' in field:
                    # Override with ITC Avant Garde 10pt
                    field['/DA'] = '/AvantGarde 10 Tf 0 g'
                    
        writer.update_page_form_field_values(
            writer.pages[0], field_data, auto_regenerate=False, flags=0)

        # Save the result
        with open(output_pdf_path, "wb") as output_file:
            writer.write(output_file)

        print(f"✅ PDF filled successfully: {output_pdf_path}")
        return True

    except Exception as e:
        print(f"❌ Error filling PDF: {e}")
        return False


def main():
    field_data = {
        "company_name": "Tesla",
        "company_address": "619 Stud Street"
        "job_title": "Senior Software Engineer",
        "ai_hook_insight": "Tesla's revolutionary approach to sustainable energy and autonomous driving technology perfectly aligns with my passion for innovation.",
        "ai_skill_alignment_paragraph": "My 7 years of Python development and machine learning expertise directly match your need for scalable software solutions. I've built real-time data processing systems that handle millions of transactions daily, similar to what Tesla requires for vehicle telemetry.",
        "ai_quantifiable_achievement_paragraph": "At my previous role, I increased system performance by 60% and reduced processing time from 2 hours to 15 minutes through algorithm optimization. I also led a team of 5 engineers to deliver a critical project 3 weeks ahead of schedule, resulting in $2M cost savings.",
        "ai_culture_fit_paragraph": "Tesla's mission to accelerate sustainable transport resonates deeply with my values. I thrive in fast-paced environments where bold thinking and rapid iteration drive breakthrough innovations that can change the world."
    }

    TEMPLATE_PATH = "Subhanga Cover Template with Blank forms.pdf"
    fill_pdf_form(TEMPLATE_PATH,
                  "Edited Cover.pdf", field_data)


if __name__ == "__main__":
    main()
