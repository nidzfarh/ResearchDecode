import google.generativeai as genai
from dotenv import load_dotenv
import os
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash")

def generate_response(paper_text):
    prompt = f"""
    Analyze this research paper and return:

    SUMMARY:
    short summary

    CORE_IDEA:
    explain the core concept

    TECH_STACK:
    suggested technologies

    IMPLEMENTATION:
    step-by-step implementation plan

    FOLDER_STRUCTURE:
    example project folder structure

    Research Paper:
    {paper_text[:12000]}
    """
    response = model.generate_content(prompt)
    return response.text