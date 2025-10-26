"""
Priority Scorer
===============

Calculate priority scores for FSEvents based on weighted factors.
"""

import re
from typing import Dict, Optional, List
from pathlib import Path
from mfaa.models import FSEvent, ScoringWeights, XattrRecord
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


class PriorityScorer:
    """Calculate priority scores for events."""

    # Default weights
    DEFAULT_EVENT_WEIGHTS = {
        'Removed': 10,
        'Created': 5,
        'Renamed': 7,
        'Modified': 3,
        'InodeMetaMod': 3,
        'ChangeOwner': 6,
        'XAttrMod': 4,
        'FinderInfoMod': 2
    }

    DEFAULT_PATH_WEIGHTS = {
        r'^/System/': 10,
        r'^/Library/LaunchDaemons/': 10,
        r'^/Users/.*/Library/LaunchAgents/': 9,
        r'^/Applications/': 8,
        r'^/usr/(s)?bin/': 9,
        r'^/Users/.*/Downloads/': 7,
        r'^/Users/.*/Desktop/': 6,
        r'^/tmp/': 6,
        r'^/var/tmp/': 6,
    }

    DEFAULT_FILE_TYPE_WEIGHTS = {
        '.app': 10,
        '.command': 10,
        '.sh': 9,
        '.bash': 9,
        '.zsh': 9,
        '.py': 7,
        '.pl': 7,
        '.rb': 7,
        '.jar': 8,
        '.pkg': 8,
        '.dmg': 7,
        '.exe': 10,
        '.dll': 10,
        '.scr': 10,
        '.encrypted': 10,
        '.locked': 10,
        '.crypt': 10,
        '.pdf': 3,
        '.doc': 3,
        '.docx': 3,
        '.xls': 3,
        '.xlsx': 3,
        '.zip': 6,
        '.tar': 6,
        '.gz': 6
    }

    def __init__(self, weights: Optional[ScoringWeights] = None):
        """
        Initialize PriorityScorer.

        Args:
            weights: ScoringWeights object with custom weights
        """
        if weights:
            self.event_weights = weights.event_type_weights or self.DEFAULT_EVENT_WEIGHTS
            self.path_weights = weights.path_weights or self.DEFAULT_PATH_WEIGHTS
            self.file_type_weights = weights.file_type_weights or self.DEFAULT_FILE_TYPE_WEIGHTS
            self.quarantine_bonus = weights.quarantine_bonus
            self.download_bonus = weights.download_bonus
        else:
            self.event_weights = self.DEFAULT_EVENT_WEIGHTS
            self.path_weights = self.DEFAULT_PATH_WEIGHTS
            self.file_type_weights = self.DEFAULT_FILE_TYPE_WEIGHTS
            self.quarantine_bonus = 5
            self.download_bonus = 5

        # Compile path patterns for performance
        self._compiled_path_patterns = {
            re.compile(pattern): weight
            for pattern, weight in self.path_weights.items()
        }

        logger.info("PriorityScorer initialized with custom weights")

    def calculate_score(
        self,
        event: FSEvent,
        xattr: Optional[XattrRecord] = None
    ) -> int:
        """
        Calculate priority score for an event.

        Score components:
        - Event type weight (0-10)
        - Path sensitivity weight (0-10)
        - File type risk weight (0-10)
        - Quarantine bonus (+5)
        - Download bonus (+5)

        Args:
            event: FSEvent object
            xattr: Optional XattrRecord for bonus scoring

        Returns:
            Priority score (0-100)
        """
        score = 0

        # 1. Event type weight (0-10)
        event_score = self._calculate_event_type_score(event)
        score += event_score

        # 2. Path sensitivity weight (0-10)
        path_score = self._calculate_path_score(event)
        score += path_score

        # 3. File type risk weight (0-10)
        file_type_score = self._calculate_file_type_score(event)
        score += file_type_score

        # 4. Bonuses from xattr
        if xattr:
            if xattr.has_quarantine:
                score += self.quarantine_bonus
                logger.debug(f"Quarantine bonus: +{self.quarantine_bonus}")

            if xattr.is_downloaded:
                score += self.download_bonus
                logger.debug(f"Download bonus: +{self.download_bonus}")

        # Normalize to 0-100 range
        # Max possible: 10 + 10 + 10 + 5 + 5 = 40
        # Scale to 100: score * 2.5
        normalized_score = min(int(score * 2.5), 100)

        logger.debug(f"Score for {event.path.name}: {normalized_score} "
                    f"(event:{event_score}, path:{path_score}, file:{file_type_score})")

        return normalized_score

    def _calculate_event_type_score(self, event: FSEvent) -> int:
        """Calculate score based on event type."""
        max_weight = 0

        for event_type in event.event_types:
            type_name = event_type.value
            weight = self.event_weights.get(type_name, 0)
            max_weight = max(max_weight, weight)

        return max_weight

    def _calculate_path_score(self, event: FSEvent) -> int:
        """Calculate score based on path sensitivity."""
        path_str = str(event.path)

        for pattern, weight in self._compiled_path_patterns.items():
            if pattern.search(path_str):
                return weight

        # Default score for non-matching paths
        return 1

    def _calculate_file_type_score(self, event: FSEvent) -> int:
        """Calculate score based on file type."""
        ext = event.path.suffix.lower()

        if ext in self.file_type_weights:
            return self.file_type_weights[ext]

        # Default score for unknown extensions
        return 1

    def categorize_score(self, score: int) -> str:
        """
        Categorize priority score.

        Args:
            score: Priority score (0-100)

        Returns:
            Category name: CRITICAL, HIGH, MEDIUM, or LOW
        """
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    def score_events(
        self,
        events: List[FSEvent],
        xattr_records: Optional[Dict[Path, XattrRecord]] = None
    ) -> List[tuple]:
        """
        Score multiple events and return with scores.

        Args:
            events: List of FSEvent objects
            xattr_records: Optional dict mapping paths to XattrRecords

        Returns:
            List of tuples: (event, score, category)
        """
        from typing import List

        results = []

        for event in events:
            # Get xattr if available
            xattr = None
            if xattr_records:
                xattr = xattr_records.get(event.path)

            score = self.calculate_score(event, xattr)
            category = self.categorize_score(score)

            results.append((event, score, category))

        logger.info(f"Scored {len(results)} events")
        return results

    def get_high_priority_events(
        self,
        scored_events: List[tuple],
        min_score: int = 60
    ) -> List[tuple]:
        """
        Get high-priority events.

        Args:
            scored_events: List of (event, score, category) tuples
            min_score: Minimum score threshold

        Returns:
            Filtered list of high-priority events
        """
        high_priority = [
            (event, score, category)
            for event, score, category in scored_events
            if score >= min_score
        ]

        logger.info(f"Found {len(high_priority)} high-priority events (>={min_score})")
        return high_priority

    def get_scoring_statistics(self, scored_events: List[tuple]) -> dict:
        """
        Get statistics about scored events.

        Args:
            scored_events: List of (event, score, category) tuples

        Returns:
            Dictionary with scoring statistics
        """
        if not scored_events:
            return {
                'total': 0,
                'by_category': {},
                'score_distribution': {}
            }

        categories = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        score_ranges = {
            '0-20': 0,
            '21-40': 0,
            '41-60': 0,
            '61-80': 0,
            '81-100': 0
        }

        for _, score, category in scored_events:
            categories[category] += 1

            # Categorize into ranges
            if score <= 20:
                score_ranges['0-20'] += 1
            elif score <= 40:
                score_ranges['21-40'] += 1
            elif score <= 60:
                score_ranges['41-60'] += 1
            elif score <= 80:
                score_ranges['61-80'] += 1
            else:
                score_ranges['81-100'] += 1

        avg_score = sum(score for _, score, _ in scored_events) / len(scored_events)

        return {
            'total': len(scored_events),
            'by_category': categories,
            'score_distribution': score_ranges,
            'average_score': round(avg_score, 2),
            'max_score': max(score for _, score, _ in scored_events),
            'min_score': min(score for _, score, _ in scored_events)
        }
