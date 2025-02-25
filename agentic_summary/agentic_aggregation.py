import subprocess
from PyPDF2 import PdfReader
import os


class Agentic_Aggregation:
    def __init__(self, output_path, deployment_name, client, max_tokens, temperature, top_p, frequency_penalty,
                 presence_penalty, max_pdfs_per_file):
        """
        Initialize the Agentic Aggregation class.

        Args:
            output_path (str): Directory where output files are stored.
            deployment_name (str): Azure OpenAI deployment name.
            client (AzureOpenAI): Azure OpenAI client instance.
            max_tokens (int): Maximum number of tokens for AI response.
            temperature (float): Sampling temperature for response generation.
            top_p (float): Nucleus sampling probability.
            frequency_penalty (float): Penalty for token repetition.
            presence_penalty (float): Encouragement for new content generation.
            max_pdfs_per_file (int): Maximum number of PDFs processed per summary file.
        """
        self.output_path = output_path
        self.deployment_name = deployment_name
        self.client = client
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.max_pdfs_per_file = max_pdfs_per_file

        self.states_of_art_path = os.path.join(self.output_path, "state_of_the_art")
        os.makedirs(self.states_of_art_path, exist_ok=True)

    def clean_directory(self):
        """
        Removes all files from the specified directory except for 'state_of_the_art.pdf'.

        This ensures that only the final compiled PDF remains, preventing clutter from temporary or
        intermediate files generated during processing.
        """
        for file in os.listdir(self.states_of_art_path):
            file_path = os.path.join(self.states_of_art_path, file)

            # Preserve only the final PDF, delete all other files
            if file != "state_of_the_art.pdf":
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting {file}: {e}")

    def aggregate_summaries(self):
        """
        Aggregates the extracted text from all summary PDF files into structured text files,
        ensuring summaries are grouped into multiple text files when exceeding a predefined limit.

        Saves the aggregated summaries in the designated output directory.

        """
        all_summaries_text = ""
        pdf_count = 0
        file_index = 1

        # Traverse the output directory to locate all summary PDF files
        for root, _, files in os.walk(self.output_path):
            for file in sorted(files):
                if file.lower().endswith("_summary.pdf"):
                    pdf_count += 1
                    pdf_path = os.path.join(root, file)

                    # Append the summary number and file name as a heading
                    all_summaries_text += f"### Summary {pdf_count}: {file}\n\n"

                    # Extract text content from the PDF
                    with open(pdf_path, "rb") as pdf_file:
                        reader = PdfReader(pdf_file)
                        for page in reader.pages:
                            extracted_text = page.extract_text()
                            if extracted_text:
                                all_summaries_text += extracted_text + "\n\n"

                    all_summaries_text += "----------------------------\n\n"

                    # If the maximum number of PDFs per file is reached, save and start a new file
                    if pdf_count % self.max_pdfs_per_file == 0:
                        text_file_name = f"aggregate{file_index}.txt"
                        text_file_path = os.path.join(self.states_of_art_path, text_file_name)

                        with open(text_file_path, "w", encoding="utf-8") as text_file:
                            text_file.write(all_summaries_text)

                        all_summaries_text = ""
                        file_index += 1

        # Save the remaining summaries if any content remains unsaved
        if all_summaries_text.strip():
            text_file_name = f"aggregate{file_index}.txt"
            text_file_path = os.path.join(self.states_of_art_path, text_file_name)

            with open(text_file_path, "w", encoding="utf-8") as text_file:
                text_file.write(all_summaries_text)

        if pdf_count == 0:
            print("No summary content found in the PDF files.")

    def summarize_aggregates(self):
        """
        Processes aggregated text summaries, generates a structured scientific survey
        using an AI model, and saves the output.

        Iterates through preprocessed aggregated text files, extracts relevant research paper
        details, and formulates a structured summary using OpenAI.

        Saves the generated summary into a new text file for further use.
        """
        for file in sorted(os.listdir(self.states_of_art_path)):
            if file.startswith("aggregate") and file.endswith(".txt"):
                file_path = os.path.join(self.states_of_art_path, file)
                file_index = file.replace("aggregate", "").replace(".txt", "")

                with open(file_path, "r", encoding="utf-8") as f:
                    all_summaries_text = f.read()

                if not all_summaries_text.strip():
                    print(f"Skipping empty file: {file}")
                    continue

                # Extracts paper titles and counts the actual number of summarized papers
                paper_titles = []
                for line in all_summaries_text.split("\n"):
                    if line.startswith("### Summary "):
                        title = line.split(": ", 1)[-1].strip()
                        paper_titles.append(title)

                total_papers = len(paper_titles)

                prompt = [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert research assistant with extensive knowledge in analyzing and synthesizing scientific literature. "
                            "Your task is to generate a comprehensive survey based on multiple summarized research papers. The survey should highlight "
                            "key trends, methodologies, gaps, and future directions in the field."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            "Follow this structured reasoning process step by step:\n\n"
                            "### Step 1: Identify Key Themes Across Papers\n"
                            "1. **Extract Key Topics:** Identify the primary topics across all papers and cluster them into broad research themes.\n"
                            "2. **Determine Subtopics:** For each theme, categorize papers into finer-grained subtopics (e.g., methodologies, evaluation metrics, applications).\n"
                            "3. **Highlight Commonalities and Differences:** Compare how different papers approach similar problems, methodologies, or experimental designs.\n\n"
                            "### Step 2: Summarize the State of the Art\n"
                            "1. **What is the field about?** Provide a high-level introduction to the research area covered in the survey.\n"
                            "2. **Historical Perspective:** If relevant, briefly outline the evolution of key ideas leading up to current research trends.\n"
                            "3. **Recent Advances:**\n"
                            "   - What are the latest breakthroughs or dominant approaches?\n"
                            "   - Which methodologies are commonly used?\n"
                            "   - What are the strongest experimental results?\n"
                            "4. **Comparison of Approaches:** Highlight different schools of thought or methodologies, pointing out trade-offs, strengths, and weaknesses.\n\n"
                            "### Step 3: Analyze Research Methodologies\n"
                            "For each category of research papers:\n"
                            "1. **Theoretical Foundations:** Summarize the core theoretical frameworks used across papers.\n"
                            "2. **Experimental Designs:**\n"
                            "   - What are the typical experimental setups?\n"
                            "   - What datasets are frequently used?\n"
                            "   - How are models evaluated (metrics, baselines)?\n"
                            "3. **Key Contributions:**\n"
                            "   - Which models, techniques, or insights were most impactful?\n"
                            "   - What novel approaches were introduced?\n"
                            "4. **Ablation Studies & Insights:**\n"
                            "   - Which techniques showed the most significant improvements?\n"
                            "   - What limitations or challenges did researchers highlight?\n\n"
                            "### Step 4: Identify Gaps & Open Research Questions\n"
                            "1. **Unsolved Problems:** Identify challenges or unresolved questions mentioned across multiple papers.\n"
                            "2. **Common Limitations:**\n"
                            "   - Are there general weaknesses in current models or methodologies?\n"
                            "   - Are there scalability, generalization, or fairness concerns?\n"
                            "3. **Future Directions:**\n"
                            "   - What new research areas are emerging?\n"
                            "   - What improvements or innovations are suggested across multiple papers?\n\n"
                            "### Step 5: Structure the Survey Paper\n"
                            "Generate a structured scientific survey using the following format:\n\n"
                            "#### Title: _(Make it concise yet informative)_\n\n"
                            "#### Abstract:\n"
                            "Summarize the key findings, contributions, and scope of the survey.\n\n"
                            "#### 1. Introduction\n"
                            "- Define the research field.\n"
                            "- Explain why this survey is needed.\n"
                            "- Outline key themes and contributions.\n\n"
                            "#### 2. Taxonomy of Research\n"
                            "- Organize papers into **major research themes**.\n"
                            "- Provide a **diagram or table** summarizing the categorization.\n\n"
                            "#### 3. Methodologies and Techniques\n"
                            "- Compare different methodologies, frameworks, and models.\n"
                            "- Discuss datasets, baselines, and evaluation metrics.\n\n"
                            "#### 4. Comparative Analysis of Results\n"
                            "- Highlight performance across different approaches.\n"
                            "- Discuss trends in effectiveness and limitations.\n\n"
                            "#### 5. Research Gaps & Future Directions\n"
                            "- Identify open research questions.\n"
                            "- Suggest possible future research avenues.\n\n"
                            "#### 6. Conclusion\n"
                            "- Provide final insights.\n"
                            "- Emphasize key takeaways from the survey.\n\n"
                            "#### 7. List of the Used Research Papers\n"
                            "*This section MUST be included in the response.*\n\n"
                            f"**Total number of summarized papers:** {total_papers}\n"
                            "**Numbered list of papers used in this summary:**\n\n"
                            f"{paper_titles}\n\n"
                            "---\n"
                            "*Make sure that the full list is included exactly as provided above, keeping each title on a separate line.*\n"
                            "### Final output Format\n"
                            "- Ensure clarity, conciseness, and coherence.\n"
                            "- Use structured paragraphs and bullet points for easy readability.\n"
                            "- Include tables, figures, and examples where necessary.\n\n"
                            "### Prompt Execution\n"
                            "Given the following corpus of summarized papers:\n"
                            "```\n"
                            f"{all_summaries_text}\n"
                            "```\n"
                            "Generate a comprehensive scientific survey by following the reasoning steps outlined above. The output should be structured, well-reasoned, and academically rigorous.\n"
                        )
                    }
                ]

                try:
                    completion = self.client.chat.completions.create(
                        model=self.deployment_name,
                        messages=prompt,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        top_p=self.top_p,
                        frequency_penalty=self.frequency_penalty,
                        presence_penalty=self.presence_penalty,
                        stop=None,
                        stream=False
                    )

                    summarized_aggregate = completion.choices[0].message.content.strip()

                    # Saves the summarized content into a new text file
                    summary_file_name = f"summarized_aggregate{file_index}.txt"
                    summary_file_path = os.path.join(self.states_of_art_path, summary_file_name)

                    with open(summary_file_path, "w", encoding="utf-8") as summary_file:
                        summary_file.write(summarized_aggregate)

                except Exception as e:
                    print(f"Error generating the summarized aggregate: {e}")

    def aggregate_aggregates(self):
        """
        Aggregates all summarized scientific surveys into a final consolidated summary.

        Iterates through all 'summarized_aggregate' text files, appends their content
        into a structured final aggregate, and saves the result.

        Returns:
            str: The final aggregated summary.
        """
        final_aggregate = ""
        summary_files = []

        for file in sorted(os.listdir(self.states_of_art_path)):
            if file.startswith("summarized_aggregate") and file.endswith(".txt"):
                file_path = os.path.join(self.states_of_art_path, file)
                summary_files.append(file_path)

                with open(file_path, "r", encoding="utf-8") as f:
                    summary_text = f.read()
                    if summary_text.strip():
                        final_aggregate += f"### Summary from {file}\n\n{summary_text}\n\n"
                        final_aggregate += "----------------------------\n\n"

        # Save the final aggregated summary if content exists
        if final_aggregate.strip():
            final_aggregate_file_path = os.path.join(self.states_of_art_path, "final_aggregate.txt")

            with open(final_aggregate_file_path, "w", encoding="utf-8") as final_aggregate_file:
                final_aggregate_file.write(final_aggregate)

        return final_aggregate

    def summarize_final_aggregate(self, final_aggregate):
        """
        Generates a structured state-of-the-art survey from the final aggregated summaries.

        This function utilizes an AI model to analyze multiple summarized research papers
        and produce a comprehensive scientific survey, following a predefined structure.

        Args:
            final_aggregate (str): The compiled text of all summarized research papers.

        Returns:
            str: The generated state-of-the-art summary.
        """
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are an expert research assistant with extensive knowledge in analyzing and synthesizing scientific literature. "
                    "Your task is to generate a comprehensive survey based on multiple summarized research papers. The survey should highlight "
                    "key trends, methodologies, gaps, and future directions in the field."
                )
            },
            {
                "role": "user",
                "content": (
                    "Follow this structured reasoning process step by step:\n\n"
                    "### Step 1: Identify Key Themes Across Papers\n"
                    "1. **Extract Key Topics:** Identify the primary topics across all papers and cluster them into broad research themes.\n"
                    "2. **Determine Subtopics:** For each theme, categorize papers into finer-grained subtopics (e.g., methodologies, evaluation metrics, applications).\n"
                    "3. **Highlight Commonalities and Differences:** Compare how different papers approach similar problems, methodologies, or experimental designs.\n\n"
                    "### Step 2: Summarize the State of the Art\n"
                    "1. **What is the field about?** Provide a high-level introduction to the research area covered in the survey.\n"
                    "2. **Historical Perspective:** If relevant, briefly outline the evolution of key ideas leading up to current research trends.\n"
                    "3. **Recent Advances:**\n"
                    "   - What are the latest breakthroughs or dominant approaches?\n"
                    "   - Which methodologies are commonly used?\n"
                    "   - What are the strongest experimental results?\n"
                    "4. **Comparison of Approaches:** Highlight different schools of thought or methodologies, pointing out trade-offs, strengths, and weaknesses.\n\n"
                    "### Step 3: Analyze Research Methodologies\n"
                    "For each category of research papers:\n"
                    "1. **Theoretical Foundations:** Summarize the core theoretical frameworks used across papers.\n"
                    "2. **Experimental Designs:**\n"
                    "   - What are the typical experimental setups?\n"
                    "   - What datasets are frequently used?\n"
                    "   - How are models evaluated (metrics, baselines)?\n"
                    "3. **Key Contributions:**\n"
                    "   - Which models, techniques, or insights were most impactful?\n"
                    "   - What novel approaches were introduced?\n"
                    "4. **Ablation Studies & Insights:**\n"
                    "   - Which techniques showed the most significant improvements?\n"
                    "   - What limitations or challenges did researchers highlight?\n\n"
                    "### Step 4: Identify Gaps & Open Research Questions\n"
                    "1. **Unsolved Problems:** Identify challenges or unresolved questions mentioned across multiple papers.\n"
                    "2. **Common Limitations:**\n"
                    "   - Are there general weaknesses in current models or methodologies?\n"
                    "   - Are there scalability, generalization, or fairness concerns?\n"
                    "3. **Future Directions:**\n"
                    "   - What new research areas are emerging?\n"
                    "   - What improvements or innovations are suggested across multiple papers?\n\n"
                    "### Step 5: Structure the Survey Paper\n"
                    "Generate a structured scientific survey using the following format:\n\n"
                    "#### Title: _(Make it concise yet informative)_\n\n"
                    "#### Abstract:\n"
                    "Summarize the key findings, contributions, and scope of the survey.\n\n"
                    "#### 1. Introduction\n"
                    "- Define the research field.\n"
                    "- Explain why this survey is needed.\n"
                    "- Outline key themes and contributions.\n\n"
                    "#### 2. Taxonomy of Research\n"
                    "- Organize papers into **major research themes**.\n"
                    "- Provide a **diagram or table** summarizing the categorization.\n\n"
                    "#### 3. Methodologies and Techniques\n"
                    "- Compare different methodologies, frameworks, and models.\n"
                    "- Discuss datasets, baselines, and evaluation metrics.\n\n"
                    "#### 4. Comparative Analysis of Results\n"
                    "- Highlight performance across different approaches.\n"
                    "- Discuss trends in effectiveness and limitations.\n\n"
                    "#### 5. Research Gaps & Future Directions\n"
                    "- Identify open research questions.\n"
                    "- Suggest possible future research avenues.\n\n"
                    "#### 6. Conclusion\n"
                    "- Provide final insights.\n"
                    "- Emphasize key takeaways from the survey.\n\n"
                    "### Final output Format\n"
                    "- Ensure clarity, conciseness, and coherence.\n"
                    "- Use structured paragraphs and bullet points for easy readability.\n"
                    "- Include **tables, figures, and examples** where necessary.\n\n"
                    "### Prompt Execution\n"
                    "Given the following corpus of summarized papers:\n"
                    "```\n"
                    f"{final_aggregate}\n"
                    "```\n"
                    "Generate a comprehensive scientific survey by following the reasoning steps outlined above. The output should be structured, well-reasoned, and academically rigorous.\n"
                    "Additionally, **do not include section 7 'List of the Used Research Papers'** in the final document, even if it appears in the provided summaries.\n"
                )
            }
        ]

        try:
            completion = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                stop=None,
                stream=False
            )

            state_of_the_art = completion.choices[0].message.content.strip()
            print("\nState-of-the-art summary generated successfully.\n")

            # Save the final state-of-the-art summary in a text file
            state_of_the_art_file_path = os.path.join(self.states_of_art_path, "state_of_the_art.txt")

            with open(state_of_the_art_file_path, "w", encoding="utf-8") as summary_file:
                summary_file.write(state_of_the_art)

            return state_of_the_art

        except Exception as e:
            print(f"Error generating state-of-the-art summary: {e}")

    def convert_txt_to_latex(self, txt_input):
        """
        Converts a structured plain text input into a fully formatted and compilable LaTeX document.

        Args:
            txt_input (str): Either the path to a text file or a string containing structured text.

        Returns:
            str: The path to the generated LaTeX (.tex) file.
        """
        # Define the LaTeX output file path
        tex_file_path = os.path.join(self.states_of_art_path, "state_of_the_art.tex")

        # Read input content from a file if txt_input is a file path
        if os.path.exists(txt_input):
            with open(txt_input, "r", encoding="utf-8") as f:
                txt_content = f.read()
        else:
            txt_content = txt_input

        prompt = [
            {
                "role": "system",
                "content": (
                    "You are a LaTeX expert specializing in scientific and technical document formatting. "
                    "Your task is to take structured plain text input and convert it into a **fully formatted, structured, and compilable LaTeX document**. "
                    "The output **must be pure LaTeX code** without additional comments, markdown formatting, or explanations."
                )
            },
            {
                "role": "user",
                "content": (
                    "Convert the following structured text into a **fully formatted and compilable LaTeX document**. "
                    "Follow these rules strictly:\n\n"

                    "### **LaTeX Document Setup**\n"
                    "- The document **must start** with `\\documentclass[a4paper,12pt]{article}`.\n"
                    "- Include the following essential packages:\n"
                    "  ```latex\n"
                    "  \\usepackage[utf8]{inputenc}\n"
                    "  \\usepackage{graphicx}\n"
                    "  \\usepackage{hyperref}\n"
                    "  \\usepackage{amsmath, amssymb}\n"
                    "  \\usepackage{enumitem}\n"
                    "  \\usepackage[T1]{fontenc}\n"
                    "  \\usepackage{booktabs}\n"
                    "  \\usepackage{longtable}\n"
                    "  \\usepackage{array}\n"
                    "  ```\n"
                    "- The document **must** include `\\title{}`, `\\author{}`, and `\\date{\\today}`.\n"
                    "- Ensure the document starts with `\\begin{document}` and ends with `\\end{document}`.\n"

                    "### **Sectioning and Headings**\n"
                    "- Convert **`#` headings** to `\\section{}`.\n"
                    "- Convert **`##` subheadings** to `\\subsection{}`.\n"
                    "- Convert **`###` subsubheadings** to `\\subsubsection{}`.\n"
                    "- Wrap the abstract in `\\begin{abstract} ... \\end{abstract}`.\n"

                    "### **Lists Handling**\n"
                    "- Convert bullet lists (`- item`) to:\n"
                    "  ```latex\n"
                    "  \\begin{itemize}\n"
                    "      \\item First item\n"
                    "      \\item Second item\n"
                    "  \\end{itemize}\n"
                    "  ```\n"
                    "- Convert numbered lists (`1. item`) to:\n"
                    "  ```latex\n"
                    "  \\begin{enumerate}\n"
                    "      \\item First item\n"
                    "      \\item Second item\n"
                    "  \\end{enumerate}\n"
                    "  ```\n"

                    "### **Tables Formatting**\n"
                    "- Convert markdown tables (`| Col1 | Col2 | Col3 |`) into properly formatted LaTeX tables.\n"
                    "- Ensure **the table appears exactly where it is declared** by using `\\usepackage{placeins}` and `\\FloatBarrier`.\n"
                    "- Force tables to remain in place by using `\\begin{table}[H]` with `\\usepackage{float}`.\n"
                    "- Correct table formatting:\n"
                    "  ```latex\n"
                    "  \\usepackage{placeins}  % Add in preamble\n"
                    "  \\usepackage{float}      % Add in preamble\n"
                    "  \n"
                    "  \\FloatBarrier  % Forces the table to stay before the next section\n"
                    "  \\begin{table}[H]\n"
                    "  \\begin{center}\n"
                    "  \\renewcommand{\\arraystretch}{1.3}\n"
                    "  \\begin{tabular}{|p{5cm}|p{9cm}|}\n"
                    "  \\hline\n"
                    "  \\textbf{Theme} & \\textbf{Subtopics} \\\\\n"
                    "  \\hline\n"
                    "  Multimodal Retrieval & Fashion retrieval, visual-textual integration \\\\\n"
                    "  \\hline\n"
                    "  Conversational Systems & Conversational recommenders, persuasive chatbots \\\\\n"
                    "  \\hline\n"
                    "  Bias and Fairness & Name-based bias, ethical implications \\\\\n"
                    "  \\hline\n"
                    "  Methodological Innovations & Unsupervised training, ensemble methods \\\\\n"
                    "  \\hline\n"
                    "  Quantum Computing & Applications in IR and RS \\\\\n"
                    "  \\hline\n"
                    "  Visualization and Recommendations & Data visualization, explainability \\\\\n"
                    "  \\hline\n"
                    "  \\end{tabular}\n"
                    "  \\caption{Summary of Research Themes}\n"
                    "  \\end{center}\n"
                    "  \\end{table}\n"
                    "  ```\n"

                    "### **Special Character Handling**\n"
                    "- Escape **special LaTeX characters**: `&`, `%`, `$`, `{}`, `_`, `#`, `\\`.\n"
                    "- Ensure that **math expressions** are enclosed in `$...$` or `\\begin{equation} ... \\end{equation}`.\n"

                    "### **output Formatting Rules**\n"
                    "- The **output must be pure LaTeX**.\n"
                    "- **DO NOT** include markdown formatting like ` ```latex ` or ` ``` `.\n"
                    "- **DO NOT** include extra text like 'Here is the LaTeX document...'.\n"
                    "- Ensure no missing `\\begin{}` or `\\end{}` environments.\n\n"

                    "### **Structured Input Text to Convert**\n"
                    "```\n"
                    f"{txt_content}\n"
                    "```\n\n"

                    "### **Generate a fully structured and compilable LaTeX document based on the above instructions.**"
                )
            }
        ]

        try:
            completion = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                stop=None,
                stream=False
            )

            latex_output = completion.choices[0].message.content.strip()

            with open(tex_file_path, "w", encoding="utf-8") as tex_file:
                tex_file.write(latex_output)

            return tex_file_path

        except Exception as e:
            print(f"Error during LaTeX generation: {e}")

    def convert_latex_to_pdf(self):
        """
        Converts the LaTeX file in the 'state_of_the_art' directory into a PDF.
        The generated PDF is saved in the same directory as 'state_of_the_art.pdf'.

        Returns:
            str: The path to the generated PDF file, or None if the conversion fails.
        """
        tex_file_path = os.path.join(self.states_of_art_path, "state_of_the_art.tex")
        pdf_file_path = os.path.join(self.states_of_art_path, "state_of_the_art.pdf")

        if not os.path.exists(tex_file_path):
            print(f"Error: LaTeX file not found: {tex_file_path}")

        try:
            # Run the Tectonic compiler to generate the PDF
            subprocess.run(["tectonic", tex_file_path, "--outdir", self.states_of_art_path], check=True)

            # Validate if the PDF file was successfully generated
            if os.path.exists(pdf_file_path):
                return pdf_file_path
            else:
                print("Error: PDF file was not created.")

        except subprocess.CalledProcessError as e:
            print(f"Error during LaTeX to PDF conversion: {e}")

    def summarize_summaries(self):
        """
        Executes the full summarization pipeline:
        1. Cleans the directory by removing unnecessary files.
        2. Aggregates individual summaries into grouped text files.
        3. Generates summarized versions of the aggregated summaries.
        4. Combines all summarized aggregates into a final aggregated document.
        5. Produces a final structured state-of-the-art summary.
        6. Converts the final summary into a LaTeX document.
        7. Compiles the LaTeX document into a PDF.
        8. Cleans the directory by removing unnecessary files.
        """
        try:
            # Remove unnecessary files before starting the process
            self.clean_directory()

            # Aggregate individual summaries into text files
            self.aggregate_summaries()

            # Summarize the aggregated text files
            self.summarize_aggregates()

            # Combine all summarized aggregates into a final comprehensive summary
            final_aggregate = self.aggregate_aggregates()

            # Generate a structured state-of-the-art summary from the final aggregate
            state_of_the_art = self.summarize_final_aggregate(final_aggregate)

            # Convert the final summary into a LaTeX document
            self.convert_txt_to_latex(state_of_the_art)

            # Compile the LaTeX document into a PDF
            self.convert_latex_to_pdf()

            # Remove unnecessary files before starting the process
            self.clean_directory()

            print("\nSummarization pipeline completed successfully.")

        except Exception as e:
            print(f"\nAn error occurred during the summarization process: {e}")
