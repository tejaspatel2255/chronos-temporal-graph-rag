import os
from pathlib import Path
import pandas as pd

class StructuredSearcher:
    def __init__(self):
        self.structured_dir = Path(__file__).parent.parent.parent / "data" / "structured"

    def search(self, query: str, entities: list[str] = None, timeframe: str = None, metrics: list[str] = None) -> list[dict]:
        """Queries CSV files in data/structured/ matching criteria and returns matching rows as candidates."""
        results = []
        if not self.structured_dir.exists():
            return []
            
        csv_files = list(self.structured_dir.glob("*.csv"))
        for file in csv_files:
            try:
                df = pd.read_csv(file)
                filtered_df = df.copy()
                
                # Filter by entity/company
                if entities:
                    company_cols = [c for c in filtered_df.columns if "company" in c.lower() or "organization" in c.lower()]
                    if company_cols:
                        col = company_cols[0]
                        mask = filtered_df[col].astype(str).apply(
                            lambda val: any(e.lower() in val.lower() or val.lower() in e.lower() for e in entities)
                        )
                        filtered_df = filtered_df[mask]
                        
                # Filter by timeframe/quarter
                if timeframe:
                    time_cols = [c for c in filtered_df.columns if "quarter" in c.lower() or "date" in c.lower() or "period" in c.lower()]
                    if time_cols:
                        col = time_cols[0]
                        mask = filtered_df[col].astype(str).apply(
                            lambda val: timeframe.lower() in val.lower() or val.lower() in timeframe.lower()
                        )
                        filtered_df = filtered_df[mask]
                        
                # Filter by metrics
                if metrics:
                    metric_cols = [c for c in filtered_df.columns if "metric" in c.lower() or "name" in c.lower()]
                    if metric_cols:
                        col = metric_cols[0]
                        mask = filtered_df[col].astype(str).apply(
                            lambda val: any(m.lower() in val.lower() or val.lower() in m.lower() for m in metrics)
                        )
                        filtered_df = filtered_df[mask]
                
                # Format matching rows as text candidates
                if len(filtered_df) < len(df) and not filtered_df.empty:
                    for idx, row in filtered_df.iterrows():
                        row_dict = row.to_dict()
                        row_text = ", ".join([f"{k}: {v}" for k, v in row_dict.items()])
                        results.append({
                            "id": f"struct_{file.name}_{idx}",
                            "text": f"Structured Data [{file.name}]: {row_text}",
                            "metadata": {
                                "source": file.name,
                                "row_data": row_dict,
                                "quarter": row_dict.get("quarter", "") or row_dict.get("date", ""),
                            },
                            "score": 0.9,
                            "source": "structured"
                        })
            except Exception as e:
                print(f"[WARNING] Error reading/searching CSV {file.name}: {e}")
                
        return results
