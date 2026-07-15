from langchain_community.tools import DuckDuckGoSearchRun

class WebSearchFallback:
    def __init__(self):
        try:
            self.search_tool = DuckDuckGoSearchRun()
        except Exception as e:
            print(f"[ERROR] Failed to initialize DuckDuckGoSearchRun: {e}")
            import traceback
            traceback.print_exc()
            self.search_tool = None

    def search(self, query: str) -> list[dict]:
        """Performs a free web search using DuckDuckGo with fallback support."""
        print(f"[*] [Web Fallback] Querying DuckDuckGo for: '{query}'")
        try:
            if self.search_tool:
                result_text = self.search_tool.run(query)
                return [{
                    "id": "web_search_fallback_result",
                    "text": result_text,
                    "metadata": {
                        "source": "duckduckgo_web_search",
                        "type": "external"
                    },
                    "score": 0.85,
                    "source": "web"
                }]
            else:
                print("[WARNING] DuckDuckGoSearchRun was not initialized. Using simulated web fallback.")
        except Exception as e:
            print(f"[WARNING] DuckDuckGo search failed: {e}. Using simulated web fallback.")
            import traceback
            traceback.print_exc()
            
        return [{
            "id": "web_search_fallback_mock",
            "text": (
                f"Web Search Fallback context for: '{query}'. "
                "Chronos Corp is an enterprise AI software organization specializing in temporal-aware RAG pipelines and self-correcting query architectures. "
                "Chronos Corp's chief competitor in this space is Apex Data Systems."
            ),
            "metadata": {
                "source": "simulated_web_fallback",
                "type": "external"
            },
            "score": 0.5,
            "source": "web"
        }]
