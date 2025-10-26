"""
HTML Reporter
=============

Generate interactive HTML reports with visualizations.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from mfaa.reporter.base_reporter import BaseReporter
from mfaa.models import Timeline, TimelineEntry, Pattern
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


class HTMLReporter(BaseReporter):
    """Generate interactive HTML reports with charts, timeline, and graphs."""

    def __init__(
        self,
        include_metadata: bool = True,
        template_dir: Optional[Path] = None
    ):
        """
        Initialize HTMLReporter.

        Args:
            include_metadata: Include generation metadata
            template_dir: Custom template directory (optional)
        """
        super().__init__(include_metadata)

        # Setup Jinja2 environment
        if template_dir and template_dir.exists():
            self.template_dir = template_dir
        else:
            # Use default templates directory
            self.template_dir = Path(__file__).parent / 'templates'

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

        logger.debug(f"HTMLReporter initialized with template dir: {self.template_dir}")

    def generate(
        self,
        timeline: Timeline,
        output_path: Path,
        open_browser: bool = False,
        theme: str = 'light'
    ) -> None:
        """
        Generate interactive HTML report.

        Args:
            timeline: Timeline object
            output_path: Path to save HTML file
            open_browser: Auto-open in browser
            theme: Color theme ('light' or 'dark')
        """
        logger.info(f"Generating HTML report: {output_path}")

        self._validate_timeline(timeline)
        self._ensure_output_directory(output_path)

        # Prepare data for template
        template_data = self._prepare_template_data(timeline, theme)

        # Render template
        template = self.env.get_template('report.html')
        html_content = template.render(**template_data)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"HTML report generated successfully: {output_path}")

        # Open in browser if requested
        if open_browser:
            self._open_in_browser(output_path)

    def _prepare_template_data(
        self,
        timeline: Timeline,
        theme: str
    ) -> Dict[str, Any]:
        """
        Prepare all data for HTML template.

        Args:
            timeline: Timeline object
            theme: Color theme

        Returns:
            Dictionary with all template data
        """
        data = {
            'theme': theme,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': self._build_summary(timeline),
            'timeline_data': self._prepare_timeline_data(timeline),
            'charts_data': self._prepare_charts_data(timeline),
            'patterns_data': self._prepare_patterns_data(timeline),
            'events_table': self._prepare_events_table(timeline),
            'correlation_graph': self._prepare_correlation_graph(timeline),
            'statistics': timeline.statistics
        }

        if self.include_metadata:
            data['metadata'] = self._prepare_metadata(timeline)

        return data

    def _build_summary(self, timeline: Timeline) -> Dict[str, Any]:
        """
        Build executive summary.

        Args:
            timeline: Timeline object

        Returns:
            Summary dictionary
        """
        entries = timeline.entries

        if not entries:
            return {
                'total_events': 0,
                'critical_events': 0,
                'patterns_detected': 0,
                'time_range': 'N/A'
            }

        # Count by priority
        critical = sum(1 for e in entries if e.priority_category == 'CRITICAL')
        high = sum(1 for e in entries if e.priority_category == 'HIGH')
        medium = sum(1 for e in entries if e.priority_category == 'MEDIUM')
        low = sum(1 for e in entries if e.priority_category == 'LOW')

        # Time range
        timestamps = [e.event.timestamp for e in entries]
        earliest = min(timestamps)
        latest = max(timestamps)
        duration_hours = (latest - earliest).total_seconds() / 3600

        # Severity classification
        if critical > 0 or any(p.severity == 'CRITICAL' for p in timeline.patterns):
            overall_severity = 'CRITICAL'
            severity_class = 'danger'
        elif high > 0 or any(p.severity == 'HIGH' for p in timeline.patterns):
            overall_severity = 'HIGH'
            severity_class = 'warning'
        elif medium > 0:
            overall_severity = 'MEDIUM'
            severity_class = 'info'
        else:
            overall_severity = 'LOW'
            severity_class = 'success'

        return {
            'total_events': len(entries),
            'critical_events': critical,
            'high_events': high,
            'medium_events': medium,
            'low_events': low,
            'patterns_detected': len(timeline.patterns),
            'time_range': f"{earliest.strftime('%Y-%m-%d %H:%M')} - {latest.strftime('%Y-%m-%d %H:%M')}",
            'duration_hours': f"{duration_hours:.1f}",
            'overall_severity': overall_severity,
            'severity_class': severity_class
        }

    def _prepare_timeline_data(self, timeline: Timeline) -> str:
        """
        Prepare data for interactive timeline visualization (Vis.js format).

        Args:
            timeline: Timeline object

        Returns:
            JSON string for Vis.js timeline
        """
        items = []

        for entry in timeline.entries:
            event = entry.event

            # Determine color by priority
            color_map = {
                'CRITICAL': '#dc3545',
                'HIGH': '#fd7e14',
                'MEDIUM': '#ffc107',
                'LOW': '#28a745'
            }
            color = color_map.get(entry.priority_category, '#6c757d')

            # Event types as string
            event_types = ', '.join(et.value for et in event.event_types)

            # Create tooltip content
            tooltip = f"""
            <b>{event.path.name}</b><br>
            Types: {event_types}<br>
            Priority: {entry.priority_score} ({entry.priority_category})<br>
            Time: {event.timestamp.strftime('%H:%M:%S')}
            """

            item = {
                'id': event.event_id,
                'content': event.path.name,
                'start': event.timestamp.isoformat(),
                'title': tooltip.strip(),
                'style': f'background-color: {color};',
                'className': entry.priority_category.lower()
            }

            items.append(item)

        return json.dumps(items)

    def _prepare_charts_data(self, timeline: Timeline) -> Dict[str, str]:
        """
        Prepare data for charts (Plotly format).

        Args:
            timeline: Timeline object

        Returns:
            Dictionary with chart data as JSON strings
        """
        charts = {}

        # Priority distribution pie chart
        priority_counts = {}
        for entry in timeline.entries:
            cat = entry.priority_category
            priority_counts[cat] = priority_counts.get(cat, 0) + 1

        charts['priority_distribution'] = json.dumps({
            'labels': list(priority_counts.keys()),
            'values': list(priority_counts.values()),
            'type': 'pie',
            'marker': {
                'colors': ['#dc3545', '#fd7e14', '#ffc107', '#28a745']
            }
        })

        # Event types distribution bar chart
        event_type_counts = {}
        for entry in timeline.entries:
            for et in entry.event.event_types:
                event_type_counts[et.value] = event_type_counts.get(et.value, 0) + 1

        charts['event_types'] = json.dumps({
            'x': list(event_type_counts.keys()),
            'y': list(event_type_counts.values()),
            'type': 'bar',
            'marker': {'color': '#007bff'}
        })

        # Timeline heatmap (events per hour)
        hourly_counts = self._calculate_hourly_activity(timeline)

        charts['activity_heatmap'] = json.dumps({
            'x': [h['hour'] for h in hourly_counts],
            'y': [h['count'] for h in hourly_counts],
            'type': 'scatter',
            'mode': 'lines+markers',
            'fill': 'tozeroy',
            'marker': {'color': '#17a2b8'}
        })

        # Priority score distribution histogram
        scores = [e.priority_score for e in timeline.entries]

        charts['score_distribution'] = json.dumps({
            'x': scores,
            'type': 'histogram',
            'nbinsx': 20,
            'marker': {'color': '#6610f2'}
        })

        return charts

    def _calculate_hourly_activity(self, timeline: Timeline) -> List[Dict[str, Any]]:
        """
        Calculate events per hour for activity heatmap.

        Args:
            timeline: Timeline object

        Returns:
            List of hour/count dictionaries
        """
        from collections import defaultdict

        hourly = defaultdict(int)

        for entry in timeline.entries:
            hour_key = entry.event.timestamp.strftime('%Y-%m-%d %H:00')
            hourly[hour_key] += 1

        # Sort by hour
        sorted_hours = sorted(hourly.items())

        return [
            {'hour': hour, 'count': count}
            for hour, count in sorted_hours
        ]

    def _prepare_patterns_data(self, timeline: Timeline) -> List[Dict[str, Any]]:
        """
        Prepare patterns data for display.

        Args:
            timeline: Timeline object

        Returns:
            List of pattern dictionaries
        """
        patterns_data = []

        for pattern in timeline.patterns:
            duration = (pattern.end_time - pattern.start_time).total_seconds()

            # Severity badge class
            severity_class_map = {
                'CRITICAL': 'danger',
                'HIGH': 'warning',
                'MEDIUM': 'info',
                'LOW': 'success'
            }

            patterns_data.append({
                'type': pattern.pattern_type.replace('_', ' ').title(),
                'severity': pattern.severity,
                'severity_class': severity_class_map.get(pattern.severity, 'secondary'),
                'start_time': pattern.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': pattern.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': f"{duration:.1f}s",
                'event_count': pattern.event_count,
                'affected_paths_count': len(pattern.affected_paths),
                'description': pattern.description,
                'indicators': pattern.indicators
            })

        return patterns_data

    def _prepare_events_table(self, timeline: Timeline) -> List[Dict[str, Any]]:
        """
        Prepare events data for interactive table.

        Args:
            timeline: Timeline object

        Returns:
            List of event dictionaries
        """
        events_data = []

        for entry in timeline.entries:
            event = entry.event

            # Priority badge class
            priority_class_map = {
                'CRITICAL': 'danger',
                'HIGH': 'warning',
                'MEDIUM': 'info',
                'LOW': 'success'
            }

            events_data.append({
                'event_id': event.event_id,
                'timestamp': event.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'path': str(event.path),
                'event_types': ', '.join(et.value for et in event.event_types),
                'priority_score': entry.priority_score,
                'priority_category': entry.priority_category,
                'priority_class': priority_class_map.get(entry.priority_category, 'secondary'),
                'has_quarantine': entry.xattr and entry.xattr.has_quarantine,
                'is_downloaded': entry.xattr and entry.xattr.is_downloaded
            })

        return events_data

    def _prepare_correlation_graph(self, timeline: Timeline) -> str:
        """
        Prepare data for event correlation network graph.

        Args:
            timeline: Timeline object

        Returns:
            JSON string for network graph
        """
        nodes = []
        edges = []

        # Create nodes for events
        for entry in timeline.entries:
            event = entry.event

            # Color by priority
            color_map = {
                'CRITICAL': '#dc3545',
                'HIGH': '#fd7e14',
                'MEDIUM': '#ffc107',
                'LOW': '#28a745'
            }

            nodes.append({
                'id': event.event_id,
                'label': event.path.name[:20],  # Truncate long names
                'title': str(event.path),
                'color': color_map.get(entry.priority_category, '#6c757d'),
                'size': entry.priority_score / 5  # Scale size by score
            })

            # Create edges for related events
            for related in entry.related_events:
                edges.append({
                    'from': event.event_id,
                    'to': related.event_id,
                    'arrows': 'to'
                })

        graph_data = {
            'nodes': nodes,
            'edges': edges
        }

        return json.dumps(graph_data)

    def _open_in_browser(self, file_path: Path) -> None:
        """
        Open HTML report in default browser.

        Args:
            file_path: Path to HTML file
        """
        import webbrowser

        try:
            webbrowser.open(f'file://{file_path.absolute()}')
            logger.info(f"Opened report in browser: {file_path}")
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")

    def generate_executive_summary(
        self,
        timeline: Timeline,
        output_path: Path
    ) -> None:
        """
        Generate executive summary HTML (compact, high-level only).

        Args:
            timeline: Timeline object
            output_path: Output HTML path
        """
        logger.info(f"Generating executive summary HTML: {output_path}")

        self._validate_timeline(timeline)
        self._ensure_output_directory(output_path)

        # Prepare summary data (patterns and critical events only)
        template_data = {
            'theme': 'light',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': self._build_summary(timeline),
            'patterns_data': self._prepare_patterns_data(timeline),
            'critical_events': [
                self._prepare_events_table([e])[0]
                for e in timeline.entries
                if e.priority_category in ['CRITICAL', 'HIGH']
            ][:20],  # Top 20 only
            'charts_data': {
                'priority_distribution': self._prepare_charts_data(timeline)['priority_distribution']
            }
        }

        # Render executive template
        template = self.env.get_template('executive_summary.html')
        html_content = template.render(**template_data)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Executive summary generated: {output_path}")
