import json
import re

def extract_entities(text: str, llm_client) -> dict:
    """Extracts entities (people, companies, products, events, metrics) from the text using LLM."""
    system_prompt = (
        "You are an expert information extraction assistant. Extract entities from the text.\n"
        "Respond ONLY with a valid JSON object. Do not include markdown code fences (like ```json) or any conversational text.\n"
        "If an entity category has no entities, return an empty list for that key.\n\n"
        "The JSON structure must be exactly as follows:\n"
        "{\n"
        "  \"people\": [ {\"name\": \"Name of Person\", \"type\": \"Person\", \"context_snippet\": \"Snippet of text where mentioned\"} ],\n"
        "  \"companies\": [ {\"name\": \"Company Name\", \"type\": \"Company\", \"context_snippet\": \"Snippet of text where mentioned\"} ],\n"
        "  \"products\": [ {\"name\": \"Product Name\", \"type\": \"Product\", \"context_snippet\": \"Snippet of text where mentioned\"} ],\n"
        "  \"events\": [ {\"name\": \"Event Name\", \"type\": \"Event\", \"context_snippet\": \"Snippet of text where mentioned\"} ],\n"
        "  \"metrics\": [ {\"name\": \"Metric Name\", \"type\": \"Metric\", \"context_snippet\": \"Snippet of text where mentioned\"} ]\n"
        "}"
    )
    
    prompt = f"Extract entities from this text:\n\n{text}"
    
    def clean_and_parse(response_text: str) -> dict:
        cleaned = response_text.strip()
        # Find first '{' and last '}'
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
        
        # Replace common LLM syntax mistakes if any, then load JSON
        return json.loads(cleaned)

    try:
        response = llm_client.completion(prompt=prompt, system_prompt=system_prompt)
        return clean_and_parse(response)
    except Exception as e:
        print(f"[WARNING] First entity extraction attempt failed: {e}. Retrying once...")
        try:
            response = llm_client.completion(prompt=prompt, system_prompt=system_prompt)
            return clean_and_parse(response)
        except Exception as retry_err:
            print(f"[ERROR] Repeated entity extraction failure: {retry_err}")
            return {
                "people": [],
                "companies": [],
                "products": [],
                "events": [],
                "metrics": []
            }

def extract_relationships(text: str, entities: list[dict], llm_client) -> list[dict]:
    """Identifies and extracts relationships between the provided entities from the text."""
    if not entities:
        return []
        
    entity_str = ", ".join([f"{e['name']} ({e['type']})" for e in entities])
    
    system_prompt = (
        "You are an expert information extraction assistant. Identify relationships between the provided entities based on the text.\n"
        "Respond ONLY with a valid JSON list. Do not include markdown code fences or conversational text.\n"
        "Allowed relationship types include: WORKS_FOR, COMPETES_WITH, LAUNCHED, FILED_PATENT, PARTNERED_WITH, MANAGED_BY, or a general relation.\n"
        "Identify and attach any temporal attributes (like 'date' or 'quarter') if mentioned in the context.\n\n"
        "JSON structure:\n"
        "[\n"
        "  {\n"
        "    \"from_entity\": \"Name of entity A\",\n"
        "    \"to_entity\": \"Name of entity B\",\n"
        "    \"relationship_type\": \"WORKS_FOR | COMPETES_WITH | LAUNCHED | etc.\",\n"
        "    \"date\": \"YYYY-MM-DD or empty\",\n"
        "    \"quarter\": \"e.g. Q2 2024 or empty\"\n"
        "  }\n"
        "]"
    )
    
    prompt = (
        f"Text:\n{text}\n\n"
        f"List of extracted entities:\n{entity_str}\n\n"
        "Extract all relationships between these entities."
    )
    
    def clean_and_parse(response_text: str) -> list[dict]:
        cleaned = response_text.strip()
        # Find first '[' and last ']'
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
        return json.loads(cleaned)

    try:
        response = llm_client.completion(prompt=prompt, system_prompt=system_prompt)
        return clean_and_parse(response)
    except Exception as e:
        print(f"[WARNING] First relationship extraction attempt failed: {e}. Retrying once...")
        try:
            response = llm_client.completion(prompt=prompt, system_prompt=system_prompt)
            return clean_and_parse(response)
        except Exception as retry_err:
            print(f"[ERROR] Repeated relationship extraction failure: {retry_err}")
            return []
