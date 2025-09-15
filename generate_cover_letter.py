import os
import pikepdf
import argparse
import google.generativeai as genai
from pypdf import PdfReader, PdfWriter

# Configure Gemini API
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("❌ Error: GOOGLE_API_KEY environment variable not set.")
    print("   Set it with: export GOOGLE_API_KEY='your_api_key'")
    exit(1)

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
    prompt = prompt_template.format(resume_text=resume_text, job_desc_text=job_desc_text)
    
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

def fill_pdf_template(template_path, output_path, form_data):
    """Fill the PDF template with generated content."""
    try:
        print(f"📄 Filling PDF template...")
        reader = PdfReader(template_path)
        writer = PdfWriter()
        
        # Copy all pages
        for page in reader.pages:
            writer.add_page(page)
        
        # Fill form fields
        writer.update_page_form_field_values(writer.pages[0], form_data)
        
        # Write output
        with open(output_path, "wb") as output_stream:
            writer.write(output_stream)
            
        print(f"✅ Success! Cover letter saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error during PDF generation: {e}")
        return False

def setup_cover_letter_template(template_path, output_path):
    """Creates a fillable PDF template with properly configured form fields."""
    
    if not os.path.exists(template_path):
        print(f"❌ Error: Template file '{template_path}' not found.")
        return False
    
    try:
        pdf = pikepdf.Pdf.open(template_path)
        
        # Ensure we have an AcroForm
        if '/AcroForm' not in pdf.Root:
            pdf.Root.AcroForm = pikepdf.Dictionary({
                '/Fields': pikepdf.Array(),
                '/NeedAppearances': True,
                '/DR': pikepdf.Dictionary({
                    '/Font': pikepdf.Dictionary({
                        '/Helv': pikepdf.Dictionary({
                            '/Type': pikepdf.Name('/Font'),
                            '/Subtype': pikepdf.Name('/Type1'),
                            '/BaseFont': pikepdf.Name('/Helvetica')
                        })
                    })
                })
            })
        
        # Define fields (adjust coordinates based on your template)
        fields = {
            'company_name': {
                'rect': [120, 720, 400, 735],
                'multiline': False,
                'font_size': 12,
                'max_chars': 50
            },
            'ai_hook_insight': {
                'rect': [120, 650, 480, 680],
                'multiline': True,
                'font_size': 10,
                'max_chars': 150
            },
            'ai_skill_alignment_paragraph': {
                'rect': [120, 550, 480, 630],
                'multiline': True,
                'font_size': 10,
                'max_chars': 400
            },
            'ai_quantifiable_achievement_paragraph': {
                'rect': [120, 450, 480, 530],
                'multiline': True,
                'font_size': 10,
                'max_chars': 400
            },
            'ai_culture_fit_paragraph': {
                'rect': [120, 380, 480, 430],
                'multiline': True,
                'font_size': 10,
                'max_chars': 200
            }
        }
        
        # Create form fields
        for field_name, spec in fields.items():
            field = pikepdf.Dictionary({
                '/Type': pikepdf.Name('/Annot'),
                '/Subtype': pikepdf.Name('/Widget'),
                '/FT': pikepdf.Name('/Tx'),
                '/T': pikepdf.String(field_name),
                '/Rect': pikepdf.Array(spec['rect']),
                '/DA': pikepdf.String(f'/Helv {spec["font_size"]} Tf 0 g'),
                '/V': pikepdf.String(''),
                '/DV': pikepdf.String(''),
                '/Ff': 4096 if spec['multiline'] else 0,
                '/Q': 0,
                '/MaxLen': spec['max_chars']
            })
            
            # Add to page and form
            if '/Annots' not in pdf.pages[0]:
                pdf.pages[0]['/Annots'] = pikepdf.Array()
            pdf.pages[0]['/Annots'].append(field)
            pdf.Root.AcroForm.Fields.append(field)
        
        pdf.save(output_path)
        pdf.close()
        print(f"✅ Template created successfully: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating template: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate a custom, AI-powered PDF cover letter.")
    parser.add_argument("company", help="The name of the company")
    parser.add_argument("job_title", help="The title of the job")
    parser.add_argument("--hm", dest="hiring_manager", default="Hiring Team", 
                       help="Optional: Name of the hiring manager")
    parser.add_argument("--setup", action="store_true", 
                       help="Set up the PDF template (run this first)")
    parser.add_argument("--template", default="canva_template.pdf",
                       help="Path to your base PDF template")
    
    args = parser.parse_args()
    
    # Setup mode
    if args.setup:
        print("🔧 Setting up PDF template...")
        if setup_cover_letter_template(args.template, "fillable_template.pdf"):
            print("\n✅ Setup complete! Now run without --setup to generate cover letters.")
        return
    
    # Validate required files
    required_files = ['resume.txt', 'job_description.txt', 'master_prompt.txt', 'fillable_template.pdf']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        if 'fillable_template.pdf' in missing_files:
            print("   Run with --setup first to create the template.")
        return
    
    # Generate cover letter
    print(f"🚀 Generating cover letter for {args.company} - {args.job_title}")
    
    # Read input files
    resume = read_file_content('resume.txt')
    job_description = read_file_content('job_description.txt')
    
    # Generate content
    custom_content = generate_custom_content(resume, job_description)
    
    if not custom_content:
        print("❌ Failed to generate content. Check your prompt and API key.")
        return
    
    # Prepare form data
    form_data = {
        "company_name": args.company,
        "job_title": args.job_title,
        "hiring_manager_name": args.hiring_manager,
        **custom_content
    }
    
    # Generate PDF
    output_path = f"Cover_Letter_{args.company.replace(' ', '_')}.pdf"
    if fill_pdf_template("fillable_template.pdf", output_path, form_data):
        print(f"\n🎉 Cover letter ready: {output_path}")
    
if __name__ == "__main__":
    main()