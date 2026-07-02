"""
Report Generator for Incident Analysis

Generates PDF, JSON, and CSV exports of incident reports.
"""

import json
import csv
from io import StringIO
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors


class ReportGenerator:
    """Generate incident reports in multiple formats."""

    def __init__(self, memory_manager):
        """Initialize report generator with memory manager."""
        self.memory_manager = memory_manager

    def generate_report(
        self,
        incident_id: str,
        format: str = 'json'
    ) -> Optional[Dict[str, Any]]:
        """
        Generate report in specified format.

        Args:
            incident_id: Incident ID to generate report for
            format: Output format (pdf, json, csv)

        Returns:
            Dictionary with 'data' (bytes), 'filename', 'content_type'
        """
        # Get incident from memory
        incidents = self.memory_manager.long_term.get('incidents', [])
        incident = None

        for inc in incidents:
            if inc.get('incident_id') == incident_id:
                incident = inc
                break

        if not incident:
            print(f"❌ Incident not found: {incident_id}")
            return None

        # Generate based on format
        if format.lower() == 'pdf':
            return self._generate_pdf(incident)
        elif format.lower() == 'json':
            return self._generate_json(incident)
        elif format.lower() == 'csv':
            return self._generate_csv(incident)
        else:
            print(f"❌ Unsupported format: {format}")
            return None

    def _generate_pdf(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Generate PDF report."""
        try:
            from io import BytesIO

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )

            elements = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f2937'),
                spaceAfter=6,
                alignment=1
            )
            elements.append(Paragraph('Incident Report', title_style))
            elements.append(Spacer(1, 0.2*inch))

            # Basic Info - only include fields that have actual data
            info_data = [
                ['Incident ID', incident.get('incident_id', 'N/A')],
                ['Severity', incident.get('severity', 'N/A')],
                ['Status', incident.get('status', 'Investigating')],
                ['Timestamp', incident.get('timestamp', 'N/A')],
            ]
            if incident.get('confidence') is not None and incident.get('confidence') != 'N/A':
                info_data.append(['Confidence', f"{incident.get('confidence')}%"])
            if incident.get('affected_users') and incident.get('affected_users') not in ['N/A', 'Unknown']:
                info_data.append(['Affected Users', incident.get('affected_users')])
            if incident.get('duration') and incident.get('duration') not in ['N/A', 'Unknown']:
                info_data.append(['Duration', incident.get('duration')])
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 0.3*inch))

            # Summary
            elements.append(Paragraph('Summary', styles['Heading2']))
            elements.append(Paragraph(
                incident.get('summary', 'No summary available'),
                styles['Normal']
            ))
            elements.append(Spacer(1, 0.2*inch))

            # Root Cause
            elements.append(Paragraph('Root Cause', styles['Heading2']))
            elements.append(Paragraph(
                incident.get('root_cause', 'Not determined'),
                styles['Normal']
            ))
            elements.append(Spacer(1, 0.2*inch))

            # Business Impact - only if real data (not default/hallucinated)
            business_impact = incident.get('business_impact')
            if business_impact and business_impact not in ['N/A', 'Unknown', incident.get('summary')]:
                elements.append(Paragraph('Business Impact', styles['Heading2']))
                elements.append(Paragraph(business_impact, styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))

            # Technical Impact - only if real data (not default/hallucinated)
            technical_impact = incident.get('technical_impact')
            if technical_impact and technical_impact not in ['N/A', 'Unknown', 'See root cause']:
                elements.append(Paragraph('Technical Impact', styles['Heading2']))
                if isinstance(technical_impact, list):
                    for impact in technical_impact:
                        elements.append(Paragraph(f"• {impact}", styles['Normal']))
                else:
                    elements.append(Paragraph(str(technical_impact), styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))

            # Affected Services
            if incident.get('affected_services'):
                elements.append(Paragraph('Affected Services', styles['Heading2']))
                services_text = ', '.join(incident['affected_services'])
                elements.append(Paragraph(services_text, styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))

            # Evidence/Retrieved Docs - only if actual docs were retrieved
            retrieved_docs = incident.get('retrieved_docs')
            if retrieved_docs and isinstance(retrieved_docs, list) and len(retrieved_docs) > 0:
                # Filter out empty/placeholder docs
                real_docs = [d for d in retrieved_docs if d and str(d).strip() and str(d) not in ['N/A', 'Unknown']]
                if real_docs:
                    elements.append(Paragraph('Evidence Retrieved', styles['Heading2']))
                    for doc in real_docs:
                        elements.append(Paragraph(f"• {doc}", styles['Normal']))
                    elements.append(Spacer(1, 0.2*inch))

            # Immediate Actions
            if incident.get('recommendations'):
                elements.append(PageBreak())
                elements.append(Paragraph('Immediate Actions', styles['Heading2']))
                for i, rec in enumerate(incident['recommendations'], 1):
                    elements.append(Paragraph(f"{i}. {rec}", styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))

            # Timeline - only if actual events exist
            timeline = incident.get('timeline')
            if timeline and isinstance(timeline, list) and len(timeline) > 0:
                elements.append(Paragraph('Timeline', styles['Heading2']))
                for event in timeline:
                    if isinstance(event, dict):
                        time = event.get('time', '')
                        event_text = event.get('event', '')
                    else:
                        event_text = str(event)
                        time = ''
                    if event_text:
                        elements.append(Paragraph(f"• {time}: {event_text}" if time else f"• {event_text}", styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))

            # Events by Severity - only if actual events exist
            events_by_severity = incident.get('events_by_severity')
            if events_by_severity and isinstance(events_by_severity, dict) and len(events_by_severity) > 0:
                # Filter out empty severity buckets
                has_events = any(isinstance(events, list) and len(events) > 0 for events in events_by_severity.values())
                if has_events:
                    elements.append(Paragraph('Events by Severity', styles['Heading2']))
                    for severity, events in events_by_severity.items():
                        if isinstance(events, list) and len(events) > 0:
                            elements.append(Paragraph(f"<b>{severity}:</b>", styles['Normal']))
                            for event in events:
                                elements.append(Paragraph(f"  • {event}", styles['Normal']))
                    elements.append(Spacer(1, 0.2*inch))

            # Similar Incidents - only if actual similar incidents found
            similar_incidents = incident.get('memory_context', {}).get('similar_incidents')
            if similar_incidents and isinstance(similar_incidents, list) and len(similar_incidents) > 0:
                real_similar = [s for s in similar_incidents if s and str(s).strip() and str(s) not in ['N/A', 'Unknown']]
                if real_similar:
                    elements.append(Paragraph('Similar Incidents from History', styles['Heading2']))
                    for sim in real_similar:
                        elements.append(Paragraph(f"• {sim}", styles['Normal']))
                    elements.append(Spacer(1, 0.2*inch))

            # Next Steps - only if actual steps exist
            next_steps = incident.get('next_steps')
            if next_steps and isinstance(next_steps, list) and len(next_steps) > 0:
                real_steps = [s for s in next_steps if s and str(s).strip() and str(s) not in ['N/A', 'Unknown']]
                if real_steps:
                    elements.append(Paragraph('Next Steps', styles['Heading2']))
                    for i, step in enumerate(real_steps, 1):
                        elements.append(Paragraph(f"{i}. {step}", styles['Normal']))
                    elements.append(Spacer(1, 0.2*inch))

            # Generated info
            elements.append(Spacer(1, 0.3*inch))
            gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elements.append(Paragraph(
                f'<i>Report generated on {gen_time}</i>',
                styles['Normal']
            ))

            # Build PDF
            doc.build(elements)
            pdf_bytes = buffer.getvalue()

            return {
                'data': pdf_bytes,
                'filename': f"{incident['incident_id']}_report.pdf",
                'content_type': 'application/pdf'
            }
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            return None

    def _generate_json(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON report."""
        try:
            report_data = {
                'incident_id': incident.get('incident_id'),
                'generated_at': datetime.now().isoformat(),
                'incident': incident
            }

            json_str = json.dumps(report_data, indent=2)
            json_bytes = json_str.encode('utf-8')

            return {
                'data': json_bytes,
                'filename': f"{incident['incident_id']}_report.json",
                'content_type': 'application/json'
            }
        except Exception as e:
            print(f"❌ JSON generation failed: {e}")
            return None

    def _generate_csv(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Generate CSV report."""
        try:
            output = StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(['Field', 'Value'])

            # Data rows
            for key, value in incident.items():
                if isinstance(value, (list, dict)):
                    value = json.dumps(value)
                writer.writerow([key, value])

            csv_str = output.getvalue()
            csv_bytes = csv_str.encode('utf-8')

            return {
                'data': csv_bytes,
                'filename': f"{incident['incident_id']}_report.csv",
                'content_type': 'text/csv'
            }
        except Exception as e:
            print(f"❌ CSV generation failed: {e}")
            return None

    def save_report_file(
        self,
        incident_id: str,
        format: str,
        report_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Save generated report to disk.

        Args:
            incident_id: Incident ID
            format: Report format
            report_data: Dictionary with 'data' (bytes) and 'filename'

        Returns:
            Path to saved file
        """
        try:
            # Create incident folder
            incident_dir = self.memory_manager.reports_dir / incident_id
            incident_dir.mkdir(exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"report_{format}_{timestamp}.{self._get_extension(format)}"
            file_path = incident_dir / filename

            # Write file
            with open(file_path, 'wb') as f:
                f.write(report_data['data'])

            file_size = file_path.stat().st_size

            # Save metadata to SQLite
            self.memory_manager.save_report(
                incident_id=incident_id,
                format=format,
                file_path=str(file_path),
                file_size=file_size
            )

            print(f"✅ Report file saved: {file_path}")
            return str(file_path)
        except Exception as e:
            print(f"❌ Failed to save report file: {e}")
            return None

    def _get_extension(self, format: str) -> str:
        """Get file extension for format."""
        extensions = {
            'pdf': 'pdf',
            'json': 'json',
            'csv': 'csv'
        }
        return extensions.get(format.lower(), 'txt')
