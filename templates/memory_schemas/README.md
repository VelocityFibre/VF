# Domain Memory Schema Templates

**Purpose**: Pre-built state schemas for different agent types to implement domain memory patterns.

---

## What Are These?

These JSON templates define **persistent state structures** for agents in different domains. They implement the core principle:

> "The agent is a policy that transforms one consistent memory state into another."

Without these schemas, agents are **amnesiacs**. With them, agents have a persistent understanding of "where we are in the world."

---

## Available Templates

### 1. Research Agent (`research_agent_state.json`)

**Use for**: Market research, competitive analysis, scientific investigation

**Key structures**:
- `hypotheses[]` - Statements being tested with confidence levels
- `experiments[]` - Tests being run to validate hypotheses
- `evidence_log[]` - Findings from experiments
- `decision_journal[]` - Decisions made based on evidence

**Example usage**:
```python
from shared.base_agent import BaseAgent

class ResearchAgent(BaseAgent):
    def __init__(self, api_key):
        super().__init__(
            api_key,
            state_file="agents/research-agent/state.json"
        )

    def initialize_state(self):
        # Load template
        import json
        with open("templates/memory_schemas/research_agent_state.json") as f:
            return json.load(f)

    def add_hypothesis(self, statement: str) -> int:
        """Add new hypothesis to research state"""
        hypothesis = {
            "id": len(self.get_state("hypotheses", [])) + 1,
            "statement": statement,
            "status": "untested",
            "evidence": [],
            "confidence": "low"
        }
        hypotheses = self.get_state("hypotheses", [])
        hypotheses.append(hypothesis)
        self.set_state("hypotheses", hypotheses)
        self.save_state()
        return hypothesis["id"]
```

---

### 2. Operations Agent (`operations_agent_state.json`)

**Use for**: System monitoring, incident response, SRE tasks, runbook automation

**Key structures**:
- `incidents[]` - Active and historical incidents
- `incident_timeline[]` - Chronological actions taken
- `sla_tracking` - Response/resolution time metrics
- `system_health` - Current system status
- `maintenance_windows[]` - Planned downtime

**Example usage**:
```python
class OperationsAgent(BaseAgent):
    def initialize_state(self):
        import json
        with open("templates/memory_schemas/operations_agent_state.json") as f:
            return json.load(f)

    def record_incident(self, severity: str, description: str) -> str:
        """Record new incident"""
        from datetime import datetime
        incident_id = f"INC-{len(self.get_state('incidents', [])) + 1:03d}"

        incident = {
            "id": incident_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": severity,
            "description": description,
            "status": "open",
            "timeline": []
        }

        incidents = self.get_state("incidents", [])
        incidents.append(incident)
        self.set_state("incidents", incidents)
        self.save_state()
        return incident_id

    def add_timeline_entry(self, incident_id: str, action: str, actor: str):
        """Add action to incident timeline"""
        from datetime import datetime
        incidents = self.get_state("incidents", [])

        for incident in incidents:
            if incident["id"] == incident_id:
                incident["timeline"].append({
                    "time": datetime.utcnow().strftime("%H:%M"),
                    "action": action,
                    "actor": actor
                })
                break

        self.set_state("incidents", incidents)
        self.save_state()
```

---

### 3. Project Management Agent (`project_management_agent_state.json`)

**Use for**: Project tracking, milestone management, risk assessment

**Key structures**:
- `milestones[]` - Key project deliverables with status
- `tasks[]` - Actionable work items
- `risks[]` - Identified risks with mitigation strategies
- `blockers[]` - Current obstacles preventing progress
- `status_reports[]` - Historical status updates
- `decision_log[]` - Important decisions made

**Example usage**:
```python
class ProjectAgent(BaseAgent):
    def initialize_state(self):
        import json
        with open("templates/memory_schemas/project_management_agent_state.json") as f:
            return json.load(f)

    def add_milestone(self, name: str, target_date: str) -> int:
        """Add project milestone"""
        milestone = {
            "id": len(self.get_state("milestones", [])) + 1,
            "name": name,
            "status": "pending",
            "target_date": target_date,
            "completion_date": None,
            "progress_pct": 0
        }

        milestones = self.get_state("milestones", [])
        milestones.append(milestone)
        self.set_state("milestones", milestones)
        self.save_state()
        return milestone["id"]

    def add_blocker(self, description: str, impact: str) -> int:
        """Record project blocker"""
        blocker = {
            "id": len(self.get_state("blockers", [])) + 1,
            "description": description,
            "impact": impact,  # "high", "medium", "low"
            "status": "open",
            "created_at": datetime.utcnow().isoformat()
        }

        blockers = self.get_state("blockers", [])
        blockers.append(blocker)
        self.set_state("blockers", blockers)
        self.save_state()
        return blocker["id"]
```

---

### 4. Customer Support Agent (`customer_support_agent_state.json`)

**Use for**: Help desk, customer inquiries, ticket management

**Key structures**:
- `customer_context` - Current customer info
- `ticket_history[]` - Past interactions
- `known_issues[]` - Common problems and solutions
- `escalations[]` - Issues escalated to humans
- `satisfaction_tracking` - NPS and feedback metrics
- `pending_followups[]` - Items requiring follow-up

**Example usage**:
```python
class SupportAgent(BaseAgent):
    def initialize_state(self):
        import json
        with open("templates/memory_schemas/customer_support_agent_state.json") as f:
            return json.load(f)

    def start_interaction(self, customer_id: str, customer_name: str):
        """Begin customer interaction"""
        self.update_state({
            "customer_context": {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "interaction_count": self.get_interaction_count(customer_id) + 1
            }
        })
        self.save_state()

    def record_ticket(self, issue: str, category: str, resolution: str):
        """Record support ticket"""
        from datetime import datetime
        ticket = {
            "id": f"TKT-{len(self.get_state('ticket_history', [])) + 1:05d}",
            "customer_id": self.get_state("customer_context", {}).get("customer_id"),
            "timestamp": datetime.utcnow().isoformat(),
            "issue": issue,
            "category": category,
            "resolution": resolution,
            "resolved": True
        }

        tickets = self.get_state("ticket_history", [])
        tickets.append(ticket)
        self.set_state("ticket_history", tickets)
        self.save_state()
```

---

## How to Use These Templates

### Step 1: Choose Template

Pick the schema that matches your agent's domain:
- Research → `research_agent_state.json`
- Operations → `operations_agent_state.json`
- Project management → `project_management_agent_state.json`
- Customer support → `customer_support_agent_state.json`

### Step 2: Copy to Agent Directory

```bash
# For a new operations agent
mkdir -p agents/my-ops-agent
cp templates/memory_schemas/operations_agent_state.json agents/my-ops-agent/state.json
```

### Step 3: Initialize Agent with State File

```python
from shared.base_agent import BaseAgent

class MyOpsAgent(BaseAgent):
    def __init__(self, api_key):
        super().__init__(
            anthropic_api_key=api_key,
            model="claude-3-haiku-20240307",
            state_file="agents/my-ops-agent/state.json"  # ← Domain memory!
        )

    def initialize_state(self):
        """Load template on first run"""
        import json
        with open("templates/memory_schemas/operations_agent_state.json") as f:
            template = json.load(f)
        # Customize if needed
        template["created_at"] = datetime.utcnow().isoformat()
        return template
```

### Step 4: Use State in Tools

```python
def execute_tool(self, tool_name: str, tool_input: dict) -> str:
    if tool_name == "record_incident":
        # Read current state
        incidents = self.get_state("incidents", [])

        # Add new incident
        incident = {...}
        incidents.append(incident)

        # Update state
        self.set_state("incidents", incidents)
        self.save_state()  # ← Persist to disk!

        return json.dumps({"status": "recorded", "incident_id": incident["id"]})
```

---

## Customizing Templates

Templates are **starting points**. Customize for your domain:

```python
def initialize_state(self):
    """Override to add custom fields"""
    base_state = super().initialize_state()

    # Add domain-specific fields
    base_state["fiber_projects"] = []
    base_state["contractor_assignments"] = {}
    base_state["material_inventory"] = {
        "fiber_cable_meters": 0,
        "connectors": 0,
        "splice_trays": 0
    }

    return base_state
```

---

## Testing State Persistence

Always test that state survives across sessions:

```python
# tests/test_agent_memory.py
import pytest
from agents.my_agent.agent import MyAgent
import os

def test_state_persistence(tmp_path):
    """Test that state survives across agent restarts"""
    state_file = tmp_path / "test_state.json"

    # Session 1: Create agent and add data
    agent1 = MyAgent(api_key="test", state_file=str(state_file))
    agent1.add_milestone("Launch MVP", "2025-12-31")
    assert len(agent1.get_state("milestones")) == 1

    # Session 2: New agent instance, state should persist
    agent2 = MyAgent(api_key="test", state_file=str(state_file))
    assert len(agent2.get_state("milestones")) == 1
    assert agent2.get_state("milestones")[0]["name"] == "Launch MVP"
```

---

## When NOT to Use These Templates

❌ **Don't use for**:
- Simple one-off queries (no persistent state needed)
- Agents using harness domain memory (feature_list.json pattern)
- Agents using Superior Agent Brain (vector memory for learning)

✅ **DO use for**:
- Manually-built agents needing long-term memory
- Domain-specific workflows with clear state
- Agents that need to "remember" across sessions

---

## Creating Your Own Template

If none of these fit your domain, create a custom schema:

```json
{
  "schema_version": "1.0.0",
  "agent_type": "your_domain",
  "created_at": null,
  "last_updated": null,

  // Core domain entities
  "main_entities": [],

  // Workflow state
  "current_phase": "initial",
  "progress_pct": 0,

  // History/audit trail
  "action_history": [],

  // Domain-specific metrics
  "metrics": {},

  // Next steps
  "pending_actions": []
}
```

**Key principles**:
1. Make it **machine-readable** (JSON, not prose)
2. Include **pass/fail criteria** where relevant
3. Track **history** (decisions, actions, changes)
4. Define **clear states** (planning, active, complete, etc.)
5. Include **next steps** or pending actions

---

## Further Reading

- `DOMAIN_MEMORY_GUIDE.md` - Complete domain memory philosophy
- `shared/base_agent.py` - BaseAgent implementation with memory methods
- `harness/README.md` - Harness domain memory (feature_list.json pattern)
- `memory/` - Superior Agent Brain (vector memory for learning)

---

**Remember**: "The magic is in the memory. The agent is a policy that transforms one consistent memory state into another."
