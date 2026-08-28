import os
import io
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

class ReportGenerator:
    @staticmethod
    def generate_pdf(
        query: str,
        answer: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generates a styled executive PDF analysis report and returns raw bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        
        # Custom palette & styles
        header_title_style = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1e293b")
        )
        
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'Body',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155")
        )

        meta_label_style = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.HexColor("#475569")
        )

        meta_val_style = ParagraphStyle(
            'MetaVal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor("#0f172a")
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("PROJECT CHRONOS", ParagraphStyle('SubHeader', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor("#6366f1"), leading=11)))
        story.append(Paragraph("Temporal Enterprise Intelligence Report", header_title_style))
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#6366f1"), spaceAfter=12))

        # 2. Metadata Summary Block
        if not metadata:
            metadata = {}
            
        gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        meta_table_data = [
            [
                Paragraph("<b>Query:</b>", meta_label_style),
                Paragraph(query, meta_val_style),
                Paragraph("<b>Date:</b>", meta_label_style),
                Paragraph(gen_time, meta_val_style)
            ],
            [
                Paragraph("<b>Classification:</b>", meta_label_style),
                Paragraph(", ".join(metadata.get("classification", ["FACTUAL"])), meta_val_style),
                Paragraph("<b>Timeframe:</b>", meta_label_style),
                Paragraph(str(metadata.get("timeframe") or "N/A"), meta_val_style)
            ]
        ]

        meta_table = Table(meta_table_data, colWidths=[80, 240, 60, 150])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 16))

        # 3. Synthesized Executive Findings
        story.append(Paragraph("Executive Summary & Synthesis", section_title_style))
        
        # Replace newlines in answer with proper paragraphs
        paragraphs = answer.strip().split("\n\n")
        for p in paragraphs:
            clean_p = p.replace("\n", "<br/>")
            story.append(Paragraph(clean_p, body_style))
            story.append(Spacer(1, 8))

        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

        # 4. Evidentiary Sources Table
        if sources:
            story.append(Paragraph("Cited Source Evidence & Chunks", section_title_style))
            
            src_table_data = [
                [
                    Paragraph("<b>Rank / Source</b>", meta_label_style),
                    Paragraph("<b>Relevance Score</b>", meta_label_style),
                    Paragraph("<b>Extracted Content Snippet</b>", meta_label_style)
                ]
            ]
            
            for idx, src in enumerate(sources[:6]):
                src_name = src.get("source", "vector")
                doc_name = src.get("metadata", {}).get("source") or f"Doc_{idx+1}"
                score = f"{src.get('score', 0.0):.4f}"
                text_snippet = src.get("text", "")[:180] + ("..." if len(src.get("text", "")) > 180 else "")
                
                src_table_data.append([
                    Paragraph(f"<b>#{idx+1}</b> {doc_name} ({src_name.upper()})", meta_val_style),
                    Paragraph(score, meta_val_style),
                    Paragraph(text_snippet, meta_val_style)
                ])

            src_table = Table(src_table_data, colWidths=[140, 80, 310])
            src_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(src_table)

        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @staticmethod
    def generate_excel(
        query: str,
        answer: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generates an Excel .xlsx report containing summary & retrieved evidence data."""
        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            # Sheet 1: Executive Summary
            summary_data = {
                "Field": ["Query", "Generated At", "Classifications", "Timeframe", "Synthesized Answer"],
                "Value": [
                    query,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    ", ".join(metadata.get("classification", [])) if metadata else "",
                    metadata.get("timeframe", "") if metadata else "",
                    answer
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name="Executive Summary", index=False)

            # Sheet 2: Cited Sources
            if sources:
                source_rows = []
                for idx, src in enumerate(sources):
                    meta = src.get("metadata", {})
                    source_rows.append({
                        "Rank": idx + 1,
                        "Source Type": src.get("source", ""),
                        "Document Name": meta.get("source", ""),
                        "Score": src.get("score", 0.0),
                        "Quarter": meta.get("quarter", ""),
                        "Content Snippet": src.get("text", "")
                    })
                df_sources = pd.DataFrame(source_rows)
                df_sources.to_excel(writer, sheet_name="Retrieved Sources", index=False)

        excel_bytes = buffer.getvalue()
        buffer.close()
        return excel_bytes
