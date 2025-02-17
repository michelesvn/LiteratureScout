from pdf2image import convert_from_path
import base64
import os
from fpdf import FPDF
import unicodedata
import re


class Agentic_Summarization:
    def __init__(self, input_path, output_path, deployment_name, client, pdf_dpi, image_quality,
                 max_tokens, temperature, top_p, frequency_penalty, presence_penalty):
        """
        Initializes the PDFProcessor with required parameters.

        Args:
            input_path (str): Path to the directory containing year-based folders with PDFs.
            output_path (str): Path to the directory where processed summaries will be saved.
            deployment_name (str): Azure OpenAI deployment name for API access.
            client (AzureOpenAI): Instance of the OpenAI client for API communication.
            pdf_dpi (int): Resolution (dots per inch) for converting PDFs to images.
            image_quality (int): Quality setting for image conversion (e.g., PNG format).
            max_tokens (int): Maximum number of tokens for AI-generated summaries.
            temperature (float): Controls response randomness; lower values make responses more deterministic.
            top_p (float): Probability threshold for nucleus sampling, influencing response diversity.
            frequency_penalty (float): Reduces the likelihood of repeating words or phrases.
            presence_penalty (float): Encourages introducing new concepts in responses.
        """
        self.input_path = input_path
        self.output_path = output_path
        self.deployment_name = deployment_name
        self.client = client
        self.pdf_dpi = pdf_dpi
        self.image_quality = image_quality
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty

    def convert_pdf_to_encoded_images(self, pdf_path, year_folder):
        """
        Converts a PDF file into images (one per page), saves them in the specified directory,
        and encodes them into Base64 format for further processing.

        Args:
            pdf_path (str): Path to the input PDF file.
            year_folder (str): Subfolder (e.g., year) within the output directory.

        Returns:
            tuple:
                - A list of dictionaries containing Base64-encoded images.
                - The path to the output directory where images are saved.
                - The filename of the processed PDF (without extension).
        """
        pdf_filename = os.path.basename(pdf_path).replace('.pdf', '')

        os.makedirs(self.output_path, exist_ok=True)

        # Convert the PDF into a list of images (one per page), with the specified DPI
        images = convert_from_path(pdf_path, dpi=self.pdf_dpi)

        output_year_path = os.path.join(self.output_path, year_folder)
        os.makedirs(output_year_path, exist_ok=True)

        encoded_images = []

        # Process each page of the PDF
        for page_num, img in enumerate(images, start=1):
            # Construct the output filename for the image, including page number
            output_image_filename = f"{pdf_filename}_page_{page_num}.png"
            image_path = os.path.join(output_year_path, output_image_filename)

            img.save(image_path, format="PNG", quality=self.image_quality)

            # Encode the saved image in Base64 format
            with open(image_path, "rb") as img_file:
                encoded_string = base64.b64encode(img_file.read()).decode("utf-8")

                # Append the encoded image as a dictionary, formatted for further use
                encoded_images.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{encoded_string}"}
                })

        return encoded_images, output_year_path, pdf_filename

    def generate_summary(self, encoded_images, pdf_filename):
        """
        Generates a structured summary of a scientific paper using Azure OpenAI GPT model.

        Args:
            encoded_images (list): List of dictionaries containing encoded images in Base64.
            pdf_filename (str): Name of the PDF file to be summarized.

        Returns:
            str: The generated summary of the paper.
        """
        # Initial content to instruct the model on the expected analysis structure
        content_list = [
            {
                "type": "text",
                "text": "Please analyze the provided scientific paper according to the comprehensive guide. "
                        "Ensure that each section is covered thoroughly and provide structured insights."
            }
        ]

        # Append encoded images to the content list for model processing
        content_list.extend(encoded_images)

        chat_prompt = [
            {
                "role": "system",
                "content": f"Title: Write the title {pdf_filename}\n\n"
                           "Section 1: Overview\n"
                           "Objective: Summarize the paper’s main focus, addressing the following:\n"
                           "Problem Statement: What issue is the paper addressing?\n"
                           "Research Question: What specific question or hypothesis is it attempting to answer?\n"
                           "Key Findings: Briefly outline the main discoveries or contributions.\n"
                           "Framework: Describe the theoretical or conceptual foundation.\n"
                           "Methodology and Design: Summarize the experimental design and approach.\n"
                           "Results and Discussion: What are the significant results, and how do they contribute to the field?\n"
                           "Future Directions: Note any questions or potential future research paths proposed by the authors.\n\n"
                           "Section 2: Detailed Paper Analysis\n"
                           "[Summary]: Write a one-paragraph summary covering the paper’s purpose and high-level findings.\n"
                           "[Novelty]: Describe unique or innovative aspects introduced by the authors and their impact on the field.\n"
                           "[Goals]: Clarify the paper’s primary objectives (e.g., developing a new model, offering a comparative analysis).\n"
                           "[Related Works]: Describe prior work the paper builds upon, noting specific studies for comparison.\n"
                           "[Motivation]: Explain the need for this study, particularly in light of unresolved issues in prior work.\n"
                           "[Problem Statement]: Define the problem the paper is aiming to solve.\n"
                           "[Theoretical Foundations]: Briefly outline the mathematical or conceptual basis for the proposed solution.\n"
                           "[Algorithm and Approach]: Provide a concise description of the algorithm or methods used, detailing any unique implementations or techniques.\n"
                           "[Experimental Design and Novelty]: Highlight innovative elements in the experimental setup or methodology that distinguish the study.\n"
                           "[Evaluation and Methodology]: Describe the experiment types and their objectives.\n"
                           "[Datasets]: List datasets used with sources and details on data preprocessing.\n"
                           "[Baseline Comparisons]: List and describe baseline models or benchmarks.\n"
                           "[Metrics]: Identify evaluation metrics used.\n"
                           "[Results]: Summarize performance against baselines.\n"
                           "[Ablation Studies]: Indicate which components significantly contributed to results.\n"
                           "[Limitations and Future Directions]: Discuss any constraints and suggested areas for future exploration.\n"
                           "[Reproducibility]: Note if code or resources are available for replication.\n"
                           "[Ethical Considerations]: Mention any ethical issues raised or addressed in the paper.\n"
                           "[Conclusion]: Offer a brief, critical opinion on the work’s impact, strengths, and relevance."
            },
            {
                "role": "user",
                "content": content_list
            }
        ]

        try:
            completion = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=chat_prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                stop=None,
                stream=False
            )

            output_text = completion.choices[0].message.content.strip()
            return output_text

        except Exception as e:
            print(f"Error generating summary: {e}")

    @staticmethod
    def format_text(pdf, line):
        """
        Formats and writes a line of text to a PDF, applying styles based on markdown-style syntax.

        Args:
            pdf (FPDF): The PDF object where the text will be written.
            line (str): The text line to be formatted.
        """
        # Normalize text to standard form
        unicodedata.normalize('NFKC', line).strip()

        # Apply heading formatting based on Markdown syntax
        if re.match(r'^#### ', line):
            pdf.set_font("Arial", style="B", size=14)
            line = re.sub(r'^#### ', '', line)
        elif re.match(r'^### ', line):
            pdf.set_font("Arial", style="B", size=14)
            line = re.sub(r'^### ', '', line)
        elif re.match(r'^## ', line):
            pdf.set_font("Arial", style="B", size=14)
            line = re.sub(r'^## ', '', line)
        elif re.match(r'^# ', line):
            pdf.set_font("Arial", style="B", size=14)
            line = re.sub(r'^# ', '', line)
        else:
            # Remove Markdown-style emphasis while preserving the text
            line = re.sub(r'\*\*\*\*(.*?)\*\*\*\*', r'\1', line)
            line = re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', line)
            line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
            line = re.sub(r'\*(.*?)\*', r'\1', line)

            # Set font style to bold if emphasis markers were detected
            if '**' in line or '*' in line:
                pdf.set_font("Arial", style="B", size=12)
            else:
                pdf.set_font("Arial", size=12)

        # Write formatted text to PDF, ensuring encoding compatibility
        pdf.multi_cell(0, 10, line.encode('latin-1', 'replace').decode('latin-1'))

    def convert_text_to_pdf(self, summary_text, pdf_file_name, output_dir):
        """
        Converts a structured text summary into a formatted PDF file.

        Args:
            summary_text (str): The text summary to be written into the PDF.
            pdf_file_name (str): The base name of the output PDF file (without extension).
            output_dir (str): The directory where the PDF file will be saved.

        Returns:
            str: The path to the generated PDF file.
        """
        os.makedirs(output_dir, exist_ok=True)
        pdf_output_path = os.path.join(output_dir, f"{pdf_file_name}_summary.pdf")

        # Initialize PDF document
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Process each line of the summary text with formatting
        for line in summary_text.split("\n"):
            self.format_text(pdf, line)

        pdf.output(pdf_output_path)
        print(f"Summary saved: '{pdf_output_path}'")

    @staticmethod
    def remove_temp_images(pdf_file, output_year_path, encoded_images):
        """
        Deletes temporary image files created during PDF processing.

        Args:
            pdf_file (str): The name of the PDF file (e.g., "document.pdf").
            output_year_path (str): The directory where the images are stored.
            encoded_images (list): A list of encoded images, determining the number of pages.

        Returns:
            None
        """
        # Iterate through the number of images, corresponding to PDF pages
        for page_num in range(1, len(encoded_images) + 1):
            # Construct the expected filename for each page image
            output_image_filename = f"{pdf_file.replace('.pdf', '')}_page_{page_num}.png"
            image_path = os.path.join(output_year_path, output_image_filename)

            # Remove the image file if it exists
            if os.path.exists(image_path):
                os.remove(image_path)

    def process_pdfs_by_year(self, selected_years):
        """
        Processes all PDF files within year-based subfolders inside the input directory.

        Args:
            selected_years (list): List of years to process.
        """
        # Iterate through year-based subdirectories in the input path
        for year_folder in os.listdir(self.input_path):
            if not year_folder.isdigit() or int(year_folder) not in selected_years:
                print(f"Skipping year: {year_folder}")
                continue

            year_path = os.path.join(self.input_path, year_folder)

            # Ensure the directory is valid before processing
            if os.path.isdir(year_path):
                for pdf_file in os.listdir(year_path):
                    if pdf_file.lower().endswith(".pdf"):
                        pdf_path = os.path.join(year_path, pdf_file)

                        summary_filename = pdf_file.replace('.pdf', '_summary.pdf')
                        output_year_path = os.path.join(self.output_path, year_folder)
                        summary_path = os.path.join(output_year_path, summary_filename)

                        # Skip processing if a summary already exists
                        if os.path.exists(summary_path):
                            print(f"Summary already exists for: {pdf_file} - Skipping.")
                            continue

                        # Convert the PDF to Base64-encoded images
                        encoded_images, output_year_path, pdf_filename = self.convert_pdf_to_encoded_images(pdf_path,
                                                                                                            year_folder)

                        # Generate a structured summary from the encoded images
                        output_summary = self.generate_summary(encoded_images, pdf_filename)

                        # Save the generated summary as a PDF file
                        self.convert_text_to_pdf(output_summary, pdf_file.replace('.pdf', ''), output_year_path)

                        # Remove temporary images used during the process
                        self.remove_temp_images(pdf_file, output_year_path, encoded_images)
