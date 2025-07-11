from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from pinecone import Pinecone
import json
import os

from LLMProvider.BaseProvider import LLMProvider
from .Delimeters import DELIMETERS



class QueryContext(BaseModel):
    author: Optional[str] = None
    tags: List[str] = []
    date_info: Optional[Dict[str, Any]] = None
    semantic_query: Optional[str] = None
    confidence: float = 0.0


    


class ParseQuery:
    def __init__(self,llm_provider:LLMProvider):
            self.llm_provider = llm_provider
            self.current_year = datetime.now().year
            self.current_month = datetime.now().month
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.prompt_path = os.path.join(base_dir, '..', 'prompts', 'QueryParser.txt')

    def load_parsing_prompt(self,query):
        with open(self.prompt_path) as p:
            parsing_prompt_template = p.read()
        parsing_prompt = parsing_prompt_template.replace(DELIMETERS.query,query)
        parsing_prompt = parsing_prompt.replace(DELIMETERS.last_year,str(self.current_year-1))
        parsing_prompt = parsing_prompt.replace(DELIMETERS.this_year,str(self.current_year))
        return parsing_prompt

    async def parse_query(self,query):
        prompt = self.load_parsing_prompt(query)
        response = await self.llm_provider.generate_response(prompt=prompt)
        try:
            parsed_data = json.loads(response)
            context = QueryContext(
                author=parsed_data.get('author'),
                tags=parsed_data.get('tags', []),
                date_info=parsed_data.get('date_info'),
                semantic_query=query,
                confidence=parsed_data.get('confidence', 0.0)
            )
            return context
        except Exception as e :
            print("Not Found Valid Json as response")
            return QueryContext()



class PineconeAgent:

    def __init__(self,llm_provider):
        self.llm_provider = llm_provider
        self.query_parser = ParseQuery(self.llm_provider)
        self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(base_dir, '..', 'prompts', 'RAGSearch.txt')
        self.rag_prompt_template = self.load_RAG_prompt_template(prompt_path)


    
    def load_RAG_prompt_template(self,prompt_path):
        with open(prompt_path) as f:
            template_rag_prompt = f.read()
        return template_rag_prompt
        


    def build_date_filter(self, date_info: Dict[str, Any]) -> dict:
        if not date_info:
            return {}
        filter_dict = {}
        if 'year' in date_info:
            filter_dict['published_year'] = {'$eq': date_info['year']}
        if 'month' in date_info:
            filter_dict['published_month'] = {'$eq': date_info['month']}
        if 'day' in date_info:
            filter_dict['published_day'] = {'$eq': date_info['day']}
        return filter_dict
    
    def generate_filter(self, context: QueryContext)->dict:
        filter_dict = {}
        if context.author:
            filter_dict['author'] = context.author
        if context.tags:
            filter_dict['tags'] = {'$in': context.tags}
        if context.date_info:
            date_filter = self.build_date_filter(context.date_info)
            filter_dict.update(date_filter)
        return filter_dict

    async def retrieve_records_from_pinecone(self,filter,query,index,pinecone_namespace):
        try:
            response = index.search(
                    namespace = pinecone_namespace, 
                    query={"inputs": {"text": query,}, "top_k": 5,"filter":filter})
            similar_record =  [res['fields'] for res in response['result']['hits']]
        except Exception as e:
            print(f"Errror in retrieving records :{e}")
            similar_record = []
        return similar_record


    async def process_query(self,query:str):
        query_context = await self.query_parser.parse_query(query)
        filter_dict =  self.generate_filter(query_context)
        result = {
                'filter': filter_dict,
                'confidence': query_context.confidence,
                'parsed_query': query
            }
        return result

    async def search_record(self,query:str,pinecone_index:str,pinecone_namespace:str):
        try:
            pinecone_desc = self.pc.describe_index(pinecone_index)
            pinecone_host_url = pinecone_desc['host']  
            pinecone_namespace = pinecone_namespace
            index = self.pc.Index(host=pinecone_host_url)
            query_context = await self.query_parser.parse_query(query)
            filter_dict =  self.generate_filter(query_context)
            if 'tag' in filter_dict:
                for k,vals in filter_dict.items():
                    filter_dict['tag'][k] = [v.lower().strip().replace(" ","") for v in vals]
            search_results = await self.retrieve_records_from_pinecone(filter_dict,query,index,pinecone_namespace)
            return search_results
        except Exception as e:
            raise Exception(f"Errror in searching records: {e}")

    async def generate_RAG_response(self,query:str,pinecone_index:str,pinecone_namespace:str):
            response = None
            try:
                context_results = await self.search_record(query,pinecone_index,pinecone_namespace)
                if context_results:
                    context_str = "/n".join([c['text'] for c in context_results])
                    rag_prompt = self.rag_prompt_template.replace(DELIMETERS.combined_context,context_str)
                    rag_prompt = rag_prompt.replace(DELIMETERS.query,query)
                    response = await self.llm_provider.generate_response(prompt=rag_prompt,is_json_response=False)
                    return response
            except Exception as e:
                raise Exception("Error in Generating RAG Response : e")

        
def create_pinecone_agent(llm_provider:str):
    if llm_provider =='gemini':
            from LLMProvider.GeminiProvider import GeminiProvider
            gemini = GeminiProvider()
            return PineconeAgent(gemini)
    else:
        raise Exception(f"Please add {llm_provider} as LLM provider . Available llm_providers : ['gemini']")

    
    


    


    
    


    

    

    

