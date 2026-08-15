export interface Citation {
  source: string;
  chunk_id: string;
}

export interface ContextUsed {
  id?: string;
  source: string;
  text: string;
}

export interface AttemptLog {
  retry_index: number;
  query_used: string;
  confidence: number;
  reasoning: string;
}

export interface QueryResponse {
  answer: string;
  confidence_score: number;
  is_valid: boolean;
  retries: number;
  citations: Citation[];
  context_used: ContextUsed[];
  attempts_log: AttemptLog[];
}

export function generateReportMarkdown(question: string, result: QueryResponse): string {
  const timestamp = new Date().toLocaleString('en-US', {
    dateStyle: 'full',
    timeStyle: 'medium',
  });

  let md = `# PROJECT CHRONOS EXECUTIVE BRIEFING\n\n`;
  md += `> **Query Analyzed:** ${question}\n`;
  md += `> **Generated At:** ${timestamp}\n`;
  md += `> **System Confidence Score:** ${result.confidence_score}%\n`;
  md += `> **Grounding Status:** ${result.is_valid ? 'Validated & Grounded' : 'Unvalidated Warning'}\n`;
  md += `> **Self-Correction Cycles:** ${result.retries} iteration(s)\n\n`;
  md += `---\n\n`;

  md += `## 1. Executive Summary & Findings\n\n`;
  md += `${result.answer}\n\n`;
  md += `---\n\n`;

  md += `## 2. Sources & Citations\n\n`;
  if (result.citations.length === 0) {
    md += `*No formal document citations recorded for this query response.*\n\n`;
  } else {
    md += `| Index | Source Document / Domain | Chunk ID | Retrieval Type |\n`;
    md += `| :---: | :--- | :---: | :---: |\n`;
    result.citations.forEach((c, idx) => {
      const isWeb = c.source === 'duckduckgo_web_search';
      md += `| ${idx + 1} | \`${c.source}\` | \`${c.chunk_id}\` | ${isWeb ? 'External Web Fallback' : 'Internal GraphRAG'} |\n`;
    });
    md += `\n`;
  }
  md += `---\n\n`;

  md += `## 3. Grounding Context Payload\n\n`;
  if (result.context_used.length === 0) {
    md += `*No context blocks retrieved.*\n\n`;
  } else {
    result.context_used.forEach((ctx, idx) => {
      md += `### Block ${idx + 1}: ${ctx.source} (ID: ${ctx.id || 'N/A'})\n`;
      md += `\`\`\`text\n${ctx.text}\n\`\`\`\n\n`;
    });
  }

  if (result.attempts_log.length > 0) {
    md += `---\n\n`;
    md += `## 4. Self-Correction & Rewrite Audit Trail\n\n`;
    result.attempts_log.forEach((log) => {
      md += `* **Attempt #${log.retry_index + 1}:** Confidence ${log.confidence}%\n`;
      md += `  * **Rewritten Query:** \`${log.query_used}\`  \n`;
      md += `  * **Failure Reasoning:** *${log.reasoning}*  \n\n`;
    });
  }

  md += `---\n\n`;
  md += `*Report generated automatically by Project Chronos Self-Correcting Temporal Enterprise Analyst.*`;

  return md;
}

export function downloadMarkdownReport(question: string, result: QueryResponse) {
  const markdownText = generateReportMarkdown(question, result);
  const blob = new Blob([markdownText], { type: 'text/markdown;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  
  const sanitizedTitle = (question || 'report')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .slice(0, 35);
    
  link.href = url;
  link.setAttribute('download', `Chronos_Report_${sanitizedTitle}.md`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function exportPDFReport(question: string, result: QueryResponse) {
  const timestamp = new Date().toLocaleString('en-US', {
    dateStyle: 'full',
    timeStyle: 'medium',
  });

  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    alert('Please allow popups to export PDF executive report.');
    return;
  }

  const citationsHTML = result.citations.map((c, idx) => `
    <tr>
      <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: center;">${idx + 1}</td>
      <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #1e293b;">${c.source}</td>
      <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; font-family: monospace; font-size: 11px;">${c.chunk_id}</td>
      <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">
        <span style="display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 600; background-color: ${c.source === 'duckduckgo_web_search' ? '#e0f2fe; color: #0369a1;' : '#e0e7ff; color: #4338ca;'}" >
          ${c.source === 'duckduckgo_web_search' ? 'External Fallback' : 'Internal GraphRAG'}
        </span>
      </td>
    </tr>
  `).join('');

  const attemptsHTML = result.attempts_log.map((log) => `
    <div style="margin-bottom: 12px; padding: 10px; border-radius: 6px; background-color: #f8fafc; border: 1px solid #e2e8f0;">
      <div style="font-weight: 700; font-size: 12px; color: #475569; margin-bottom: 4px;">Attempt #${log.retry_index + 1} &bull; Confidence: ${log.confidence}%</div>
      <div style="font-family: monospace; font-size: 11px; background-color: #ffffff; padding: 6px; border-radius: 4px; border: 1px solid #cbd5e1; margin-bottom: 4px;">${log.query_used}</div>
      <div style="font-size: 11px; font-style: italic; color: #64748b;">"${log.reasoning}"</div>
    </div>
  `).join('');

  // Simple HTML renderer for markdown paragraphs
  const formattedAnswer = result.answer
    .replace(/\n\n/g, '</p><p>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>');

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Chronos Executive Report - ${question}</title>
      <style>
        @media print {
          body { -webkit-print-color-adjust: exact; }
          .no-print { display: none; }
        }
        body {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          color: #0f172a;
          line-height: 1.6;
          padding: 40px;
          max-width: 850px;
          margin: 0 auto;
          background-color: #ffffff;
        }
        .header {
          border-bottom: 3px solid #4f46e5;
          padding-bottom: 16px;
          margin-bottom: 24px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .title { font-size: 22px; font-weight: 800; color: #1e1b4b; text-transform: uppercase; letter-spacing: 0.5px; }
        .subtitle { font-size: 12px; color: #64748b; margin-top: 2px; }
        .meta-box {
          background-color: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 24px;
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
          font-size: 12px;
        }
        .meta-label { color: #64748b; font-weight: 600; font-size: 11px; text-transform: uppercase; }
        .meta-val { color: #0f172a; font-weight: 700; margin-top: 2px; }
        .badge {
          display: inline-block;
          padding: 3px 10px;
          border-radius: 12px;
          font-size: 11px;
          font-weight: 700;
        }
        .badge-success { background-color: #dcfce7; color: #15803d; }
        .badge-warning { background-color: #fef3c7; color: #b45309; }
        .section-title {
          font-size: 14px;
          font-weight: 800;
          color: #334155;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          border-bottom: 1px solid #cbd5e1;
          padding-bottom: 6px;
          margin-top: 24px;
          margin-bottom: 12px;
        }
        .report-body { font-size: 13px; color: #334155; }
        table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12px; }
        th { background-color: #f1f5f9; text-align: left; padding: 8px; border-bottom: 2px solid #cbd5e1; color: #475569; font-weight: 700; }
        .footer {
          margin-top: 40px;
          border-top: 1px solid #e2e8f0;
          padding-top: 16px;
          font-size: 10px;
          color: #94a3b8;
          text-align: center;
        }
      </style>
    </head>
    <body>
      <div class="no-print" style="margin-bottom: 20px; text-align: right;">
        <button onclick="window.print()" style="background-color: #4f46e5; color: white; border: none; padding: 10px 20px; font-weight: 600; border-radius: 6px; cursor: pointer;">
          🖨️ Print / Save as PDF
        </button>
      </div>

      <div class="header">
        <div>
          <div class="title">Project Chronos</div>
          <div class="subtitle">Self-Correcting Temporal Enterprise Analyst &bull; Executive Briefing</div>
        </div>
        <div style="text-align: right; font-size: 11px; color: #64748b;">
          <strong>Date:</strong> ${timestamp}
        </div>
      </div>

      <div class="meta-box">
        <div style="grid-column: span 2;">
          <div class="meta-label">Analyzed Question</div>
          <div class="meta-val" style="font-size: 14px; color: #4f46e5;">"${question}"</div>
        </div>
        <div>
          <div class="meta-label">Grounding & Factuality Status</div>
          <div class="meta-val">
            <span class="badge ${result.is_valid ? 'badge-success' : 'badge-warning'}">
              ${result.is_valid ? 'Validated & Grounded' : 'Low-Grounding Warning'}
            </span>
          </div>
        </div>
        <div>
          <div class="meta-label">Confidence Score</div>
          <div class="meta-val">${result.confidence_score}%</div>
        </div>
      </div>

      <div class="section-title">1. Executive Synthesized Findings</div>
      <div class="report-body">
        <p>${formattedAnswer}</p>
      </div>

      <div class="section-title">2. Sources & Citations Audit</div>
      ${result.citations.length === 0 ? '<p style="font-size: 12px; color: #64748b; italic;">No formal source citations referenced.</p>' : `
        <table>
          <thead>
            <tr>
              <th style="text-align: center;">#</th>
              <th>Source File / Domain</th>
              <th>Chunk ID</th>
              <th>Retrieval Type</th>
            </tr>
          </thead>
          <tbody>
            ${citationsHTML}
          </tbody>
        </table>
      `}

      ${result.attempts_log.length > 0 ? `
        <div class="section-title">3. Self-Correction & Rewrite Audit Trail</div>
        ${attemptsHTML}
      ` : ''}

      <div class="footer">
        Confidential Enterprise Document &bull; Generated by Project Chronos GraphRAG Engine
      </div>
    </body>
    </html>
  `;

  printWindow.document.write(html);
  printWindow.document.close();
  printWindow.focus();
}
