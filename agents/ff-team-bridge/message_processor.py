#!/usr/bin/env python3
"""
Message Processor for FF Team Bridge
Extracts tasks, decisions, and other important information from WhatsApp messages
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageProcessor:
    """Processes WhatsApp messages to extract actionable information"""

    def __init__(self):
        # Explicit prefixes that indicate importance
        self.important_prefixes = [
            "TASK:", "TODO:", "DECIDED:", "DECISION:",
            "@CLAUDE", "IMPORTANT:", "BUG:", "FIXED:",
            "ISSUE:", "PROBLEM:", "URGENT:", "NOTE:",
            "BLOCKER:", "QUESTION:", "HELP:", "UPDATE:"
        ]

        # Natural language patterns for task detection
        self.task_patterns = [
            # "Louis will/should/can/must..."
            (r"(louis|hein)\s+(will|should|can|must|needs to|has to|is going to)\s+(.+)", "assignment"),
            # "Can/Could Louis/Hein..."
            (r"(can|could|would)\s+(louis|hein)\s+(.+)", "request"),
            # "I'll/I will..." (from identified sender)
            (r"(i'll|i will|i'm going to|i am going to|let me|i can)\s+(.+)", "self_assignment"),
            # "@Louis/@Hein..."
            (r"@(louis|hein)\s+(.+)", "mention"),
            # "for Louis/Hein to..."
            (r"for\s+(louis|hein)\s+to\s+(.+)", "delegation"),
            # "Louis/Hein, please..."
            (r"(louis|hein),?\s+please\s+(.+)", "polite_request")
        ]

        # Decision patterns
        self.decision_patterns = [
            r"(decided|decision|agreed|confirmed|finalized):\s*(.+)",
            r"we\s+(will|are going to|should|must)\s+(.+)",
            r"let's\s+(.+)",
            r"going\s+with\s+(.+)"
        ]

        # Technical terms that make a message important
        self.technical_terms = [
            'deploy', 'deployment', 'production', 'staging', 'bug', 'error',
            'fix', 'auth', 'authentication', 'database', 'api', 'endpoint',
            'server', 'vps', 'docker', 'test', 'testing', 'migration',
            'backup', 'security', 'performance', 'optimization', 'refactor'
        ]

    async def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single message and extract information"""

        text = message.get('text', '')
        sender = message.get('sender', 'Unknown')

        if not text:
            return self._empty_result()

        # Extract all types of information
        result = {
            'tasks': self._extract_tasks(text, sender),
            'decisions': self._extract_decisions(text, sender),
            'bugs': self._extract_bugs(text),
            'questions': self._extract_questions(text),
            'code_references': self._extract_code_references(text),
            'is_important': self._is_important(text)
        }

        # Log extraction results
        if any([result['tasks'], result['decisions'], result['bugs'], result['questions']]):
            logger.debug(f"Extracted from '{text[:50]}...': {result}")

        return result

    def _is_important(self, text: str) -> bool:
        """Determine if a message is important enough to save"""

        text_upper = text.upper()
        text_lower = text.lower()

        # Check explicit prefixes
        if any(prefix in text_upper for prefix in self.important_prefixes):
            return True

        # Check for natural task language
        for pattern, _ in self.task_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        # Check for technical terms with questions
        if '?' in text and any(term in text_lower for term in self.technical_terms):
            return True

        # Check for decision language
        for pattern in self.decision_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    def _extract_tasks(self, text: str, sender: str) -> List[Dict[str, Any]]:
        """Extract tasks from the message"""

        tasks = []
        text_lower = text.lower()
        text_upper = text.upper()

        # Check for explicit TASK:/TODO:
        if "TASK:" in text_upper or "TODO:" in text_upper:
            # Try to extract assignment
            assigned_to = self._extract_assignee(text_lower)

            # Clean the task text
            task_text = re.sub(r'^(TASK:|TODO:)\s*', '', text, flags=re.IGNORECASE).strip()

            tasks.append({
                'description': task_text,
                'assigned_to': assigned_to or 'unassigned',
                'type': 'explicit',
                'sender': sender,
                'timestamp': datetime.now().isoformat()
            })

        # Check natural language patterns
        for pattern, pattern_type in self.task_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                if pattern_type == 'assignment':
                    person = match.group(1)
                    action = match.group(3).strip()
                    tasks.append({
                        'description': f"{person.capitalize()} will {action}",
                        'assigned_to': person,
                        'type': 'natural',
                        'sender': sender,
                        'timestamp': datetime.now().isoformat()
                    })

                elif pattern_type == 'self_assignment' and sender.lower() in ['louis', 'hein']:
                    action = match.group(2).strip()
                    tasks.append({
                        'description': f"{sender} will {action}",
                        'assigned_to': sender.lower(),
                        'type': 'self',
                        'sender': sender,
                        'timestamp': datetime.now().isoformat()
                    })

        return tasks

    def _extract_decisions(self, text: str, sender: str) -> List[Dict[str, Any]]:
        """Extract decisions from the message"""

        decisions = []
        text_lower = text.lower()
        text_upper = text.upper()

        # Explicit decision markers
        if "DECIDED:" in text_upper or "DECISION:" in text_upper:
            decision_text = re.sub(r'^(DECIDED|DECISION):\s*', '', text, flags=re.IGNORECASE).strip()
            decisions.append({
                'description': decision_text,
                'made_by': sender,
                'type': 'explicit',
                'timestamp': datetime.now().isoformat()
            })

        # Natural language decisions
        for pattern in self.decision_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Extract the decision content
                if len(match.groups()) >= 2:
                    decision_text = match.group(2).strip()
                else:
                    decision_text = match.group(1).strip()

                # Avoid duplicates
                if not any(d['description'].lower() == decision_text.lower() for d in decisions):
                    decisions.append({
                        'description': decision_text.capitalize(),
                        'made_by': sender,
                        'type': 'natural',
                        'timestamp': datetime.now().isoformat()
                    })

        return decisions

    def _extract_bugs(self, text: str) -> List[Dict[str, Any]]:
        """Extract bug reports or issues"""

        bugs = []
        text_upper = text.upper()

        bug_markers = ["BUG:", "ISSUE:", "PROBLEM:", "ERROR:", "BROKEN:", "FAILING:"]

        for marker in bug_markers:
            if marker in text_upper:
                bug_text = re.sub(f'^{marker}\s*', '', text, flags=re.IGNORECASE).strip()
                bugs.append({
                    'description': bug_text,
                    'severity': 'high' if 'URGENT' in text_upper else 'normal',
                    'timestamp': datetime.now().isoformat()
                })

        return bugs

    def _extract_questions(self, text: str) -> List[Dict[str, Any]]:
        """Extract questions, especially those directed at Claude"""

        questions = []
        text_lower = text.lower()

        # Questions for Claude
        if '@claude' in text_lower or 'claude?' in text_lower:
            question_text = re.sub(r'@claude\s*', '', text, flags=re.IGNORECASE).strip()
            questions.append({
                'question': question_text,
                'for': 'claude',
                'timestamp': datetime.now().isoformat()
            })

        # General questions with technical context
        elif '?' in text and any(term in text_lower for term in self.technical_terms):
            questions.append({
                'question': text.strip(),
                'for': 'team',
                'timestamp': datetime.now().isoformat()
            })

        return questions

    def _extract_code_references(self, text: str) -> List[str]:
        """Extract code file references and function names"""

        references = []

        # File patterns
        file_patterns = [
            r'([a-zA-Z0-9_/]+\.(py|js|ts|tsx|jsx|md|yaml|yml|json))',
            r'`([^`]+)`',  # Backtick references
            r'function\s+(\w+)',
            r'class\s+(\w+)',
            r'def\s+(\w+)'
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    references.append(match[0])
                else:
                    references.append(match)

        return list(set(references))  # Remove duplicates

    def _extract_assignee(self, text: str) -> Optional[str]:
        """Extract who a task is assigned to"""

        text_lower = text.lower()

        # Direct mentions
        if '@louis' in text_lower or 'for louis' in text_lower:
            return 'louis'
        elif '@hein' in text_lower or 'for hein' in text_lower:
            return 'hein'

        # Natural language
        if 'louis' in text_lower and any(word in text_lower for word in ['will', 'should', 'can', 'must']):
            return 'louis'
        elif 'hein' in text_lower and any(word in text_lower for word in ['will', 'should', 'can', 'must']):
            return 'hein'

        return None

    def _empty_result(self) -> Dict[str, Any]:
        """Return an empty result structure"""
        return {
            'tasks': [],
            'decisions': [],
            'bugs': [],
            'questions': [],
            'code_references': [],
            'is_important': False
        }