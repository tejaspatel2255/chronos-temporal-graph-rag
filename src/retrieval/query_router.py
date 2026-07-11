import json
import re

def classify_query(query: str, llm_client) -> dict:
    """Classifies the query and extracts entities, timeframe, metrics, and paraphrases."""
    system_prompt = (
        "You are an expert query analysis assistant.\n"
        "Analyze the user's query and respond ONLY with a valid JSON object. Do not include markdown code fences or conversational text.\n\n"
        "The JSON structure must be exactly as follows:\n"
        "{\n"
        "  \"classification\": [\"FACTUAL\" | \"ANALYTICAL\" | \"TEMPORAL\"], // List of matching categories (can be multiple)\n"
        "  \"entities\": [\"string\"], // Entities mentioned in the query\n"
        "  \"timeframe\": \"string\", // Timeframe indicator or reference period (e.g. 'Q2 2024', 'recent', or empty string)\n"
        "  \"metrics\": [\"string\"], // Key metrics asked about (e.g. 'revenue', 'funding', 'growth', etc.)\n"
        "  \"paraphrased_queries\": [\"string\"] // 2-3 paraphrased variations of the original query to improve recall\n"
        "}"
    )

    prompt = f"Analyze this query:\n\n{query}"

    def clean_and_parse(response_text: str) -> dict:
        cleaned = response_text.strip()
        # Find first '{' and last '}'
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
        return json.loads(cleaned)

    try:
        response = llm_client.completion(prompt=prompt, system_prompt=system_prompt)
        return clean_and_parse(response)
    except Exception as e:
        print(f"[WARNING] First query classification attempt failed: {e}. Retrying once...")
        try:
            response = llm_client.completion(prompt=prompt, system_prompt=system_prompt)
            return clean_and_parse(response)
        except Exception as retry_err:
            print(f"[ERROR] Repeated query classification failure: {retry_err}")
            # Fallback structure
            return {
                "classification": ["FACTUAL"],
                "entities": [],
                "timeframe": "",
                "metrics": [],
                "paraphrased_queries": [query]
            }
