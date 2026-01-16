"""
Medical Metadata Extractor - Structured extraction with regex patterns
Optimized for maternal health reports
"""
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExtractionResult:
    """Result of a single extraction with confidence score"""
    value: Any
    raw_text: str
    confidence: float
    unit: Optional[str] = None
    reference_range: Optional[Tuple[float, float]] = None
    is_abnormal: Optional[bool] = None


class MedicalMetadataExtractor:
    """
    Extract structured metadata from medical reports using regex patterns.
    Optimized for maternal health and pregnancy reports.
    """
    
    def __init__(self):
        self._init_patterns()
        self._init_reference_ranges()
    
    def _init_patterns(self):
        """Initialize regex patterns for extraction"""
        
        # Vital signs patterns
        self.vital_patterns = {
            'blood_pressure': [
                r'(?:BP|B\.P\.|Blood\s*Pressure)\s*:?\s*(\d{2,3})\s*/\s*(\d{2,3})\s*(?:mmHg|mm\s*Hg)?',
            ],
            'heart_rate': [
                r'(?:HR|Heart\s*Rate|Pulse)\s*:?\s*(\d{2,3})\s*(?:bpm|/min|beats?\s*per\s*min)?',
            ],
            'temperature': [
                r'(?:Temp|Temperature)\s*:?\s*(\d{2,3}\.?\d?)\s*(?:°?[FC])?',
            ],
            'oxygen_saturation': [
                r'(?:SpO2|O2\s*Sat|Oxygen\s*Saturation?)\s*:?\s*(\d{2,3})\s*%?',
            ],
            'respiratory_rate': [
                r'(?:RR|Resp(?:iratory)?\s*Rate)\s*:?\s*(\d{1,2})\s*(?:/min)?',
            ],
            'weight': [
                r'(?:Weight|Wt)\s*:?\s*(\d{2,3}\.?\d?)\s*(?:kg|lbs?|pounds?)',
            ],
        }
        
        # Lab value patterns
        self.lab_patterns = {
            'hemoglobin': [
                r'(?:Hemoglobin|HGB|Hgb|Hb)\s*:?\s*(\d{1,2}\.?\d?)\s*(?:g/dL|g/L)?',
            ],
            'hematocrit': [
                r'(?:Hematocrit|HCT|Hct)\s*:?\s*(\d{1,2}\.?\d?)\s*%?',
            ],
            'wbc': [
                r'(?:WBC|White\s*Blood\s*Cells?)\s*:?\s*(\d{1,2}\.?\d?)\s*(?:x?\s*10\^?[39]|K|k|/[μu]?L)?',
            ],
            'platelets': [
                r'(?:PLT|Platelets?)\s*:?\s*(\d{2,3})\s*(?:x?\s*10\^?[39]|K|k|/[μu]?L)?',
            ],
            'glucose': [
                r'(?:Glucose|FBS|Fasting\s*Blood\s*Sugar|RBS|Blood\s*Sugar)\s*:?\s*(\d{2,3})\s*(?:mg/dL|mmol/L)?',
            ],
            'hba1c': [
                r'(?:HbA1c|A1C|Glycated\s*Hemoglobin)\s*:?\s*(\d{1,2}\.?\d?)\s*%?',
            ],
            'creatinine': [
                r'(?:Creatinine|Cr)\s*:?\s*(\d\.?\d{1,2})\s*(?:mg/dL|μmol/L)?',
            ],
            'bun': [
                r'(?:BUN|Blood\s*Urea\s*Nitrogen)\s*:?\s*(\d{1,2}\.?\d?)\s*(?:mg/dL)?',
            ],
        }
        
        # Pregnancy-specific patterns
        self.pregnancy_patterns = {
            'gestational_age': [
                r'(?:Gestational\s*Age|GA)\s*:?\s*(\d{1,2})\s*(?:weeks?|wks?)',
                r'(\d{1,2})\s*(?:weeks?|wks?)\s*(?:gestation|gestational|pregnant|GA)',
                r'(\d{1,2})\s*\+\s*(\d)\s*(?:weeks?|wks?)',  # e.g., "28+3 weeks"
            ],
            'gravida_para': [
                r'(G\d+)\s*(P\d+)?\s*(A\d+)?\s*(L\d+)?',
                r'Gravida\s*(\d+)\s*,?\s*Para\s*(\d+)',
            ],
            'edd': [
                r'(?:EDD|Estimated\s*Due\s*Date|Due\s*Date)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'(?:EDD|Due)\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4})',
            ],
            'lmp': [
                r'(?:LMP|Last\s*Menstrual\s*Period)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
            'fetal_heart_rate': [
                r'(?:FHR|Fetal\s*Heart\s*Rate|Fetal\s*HR)\s*:?\s*(\d{2,3})\s*(?:bpm)?',
            ],
            'fundal_height': [
                r'(?:Fundal\s*Height|FH)\s*:?\s*(\d{1,2}\.?\d?)\s*(?:cm|weeks?)?',
            ],
        }
        
        # Date patterns
        self.date_patterns = {
            'visit_date': [
                r'(?:Visit\s*Date|Date\s*of\s*Visit|DOV)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'(?:Date)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
        }
        
        # Demographics patterns
        self.demographics_patterns = {
            'age': [
                r'(\d{1,3})\s*(?:years?\s*old|y/?o|yo)',
                r'Age\s*:?\s*(\d{1,3})',
            ],
            'name': [
                r'(?:Patient|Name)\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            ],
        }
    
    def _init_reference_ranges(self):
        """Initialize reference ranges for maternal health"""
        # General ranges (some adjusted for pregnancy)
        self.reference_ranges = {
            'hemoglobin': (10.5, 14.5),  # Lower threshold in pregnancy
            'hematocrit': (31, 41),  # Adjusted for pregnancy
            'wbc': (6.0, 16.0),  # Higher in pregnancy
            'platelets': (150, 400),
            'glucose': (70, 140),
            'fasting_glucose': (70, 95),  # Stricter for gestational diabetes screening
            'hba1c': (4.0, 5.6),
            'creatinine': (0.4, 0.9),  # Lower in pregnancy
            'bp_systolic': (90, 140),
            'bp_diastolic': (60, 90),
            'heart_rate': (60, 100),
            'temperature': (97.0, 99.5),
            'oxygen_saturation': (95, 100),
            'fetal_heart_rate': (110, 160),
        }
    
    def _extract_with_patterns(
        self, 
        text: str, 
        patterns: List[str], 
        base_confidence: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Extract values using a list of regex patterns"""
        results = []
        
        for i, pattern in enumerate(patterns):
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Higher confidence for earlier patterns (more specific)
                confidence = base_confidence - (i * 0.05)
                results.append({
                    'match': match,
                    'groups': match.groups(),
                    'text': match.group(0),
                    'confidence': max(confidence, 0.5)
                })
        
        return results
    
    def extract_vitals(self, text: str) -> Dict[str, ExtractionResult]:
        """Extract vital signs from text"""
        vitals = {}
        
        for vital_name, patterns in self.vital_patterns.items():
            matches = self._extract_with_patterns(text, patterns)
            if matches:
                match = matches[0]  # Take first match
                
                if vital_name == 'blood_pressure' and len(match['groups']) >= 2:
                    systolic = float(match['groups'][0])
                    diastolic = float(match['groups'][1])
                    
                    vitals['bp_systolic'] = ExtractionResult(
                        value=systolic,
                        raw_text=match['text'],
                        confidence=match['confidence'],
                        unit='mmHg',
                        reference_range=self.reference_ranges.get('bp_systolic'),
                        is_abnormal=systolic < 90 or systolic > 140
                    )
                    vitals['bp_diastolic'] = ExtractionResult(
                        value=diastolic,
                        raw_text=match['text'],
                        confidence=match['confidence'],
                        unit='mmHg',
                        reference_range=self.reference_ranges.get('bp_diastolic'),
                        is_abnormal=diastolic < 60 or diastolic > 90
                    )
                else:
                    value = float(match['groups'][0]) if match['groups'][0] else None
                    if value:
                        ref_range = self.reference_ranges.get(vital_name.replace('_', ''))
                        is_abnormal = None
                        if ref_range:
                            is_abnormal = value < ref_range[0] or value > ref_range[1]
                        
                        vitals[vital_name] = ExtractionResult(
                            value=value,
                            raw_text=match['text'],
                            confidence=match['confidence'],
                            reference_range=ref_range,
                            is_abnormal=is_abnormal
                        )
        
        return vitals
    
    def extract_lab_values(self, text: str) -> Dict[str, ExtractionResult]:
        """Extract laboratory values from text"""
        labs = {}
        
        for lab_name, patterns in self.lab_patterns.items():
            matches = self._extract_with_patterns(text, patterns)
            if matches:
                match = matches[0]
                value = float(match['groups'][0]) if match['groups'][0] else None
                
                if value:
                    ref_range = self.reference_ranges.get(lab_name)
                    is_abnormal = None
                    if ref_range:
                        is_abnormal = value < ref_range[0] or value > ref_range[1]
                    
                    labs[lab_name] = ExtractionResult(
                        value=value,
                        raw_text=match['text'],
                        confidence=match['confidence'],
                        reference_range=ref_range,
                        is_abnormal=is_abnormal
                    )
        
        return labs
    
    def extract_pregnancy_data(self, text: str) -> Dict[str, ExtractionResult]:
        """Extract pregnancy-specific data"""
        pregnancy = {}
        
        for field_name, patterns in self.pregnancy_patterns.items():
            matches = self._extract_with_patterns(text, patterns, base_confidence=0.85)
            if matches:
                match = matches[0]
                
                if field_name == 'gestational_age':
                    # Handle "28+3 weeks" format
                    if len(match['groups']) >= 2 and match['groups'][1]:
                        weeks = int(match['groups'][0])
                        days = int(match['groups'][1])
                        value = f"{weeks}+{days}"
                    else:
                        value = int(match['groups'][0])
                    
                    pregnancy[field_name] = ExtractionResult(
                        value=value,
                        raw_text=match['text'],
                        confidence=match['confidence'],
                        unit='weeks'
                    )
                
                elif field_name == 'gravida_para':
                    pregnancy[field_name] = ExtractionResult(
                        value=''.join(g for g in match['groups'] if g),
                        raw_text=match['text'],
                        confidence=match['confidence']
                    )
                
                elif field_name == 'fetal_heart_rate':
                    value = int(match['groups'][0])
                    ref_range = self.reference_ranges.get('fetal_heart_rate')
                    pregnancy[field_name] = ExtractionResult(
                        value=value,
                        raw_text=match['text'],
                        confidence=match['confidence'],
                        unit='bpm',
                        reference_range=ref_range,
                        is_abnormal=value < 110 or value > 160
                    )
                
                else:
                    pregnancy[field_name] = ExtractionResult(
                        value=match['groups'][0] if match['groups'] else match['text'],
                        raw_text=match['text'],
                        confidence=match['confidence']
                    )
        
        return pregnancy
    
    def extract_demographics(self, text: str) -> Dict[str, ExtractionResult]:
        """Extract patient demographics"""
        demographics = {}
        
        for field_name, patterns in self.demographics_patterns.items():
            matches = self._extract_with_patterns(text, patterns, base_confidence=0.75)
            if matches:
                match = matches[0]
                demographics[field_name] = ExtractionResult(
                    value=match['groups'][0] if match['groups'] else None,
                    raw_text=match['text'],
                    confidence=match['confidence']
                )
        
        return demographics
    
    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        Extract all metadata from text.
        
        Returns:
            Dictionary with all extracted metadata organized by category
        """
        vitals = self.extract_vitals(text)
        labs = self.extract_lab_values(text)
        pregnancy = self.extract_pregnancy_data(text)
        demographics = self.extract_demographics(text)
        
        # Convert ExtractionResults to dict for JSON serialization
        def to_dict(results: Dict[str, ExtractionResult]) -> Dict[str, Any]:
            return {
                key: {
                    'value': r.value,
                    'raw_text': r.raw_text,
                    'confidence': r.confidence,
                    'unit': r.unit,
                    'reference_range': r.reference_range,
                    'is_abnormal': r.is_abnormal
                }
                for key, r in results.items()
            }
        
        # Count abnormal findings
        all_results = {**vitals, **labs, **pregnancy}
        abnormal_count = sum(1 for r in all_results.values() if r.is_abnormal)
        
        return {
            'vitals': to_dict(vitals),
            'lab_values': to_dict(labs),
            'pregnancy_data': to_dict(pregnancy),
            'demographics': to_dict(demographics),
            'summary': {
                'vitals_count': len(vitals),
                'labs_count': len(labs),
                'pregnancy_fields': len(pregnancy),
                'abnormal_findings': abnormal_count,
                'extraction_confidence': self._calculate_overall_confidence(all_results)
            }
        }
    
    def _calculate_overall_confidence(self, results: Dict[str, ExtractionResult]) -> float:
        """Calculate average confidence across all extractions"""
        if not results:
            return 0.0
        confidences = [r.confidence for r in results.values()]
        return round(sum(confidences) / len(confidences), 2)
