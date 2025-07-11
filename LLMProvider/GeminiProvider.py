from google import genai
from google.genai import types

from .BaseProvider import LLMProvider



class GeminiProvider(LLMProvider):
    def __init__(self):
        pass

    async def generate_response(self, prompt, is_json_response = True):
        try:
            client = genai.Client()
            if is_json_response:
                response = client.models.generate_content(
                    model="gemini-2.5-flash", 
                    contents=prompt,
                    config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                ))
            else:
                response = client.models.generate_content(
                    model="gemini-2.5-flash", 
                    contents=prompt,
                    config=types.GenerateContentConfig(
                ))

            # client = genai.Client()
            # response = client.models.generate_content(
            #     model="gemini-2.5-flash", 
            #     contents=prompt,
            #     config=types.GenerateContentConfig(
            #     response_mime_type='application/json',
            #     response_schema=response_schema
            # ))
               
            return response.text
        except Exception as e :
            raise Exception(f"GEMINI_Error:{e}")

