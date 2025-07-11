import os
import asyncio
from dotenv import load_dotenv
from LLMProvider.GeminiProvider import GeminiProvider
from Agents.PineconeAgent import PineconeAgent


load_dotenv()

async def get_response():

    gemini = GeminiProvider()
    pinecode_index = os.getenv('PINECONE_INDEX_NAME')
    pinecone_namespace = os.getenv('PINECONE_NAMESPACE')
    pinecone_agent = PineconeAgent(gemini,pinecode_index,pinecone_namespace)
    response = await pinecone_agent.generate_RAG_response("summarize the article written by Akainu")
#     response = await gemini.generate_response("hii")

    print(response)

if __name__ == "__main__":
    asyncio.run(get_response())