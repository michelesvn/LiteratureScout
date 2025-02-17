# LiteratureScout

LiteratureScout is a **web scraping and summarization toolkit** designed to automate the retrieval of conference papers, with the aim of generating **detailed and well-structured summaries**, and leveraging them to create a **mini survey of the state of the art** in the specific subject area they collectively pertain to.

## Project Structure

```
LiteratureScout/
    AgenticSummary/
        Output/
            State of the Art/
                state_of_the_art.pdf
            2025/
                summarized_pdf1.pdf
                summarized_pdf2.pdf
                [...]
            2024/
                [...]
            [...]
        .env
        agentic_aggregation.py
        agentic_summarization.py
        config.py
        main.py
    Scraper/
        Output/
            2025/
                pdf1.pdf
                pdf2.pdf
                [...]
            2024/
                [...]
            [...]
        Spider/
            AAAI_spider.py           
            ACL_spider.py            
            ACM_spider.py         
            base_spider.py          
            credentials.json        
            ICLR_spider.py
            ICML_spider.py
            IJCAI_spider.py          
            NeurIPS_spider.py        
            utils.py                 
        automatic_main.py            
        config.py                    
        interactive_main.py         
        keyword_handling.py
        nokeywords_automatic_main.py
    .gitignore
    LICENSE
    README.md             
    requirements.txt              
```

## Academic Context and Ethical Usage

LiteratureScout is the result of an academic research and development project conducted as part of a university coursework initiative.

Users are strongly encouraged to utilize this tool responsibly and in strict accordance with the terms of service and policies of the platforms from which data is retrieved. LiteratureScout does not circumvent paywalls, access restricted content, or engage in any form of unauthorized data extraction. The responsibility for ensuring compliance with legal and ethical guidelines, including respect for intellectual property rights and data access restrictions, lies entirely with the end user.

This project is intended for educational and research purposes only, and its developers disclaim any liability arising from misuse.