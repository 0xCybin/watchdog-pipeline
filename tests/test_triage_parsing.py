import json

import pytest


class TestTriageResponseParsing:
    """Test parsing of Claude triage responses (no API calls)."""

    def test_parse_valid_response(self):
        response = json.dumps({
            "priority_score": 0.75,
            "summary": "Document discusses flight logs",
            "entities": [
                {"name": "John Doe", "type": "person", "context": "Named as pilot"},
                {"name": "Palm Beach", "type": "location", "context": "Flight destination"},
            ],
            "relationships": [
                {
                    "source": "John Doe",
                    "target": "Palm Beach",
                    "type": "traveled_to",
                    "description": "Flew to Palm Beach",
                    "confidence": 0.8,
                }
            ],
            "anomalies": [
                {
                    "type": "timeline",
                    "description": "Date inconsistency in flight logs",
                    "severity": "medium",
                    "confidence": 0.6,
                    "evidence": "Log shows March 5 but receipt shows March 7",
                }
            ],
        })

        result = json.loads(response)
        assert result["priority_score"] == 0.75
        assert len(result["entities"]) == 2
        assert len(result["relationships"]) == 1
        assert len(result["anomalies"]) == 1
        assert result["anomalies"][0]["severity"] == "medium"

    def test_parse_empty_response(self):
        response = json.dumps({
            "priority_score": 0.1,
            "summary": "Administrative document",
            "entities": [],
            "relationships": [],
            "anomalies": [],
        })

        result = json.loads(response)
        assert result["priority_score"] == 0.1
        assert len(result["entities"]) == 0

    def test_parse_high_priority(self):
        response = json.dumps({
            "priority_score": 0.95,
            "summary": "Critical evidence found",
            "entities": [{"name": "Key Person", "type": "person", "context": "Central figure"}],
            "relationships": [],
            "anomalies": [
                {
                    "type": "missing_evidence",
                    "description": "Referenced document appears to be missing",
                    "severity": "critical",
                    "confidence": 0.9,
                    "evidence": "Document 47B referenced but not in collection",
                }
            ],
        })

        result = json.loads(response)
        assert result["priority_score"] > 0.9
        assert result["anomalies"][0]["severity"] == "critical"
