import json
import re
from openai import AzureOpenAI
from AgenticSummary.config import (
    API_KEY, AZURE_ENDPOINT, DEPLOYMENT_NAME, API_VERSION,
    MAX_TOKENS, TEMPERATURE, TOP_P, FREQUENCY_PENALTY, PRESENCE_PENALTY
)

# Initialize the Azure OpenAI client with API credentials and configuration settings
client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    azure_deployment=DEPLOYMENT_NAME,
    api_key=API_KEY,
    api_version=API_VERSION
)


def extract_topics(user_input):
    """
    Extracts relevant research topics from a user-provided sentence.
    The extracted topics are returned as a list of lists, where each inner list contains a single topic.

    Args:
        user_input (str): A sentence describing the type of papers the user wants to find.

    Returns:
        list: A list of lists, where each inner list contains a single extracted topic.
    """
    prompt = f"""
    Identify the main research topics from the following sentence. 
    Return only the extracted topics as a JSON array of strings.

    Example:
    Input: "I want to scrape papers about LLM and IR."
    Output: ["LLM", "IR"]

    Input: "I am interested in AI, deep learning, and robotics."
    Output: ["AI", "Deep Learning", "Robotics"]

    User Input:
    {user_input}

    Response:
    """

    chat_prompt = [
        {"role": "system", "content": "You are an expert in extracting research topics from text."},
        {"role": "user", "content": prompt}
    ]

    completion = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=chat_prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        frequency_penalty=FREQUENCY_PENALTY,
        presence_penalty=PRESENCE_PENALTY,
        stop=None,
        stream=False
    )

    # Extract and clean the response
    answer = completion.choices[0].message.content.strip()
    cleaned_answer = re.sub(r"^```json|```$", "", answer.strip()).strip()

    # Parse JSON response
    try:
        extracted_topics = json.loads(cleaned_answer)

        # Validate that the response is a proper list of strings
        if not isinstance(extracted_topics, list) or not all(isinstance(topic, str) for topic in extracted_topics):
            raise ValueError("Invalid format received from the model. Expected a list of topics.")

    except json.JSONDecodeError:
        raise ValueError("Could not parse the assistant's response as JSON.")

    return [[topic] for topic in extracted_topics]


def augment_keywords(keywords):
    """
    Expands each keyword group while preserving the input structure.
    Ensures the output remains a list of lists, where each inner list starts
    with the original topic followed by its synonyms and related terms.

    Args:
        keywords (list): A list of keyword groups, where each group is a list of related terms.

    Returns:
        list: A list of expanded keyword groups with synonyms, acronyms, and related terms.
    """
    # Convert keywords into a JSON string for inclusion in the prompt
    keywords_str = json.dumps(keywords)

    prompt = f"""
    Expand the following keyword groups by adding **closely related** terms while maintaining precision.
    For each keyword, include:
    - **Synonyms and variations**
    - **Acronyms**, ensuring they are **separated from full names**  
      - Correct: ["Natural Language Processing", "NLP"]  
      - Incorrect: ["Natural Language Processing (NLP)"]
    - **Technical jargon frequently associated with the topic**
    - **Domain-specific terminology and key concepts** from relevant research papers
    - **Popular methodologies, frameworks, models, and algorithms** strongly tied to the topic
    - **All words derived from the same root**, including verb forms, noun variations, and other morphological derivatives.
      - Example: If the keyword is "recommender", include "recommend", "recommendation", "recommendations", etc.


    ### **Strict Formatting Rules:**
    - **Include both singular and plural forms of each keyword and its expansions.**
      - Correct: ["Recommender System", "Recommender Systems", "Recommendation Engine", "Recommendation Engines"]
      - Incorrect: ["Recommender Systems", "Recommendation Engines"] (missing singular forms)
    - **Preserve acronyms separately** from their full names:
      - Correct: ["Large Language Model", "Large Language Models", "LLM", "LLMs"]
      - Incorrect: ["Large Language Models (LLMs)"]
    - **Avoid generic or ambiguous terms** that could lead to irrelevant matches.
    - **Do not include unrelated subfields** that shift the focus to a different topic.

    ### **Initial Keyword Groups:**
    {keywords_str}

    ### **Expected Response Format:**
    ```json
    [
        ["Original Keyword", "Original Keyword (Plural)", "Highly Relevant Synonym 1", "Highly Relevant Synonym 1 (Plural)", "Closely Related Concept 1", "Closely Related Concept 1 (Plural)", ..., "Technical Term N"],
        ["Another Keyword", "Another Keyword (Plural)", "Highly Relevant Synonym A", "Highly Relevant Synonym A (Plural)", "Closely Related Concept B", "Closely Related Concept B (Plural)", ..., "Technical Term M"]
    ]
    """

    chat_prompt = [
        {"role": "system", "content": "You are a helpful assistant that expands keyword groups."},
        {"role": "user", "content": prompt}
    ]

    completion = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=chat_prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        frequency_penalty=FREQUENCY_PENALTY,
        presence_penalty=PRESENCE_PENALTY,
        stop=None,
        stream=False
    )

    # Extract and clean the response
    answer = completion.choices[0].message.content.strip()
    cleaned_answer = re.sub(r"^```json|```$", "", answer.strip()).strip()

    # Parse the response into a structured JSON format
    try:
        augmented_keywords = json.loads(cleaned_answer)

        # Ensure the output is a properly formatted list of lists
        if not isinstance(augmented_keywords, list) or not all(isinstance(group, list) for group in augmented_keywords):
            raise ValueError("Invalid format received from the model. Expected a list of lists.")

    except json.JSONDecodeError:
        raise ValueError("Could not parse the assistant's response as JSON.")

    return augmented_keywords
