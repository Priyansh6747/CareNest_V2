import spacy
import scispacy
from scispacy.abbreviation import AbbreviationDetector
from scispacy.linking import EntityLinker
import pandas as pd
from typing import List, Dict, Tuple, Optional
import re

class MedicalNERExtractor:
    # def __init__(self, model_name: str = "en_core_sci_sm"):
    #     """
    #     Initialize medical NER extractor with scispaCy
        
    #     Args:
    #         model_name: "en_core_sci_sm", "en_core_sci_md", or "en_core_sci_lg"
    #     """
    #     self.nlp = None
    #     self.model_name = model_name
    #     self.load_model()
        
    #     # Custom patterns for medical entities
    #     self.custom_patterns = self._create_custom_patterns()

    def __init__(self, model_name: str = "en_core_sci_sm"):
        self.nlp = None
        self.model_name = model_name

        # ✅ Create patterns FIRST
        self.custom_patterns = self._create_custom_patterns()

        # ✅ Then load model
        self.load_model()


    def _create_custom_patterns(self) -> List[Dict]:
        """Create custom patterns for medical entities"""
        patterns = []
        
        # Medication patterns
        medication_patterns = [
            {"label": "MEDICATION", "pattern": [{"LOWER": {"IN": [
                "aspirin", "ibuprofen", "acetaminophen", "metformin",
                "lisinopril", "atorvastatin", "amlodipine", "metoprolol"
            ]}}]},
            {"label": "MEDICATION", "pattern": [
                {"POS": "PROPN", "OP": "?"},
                {"LIKE_NUM": True},
                {"LOWER": {"IN": ["mg", "g", "ml"]}},
                {"LOWER": {"IN": ["daily", "bid", "tid", "qid", "qhs"]}, "OP": "?"}
            ]}
        ]
        patterns.extend(medication_patterns)
        
        # Lab value patterns
        lab_patterns = [
            {"label": "MEASUREMENT", "pattern": [
                {"TEXT": {"REGEX": r"^(BP|HR|RR|Temp|SpO2|O2|BMI)"}},
                {"TEXT": ":", "OP": "?"},
                {"LIKE_NUM": True},
                {"TEXT": {"REGEX": r"^(mmHg|bpm|/min|°F|°C|%)"}, "OP": "?"}
            ]},
            {"label": "MEASUREMENT", "pattern": [
                {"TEXT": {"REGEX": r"^(WBC|RBC|HGB|HCT|PLT|ALT|AST|BUN|Cr|Na|K|Glucose)"}},
                {"TEXT": ":", "OP": "?"},
                {"LIKE_NUM": True},
                {"TEXT": {"REGEX": r"^[a-zA-Z/μLdL]+$"}, "OP": "?"}
            ]}
        ]
        patterns.extend(lab_patterns)
        
        return patterns
        
    def load_model(self):
        """Load the scispaCy model with necessary components"""
        try:
            # Load base model
            self.nlp = spacy.load(self.model_name)
            
            # Add abbreviation detector
            self.nlp.add_pipe("abbreviation_detector")
            
            # Add UMLS linker (optional)
            # self.nlp.add_pipe("scispacy_linker", 
            #                  config={"resolve_abbreviations": True, 
            #                         "linker_name": "umls"})
            
            # Add custom entity ruler
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            ruler.add_patterns(self.custom_patterns)
            
            print(f"✅ Model '{self.model_name}' loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            # Fallback to small English model
            self.nlp = spacy.load("en_core_web_sm")
    
    
    
    def extract_entities(self, text: str, 
                        confidence_threshold: float = 0.7,
                        entity_types: Optional[List[str]] = None) -> Tuple[pd.DataFrame, str]:
        """
        Extract medical entities from text
        
        Returns:
            DataFrame with entities and HTML highlighted text
        """
        # Process text
        doc = self.nlp(text)
        
        entities = []
        html_text = text
        
        for ent in doc.ents:
            # Filter by entity type if specified
            if entity_types and ent.label_ not in entity_types:
                continue
            
            # Get confidence (scispaCy doesn't provide confidence by default)
            confidence = 0.9  # Default confidence
            
            entities.append({
                "text": ent.text,
                "entity_type": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": confidence
            })
        
        # Sort entities by start position for HTML highlighting
        entities.sort(key=lambda x: x["start"], reverse=True)
        
        # Create highlighted HTML text
        for entity in entities:
            color_map = {
                "MEDICATION": "medication",
                "CONDITION": "condition",
                "PROCEDURE": "procedure",
                "ANATOMY": "anatomy",
                "MEASUREMENT": "measurement",
                "DATE": "measurement"  # Using measurement color for dates
            }
            
            color_class = color_map.get(entity["entity_type"], "measurement")
            
            # Wrap entity in span with class
            span = f'<span class="entity-tag {color_class}" title="{entity["entity_type"]}">{entity["text"]}</span>'
            
            # Insert into HTML
            html_text = (
                html_text[:entity["start"]] + 
                span + 
                html_text[entity["end"]:]
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(entities)
        
        return df, html_text
    
    def extract_medications(self, text: str) -> List[Dict]:
        """Specialized medication extraction"""
        doc = self.nlp(text)
        medications = []
        
        for ent in doc.ents:
            if ent.label_ == "MEDICATION":
                # Look for dosage pattern
                dosage = self._extract_dosage(ent.text, text[ent.start_char:ent.start_char+100])
                
                medications.append({
                    "name": ent.text,
                    "dosage": dosage,
                    "context": text[max(0, ent.start_char-50):min(len(text), ent.end_char+50)]
                })
        
        return medications
    
    def _extract_dosage(self, medication: str, context: str) -> str:
        """Extract dosage information from context"""
        patterns = [
            r"(\d+\.?\d*)\s*(mg|g|ml|µg)\s*(?:daily|BID|TID|QID|QHS|q\.?d\.?|b\.?i\.?d\.?|t\.?i\.?d\.?|q\.?i\.?d\.?)",
            r"(\d+\.?\d*)\s*(mg|g|ml|µg)",
            r"(\d+)\s*mg"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""