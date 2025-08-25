"""Prompt templates for different intents and languages."""
from typing import Dict, Any, Optional
from enum import Enum


class Language(str, Enum):
    """Supported languages."""
    ENGLISH = "en"
    GREEK = "el"
    AUTO = "auto"


class PromptTemplate:
    """Base class for prompt templates."""
    
    def __init__(self, template_en: str, template_el: str):
        """Initialize with English and Greek templates."""
        self.templates = {
            Language.ENGLISH: template_en,
            Language.GREEK: template_el
        }
    
    def format(self, language: Language = Language.ENGLISH, **kwargs) -> str:
        """Format the template with provided variables."""
        template = self.templates.get(language, self.templates[Language.ENGLISH])
        return template.format(**kwargs)
    
    def get_template(self, language: Language = Language.ENGLISH) -> str:
        """Get raw template string."""
        return self.templates.get(language, self.templates[Language.ENGLISH])


# Intent Detection Prompt Templates
INTENT_DETECTION_TEMPLATE = PromptTemplate(
    template_en="""Analyze the following user message and detect the intent and targets.

Available intents:
- integration_check: Check consistency between Solution Outline sections and diagrams
- requirements_coverage: Analyze how well requirements are covered in SO/diagrams  
- improve_paragraph: Improve specific paragraph or section of Solution Outline
- qna: General questions and answers using available context

User message: "{user_message}"

Context information:
- Project ID: {project_id}
- Explicitly mentioned targets: {explicit_targets}
- Available SO sections: {available_so_sections}
- Available requirements: {available_requirements}
- Available diagrams: {available_diagrams}

Instructions:
1. Detect exactly ONE intent from the four options above
2. Extract or infer target IDs (SEC-*, REQ-*, SEQ-*, C4-*)
3. Provide confidence score (0.0-1.0) based on clarity of intent
4. Give short rationale for the decision

Respond with valid JSON in this exact format:
{{
    "intent": "one_of_the_four_intents",
    "targets": {{
        "so_ids": ["SEC-1.1", "SEC-2.3"],
        "requirement_ids": ["REQ-12", "REQ-15"], 
        "diagram_ids": ["SEQ-01", "C4-Context"]
    }},
    "confidence": 0.85,
    "reason": "Short explanation of why this intent was chosen"
}}""",
    
    template_el="""Αναλύστε το ακόλουθο μήνυμα χρήστη και εντοπίστε την πρόθεση και τους στόχους.

Διαθέσιμες προθέσεις:
- integration_check: Έλεγχος συνέπειας μεταξύ ενοτήτων Solution Outline και διαγραμμάτων
- requirements_coverage: Ανάλυση κάλυψης απαιτήσεων σε SO/διαγράμματα
- improve_paragraph: Βελτίωση συγκεκριμένης παραγράφου ή ενότητας του Solution Outline
- qna: Γενικές ερωτήσεις και απαντήσεις με χρήση διαθέσιμου περιεχομένου

Μήνυμα χρήστη: "{user_message}"

Πληροφορίες περιβάλλοντος:
- Project ID: {project_id}
- Ρητώς αναφερόμενοι στόχοι: {explicit_targets}
- Διαθέσιμες ενότητες SO: {available_so_sections}
- Διαθέσιμες απαιτήσεις: {available_requirements}
- Διαθέσιμα διαγράμματα: {available_diagrams}

Οδηγίες:
1. Εντοπίστε ακριβώς ΜΙΑ πρόθεση από τις τέσσερις παραπάνω επιλογές
2. Εξάγετε ή συμπεράνετε target IDs (SEC-*, REQ-*, SEQ-*, C4-*)
3. Δώστε βαθμολογία εμπιστοσύνης (0.0-1.0) βάσει της σαφήνειας της πρόθεσης
4. Δώστε σύντομη αιτιολόγηση για την απόφαση

Απαντήστε με έγκυρο JSON σε αυτή ακριβώς τη μορφή:
{{
    "intent": "μια_από_τις_τέσσερις_προθέσεις",
    "targets": {{
        "so_ids": ["SEC-1.1", "SEC-2.3"],
        "requirement_ids": ["REQ-12", "REQ-15"],
        "diagram_ids": ["SEQ-01", "C4-Context"]
    }},
    "confidence": 0.85,
    "reason": "Σύντομη εξήγηση γιατί επιλέχθηκε αυτή η πρόθεση"
}}"""
)

# Integration Check Analysis Template
INTEGRATION_CHECK_TEMPLATE = PromptTemplate(
    template_en="""Analyze the consistency between Solution Outline sections and diagrams.

## Context
Project: {project_id}
Analysis Type: Integration Consistency Check

## Solution Outline Sections
{so_sections}

## Diagrams
{diagrams}

## Requirements (for reference)
{requirements}

## Task
Compare the Solution Outline sections with the provided diagrams and identify:
1. Consistency issues between architectural descriptions and diagram flows
2. Missing components or connections
3. Contradictions or misalignments
4. Areas that need clarification or improvement

## Response Format
Respond with valid JSON matching this schema:
{{
    "suggestions": [
        {{
            "id": "SUG-001",
            "type": "integration",
            "severity": "major",
            "location": {{
                "so_section_id": "SEC-2.1",
                "paragraph_index": 0
            }},
            "summary": "Component X missing in sequence diagram",
            "rationale": "SO describes component X but it's not shown in SEQ-01",
            "evidence": {{
                "requirements": ["REQ-12"],
                "diagrams": [{{
                    "diagram_id": "SEQ-01",
                    "steps": [1, 2]
                }}],
                "so_quotes": ["The system shall include component X"]
            }},
            "recommendation": "Add component X to sequence diagram or update SO description",
            "proposed_text": null,
            "confidence": 0.9
        }}
    ],
    "scores": {{
        "integration_consistency": 0.75,
        "requirements_coverage": 0.80,
        "security_readiness": 0.85,
        "operability": 0.70
    }},
    "status": "ok"
}}

If insufficient context is provided, respond with: {{"status": "insufficient"}}""",
    
    template_el="""Αναλύστε τη συνέπεια μεταξύ των ενοτήτων του Solution Outline και των διαγραμμάτων.

## Περιβάλλον
Έργο: {project_id}
Τύπος Ανάλυσης: Έλεγχος Συνέπειας Ολοκλήρωσης

## Ενότητες Solution Outline
{so_sections}

## Διαγράμματα
{diagrams}

## Απαιτήσεις (για αναφορά)
{requirements}

## Εργασία
Συγκρίνετε τις ενότητες του Solution Outline με τα παρεχόμενα διαγράμματα και εντοπίστε:
1. Θέματα συνέπειας μεταξύ αρχιτεκτονικών περιγραφών και ροών διαγραμμάτων
2. Στοιχεία ή συνδέσεις που λείπουν
3. Αντιφάσεις ή αναντιστοιχίες
4. Περιοχές που χρειάζονται διευκρίνιση ή βελτίωση

## Μορφή Απάντησης
Απαντήστε με έγκυρο JSON που ταιριάζει σε αυτό το σχήμα:
{{
    "suggestions": [
        {{
            "id": "SUG-001",
            "type": "integration",
            "severity": "major",
            "location": {{
                "so_section_id": "SEC-2.1",
                "paragraph_index": 0
            }},
            "summary": "Το στοιχείο X λείπει από το διάγραμμα ακολουθίας",
            "rationale": "Το SO περιγράφει το στοιχείο X αλλά δεν φαίνεται στο SEQ-01",
            "evidence": {{
                "requirements": ["REQ-12"],
                "diagrams": [{{
                    "diagram_id": "SEQ-01",
                    "steps": [1, 2]
                }}],
                "so_quotes": ["Το σύστημα θα πρέπει να περιλαμβάνει το στοιχείο X"]
            }},
            "recommendation": "Προσθέστε το στοιχείο X στο διάγραμμα ακολουθίας ή ενημερώστε την περιγραφή SO",
            "proposed_text": null,
            "confidence": 0.9
        }}
    ],
    "scores": {{
        "integration_consistency": 0.75,
        "requirements_coverage": 0.80,
        "security_readiness": 0.85,
        "operability": 0.70
    }},
    "status": "ok"
}}

Αν δεν παρέχεται επαρκές περιβάλλον, απαντήστε με: {{"status": "insufficient"}}"""
)

# Requirements Coverage Analysis Template
REQUIREMENTS_COVERAGE_TEMPLATE = PromptTemplate(
    template_en="""Analyze how well requirements are covered in the Solution Outline and diagrams.

## Context
Project: {project_id}
Analysis Type: Requirements Coverage Analysis

## Requirements
{requirements}

## Solution Outline Sections
{so_sections}

## Diagrams
{diagrams}

## Task
Analyze the coverage of requirements in the provided SO sections and diagrams:
1. Map each requirement to relevant SO sections and diagrams
2. Identify gaps where requirements are not adequately covered
3. Find requirements that are over-specified or contradictory
4. Suggest improvements for better coverage

## Response Format
Respond with valid JSON matching this schema:
{{
    "suggestions": [
        {{
            "id": "SUG-001",
            "type": "coverage",
            "severity": "critical",
            "location": {{
                "so_section_id": "SEC-3.1",
                "paragraph_index": 1
            }},
            "summary": "REQ-15 not covered in authentication section",
            "rationale": "Requirement REQ-15 specifies multi-factor auth but SO only mentions basic auth",
            "evidence": {{
                "requirements": ["REQ-15"],
                "diagrams": [],
                "so_quotes": ["Basic authentication will be implemented"]
            }},
            "recommendation": "Add multi-factor authentication details to SEC-3.1",
            "proposed_text": null,
            "confidence": 0.95
        }}
    ],
    "scores": {{
        "integration_consistency": 0.80,
        "requirements_coverage": 0.65,
        "security_readiness": 0.75,
        "operability": 0.85
    }},
    "status": "ok"
}}

If insufficient context is provided, respond with: {{"status": "insufficient"}}""",
    
    template_el="""Αναλύστε πόσο καλά καλύπτονται οι απαιτήσεις στο Solution Outline και τα διαγράμματα.

## Περιβάλλον
Έργο: {project_id}
Τύπος Ανάλυσης: Ανάλυση Κάλυψης Απαιτήσεων

## Απαιτήσεις
{requirements}

## Ενότητες Solution Outline
{so_sections}

## Διαγράμματα
{diagrams}

## Εργασία
Αναλύστε την κάλυψη των απαιτήσεων στις παρεχόμενες ενότητες SO και διαγράμματα:
1. Αντιστοιχίστε κάθε απαίτηση σε σχετικές ενότητες SO και διαγράμματα
2. Εντοπίστε κενά όπου οι απαιτήσεις δεν καλύπτονται επαρκώς
3. Βρείτε απαιτήσεις που είναι υπερ-προσδιορισμένες ή αντιφατικές
4. Προτείνετε βελτιώσεις για καλύτερη κάλυψη

## Μορφή Απάντησης
Απαντήστε με έγκυρο JSON που ταιριάζει σε αυτό το σχήμα:
{{
    "suggestions": [
        {{
            "id": "SUG-001",
            "type": "coverage",
            "severity": "critical",
            "location": {{
                "so_section_id": "SEC-3.1",
                "paragraph_index": 1
            }},
            "summary": "Η REQ-15 δεν καλύπτεται στην ενότητα αυθεντικοποίησης",
            "rationale": "Η απαίτηση REQ-15 προσδιορίζει πολυπαραγοντική αυθεντικοποίηση αλλά το SO αναφέρει μόνο βασική αυθεντικοποίηση",
            "evidence": {{
                "requirements": ["REQ-15"],
                "diagrams": [],
                "so_quotes": ["Θα υλοποιηθεί βασική αυθεντικοποίηση"]
            }},
            "recommendation": "Προσθέστε λεπτομέρειες πολυπαραγοντικής αυθεντικοποίησης στο SEC-3.1",
            "proposed_text": null,
            "confidence": 0.95
        }}
    ],
    "scores": {{
        "integration_consistency": 0.80,
        "requirements_coverage": 0.65,
        "security_readiness": 0.75,
        "operability": 0.85
    }},
    "status": "ok"
}}

Αν δεν παρέχεται επαρκές περιβάλλον, απαντήστε με: {{"status": "insufficient"}}"""
)

# Paragraph Improvement Template
PARAGRAPH_IMPROVEMENT_TEMPLATE = PromptTemplate(
    template_en="""Provide targeted improvement suggestions for specific Solution Outline sections.

## Context
Project: {project_id}
Analysis Type: Paragraph/Section Improvement
Focus Area: {focus_area}

## Target Section(s)
{target_sections}

## Related Requirements (for context)
{requirements}

## Related Diagrams (for context)
{diagrams}

## Task
Analyze the target section(s) and provide specific improvement suggestions focusing on:
1. Clarity and readability
2. Technical accuracy and completeness
3. Alignment with requirements and diagrams
4. Best practices for solution architecture documentation
5. {focus_area} (if specified)

## Response Format
Respond with valid JSON matching this schema:
{{
    "suggestions": [
        {{
            "id": "SUG-001",
            "type": "rewrite",
            "severity": "minor",
            "location": {{
                "so_section_id": "SEC-2.1",
                "paragraph_index": 0
            }},
            "summary": "Improve clarity of component description",
            "rationale": "Current description is too technical and lacks business context",
            "evidence": {{
                "requirements": ["REQ-8"],
                "diagrams": [{{
                    "diagram_id": "C4-Container",
                    "steps": []
                }}],
                "so_quotes": ["The microservice handles data processing"]
            }},
            "recommendation": "Rewrite to include business purpose and technical details",
            "proposed_text": "The Data Processing Service is a microservice responsible for transforming raw customer data into actionable insights. It receives data from the API Gateway, applies business rules defined in REQ-8, and outputs structured data for downstream analytics systems.",
            "confidence": 0.85
        }}
    ],
    "scores": {{
        "integration_consistency": 0.90,
        "requirements_coverage": 0.85,
        "security_readiness": 0.80,
        "operability": 0.75
    }},
    "status": "ok"
}}

If insufficient context is provided, respond with: {{"status": "insufficient"}}""",
    
    template_el="""Παρέχετε στοχευμένες προτάσεις βελτίωσης για συγκεκριμένες ενότητες του Solution Outline.

## Περιβάλλον
Έργο: {project_id}
Τύπος Ανάλυσης: Βελτίωση Παραγράφου/Ενότητας
Περιοχή Εστίασης: {focus_area}

## Στοχευόμενη(ες) Ενότητα(ες)
{target_sections}

## Σχετικές Απαιτήσεις (για περιβάλλον)
{requirements}

## Σχετικά Διαγράμματα (για περιβάλλον)
{diagrams}

## Εργασία
Αναλύστε τη(ις) στοχευόμενη(ες) ενότητα(ες) και παρέχετε συγκεκριμένες προτάσεις βελτίωσης εστιάζοντας σε:
1. Σαφήνεια και αναγνωσιμότητα
2. Τεχνική ακρίβεια και πληρότητα
3. Ευθυγράμμιση με απαιτήσεις και διαγράμματα
4. Βέλτιστες πρακτικές για τεκμηρίωση αρχιτεκτονικής λύσης
5. {focus_area} (αν προσδιορίζεται)

## Μορφή Απάντησης
Απαντήστε με έγκυρο JSON που ταιριάζει σε αυτό το σχήμα:
{{
    "suggestions": [
        {{
            "id": "SUG-001",
            "type": "rewrite",
            "severity": "minor",
            "location": {{
                "so_section_id": "SEC-2.1",
                "paragraph_index": 0
            }},
            "summary": "Βελτίωση σαφήνειας περιγραφής στοιχείου",
            "rationale": "Η τρέχουσα περιγραφή είναι πολύ τεχνική και στερείται επιχειρηματικού περιβάλλοντος",
            "evidence": {{
                "requirements": ["REQ-8"],
                "diagrams": [{{
                    "diagram_id": "C4-Container",
                    "steps": []
                }}],
                "so_quotes": ["Η μικροϋπηρεσία χειρίζεται την επεξεργασία δεδομένων"]
            }},
            "recommendation": "Ξαναγράψτε για να περιλάβετε επιχειρηματικό σκοπό και τεχνικές λεπτομέρειες",
            "proposed_text": "Η Υπηρεσία Επεξεργασίας Δεδομένων είναι μια μικροϋπηρεσία υπεύθυνη για τη μετατροπή ακατέργαστων δεδομένων πελατών σε χρήσιμες πληροφορίες. Λαμβάνει δεδομένα από το API Gateway, εφαρμόζει επιχειρηματικούς κανόνες που ορίζονται στη REQ-8, και παράγει δομημένα δεδομένα για συστήματα ανάλυσης.",
            "confidence": 0.85
        }}
    ],
    "scores": {{
        "integration_consistency": 0.90,
        "requirements_coverage": 0.85,
        "security_readiness": 0.80,
        "operability": 0.75
    }},
    "status": "ok"
}}

Αν δεν παρέχεται επαρκές περιβάλλον, απαντήστε με: {{"status": "insufficient"}}"""
)

# Q&A Template
QNA_TEMPLATE = PromptTemplate(
    template_en="""Answer the user's question using only the provided project context.

## Context
Project: {project_id}
Question: {question}

## Available Information

### Solution Outline Sections
{so_sections}

### Requirements
{requirements}

### Diagrams
{diagrams}

### Chat Summary
{chat_summary}

## Instructions
1. Answer the question using ONLY the information provided above
2. Be concise and direct
3. If the provided context is insufficient to answer the question, respond with exactly: "INSUFFICIENT"
4. Do not use markdown formatting
5. Provide specific references to sections, requirements, or diagrams when relevant

## Response
Provide a plain text answer (no JSON, no markdown):""",
    
    template_el="""Απαντήστε στην ερώτηση του χρήστη χρησιμοποιώντας μόνο το παρεχόμενο περιβάλλον του έργου.

## Περιβάλλον
Έργο: {project_id}
Ερώτηση: {question}

## Διαθέσιμες Πληροφορίες

### Ενότητες Solution Outline
{so_sections}

### Απαιτήσεις
{requirements}

### Διαγράμματα
{diagrams}

### Περίληψη Συνομιλίας
{chat_summary}

## Οδηγίες
1. Απαντήστε στην ερώτηση χρησιμοποιώντας ΜΟΝΟ τις πληροφορίες που παρέχονται παραπάνω
2. Να είστε συνοπτικοί και άμεσοι
3. Αν το παρεχόμενο περιβάλλον δεν επαρκεί για να απαντήσετε στην ερώτηση, απαντήστε ακριβώς: "INSUFFICIENT"
4. Μη χρησιμοποιείτε μορφοποίηση markdown
5. Παρέχετε συγκεκριμένες αναφορές σε ενότητες, απαιτήσεις ή διαγράμματα όταν είναι σχετικό

## Απάντηση
Παρέχετε απάντηση σε απλό κείμενο (όχι JSON, όχι markdown):"""
)


class PromptManager:
    """Manager for prompt templates with language support."""
    
    def __init__(self):
        """Initialize prompt manager with all templates."""
        self.templates = {
            "intent_detection": INTENT_DETECTION_TEMPLATE,
            "integration_check": INTEGRATION_CHECK_TEMPLATE,
            "requirements_coverage": REQUIREMENTS_COVERAGE_TEMPLATE,
            "paragraph_improvement": PARAGRAPH_IMPROVEMENT_TEMPLATE,
            "qna": QNA_TEMPLATE
        }
    
    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """Get a template by name."""
        return self.templates.get(template_name)
    
    def format_prompt(self, template_name: str, language: Language = Language.ENGLISH, **kwargs) -> str:
        """Format a prompt template with variables."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        return template.format(language=language, **kwargs)
    
    def get_available_templates(self) -> list:
        """Get list of available template names."""
        return list(self.templates.keys())


# Global prompt manager instance
prompt_manager = PromptManager()