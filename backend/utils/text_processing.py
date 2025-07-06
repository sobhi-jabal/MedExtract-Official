"""
Text processing utilities for medical text extraction
Based on preprocessing patterns from provided examples
"""

import re
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple


class TextProcessor:
    """
    Text preprocessing utilities for medical documents
    """
    
    def __init__(self):
        # Medical section patterns (from ds_btrads example)
        self.medical_sections = [
            (r"Oncology Treatment History:", "treatment_history"),
            (r"Current Medications:", "current_medications"),
            (r"Treatment to be received:", "treatment_plan"),
            (r"History of Present Illness:", "present_illness"),
            (r"Assessment & Plan:", "assessment_plan"),
            (r"Subjective:", "subjective"),
            (r"Objective:", "objective"),
            (r"Past Medical History:", "past_medical"),
            (r"Past Surgical History:", "past_surgical"),
            (r"Social History:", "social_history"),
            (r"Review of Systems:", "review_systems"),
            (r"Physical Exam:", "physical_exam"),
            (r"Laboratory:", "laboratory"),
            (r"Allergies:", "allergies"),
            (r"Indication:", "indication"),
            (r"Reason for Exam:", "indication"),
            (r"History:", "indication"),
            (r"DX:", "indication"),
            (r"Impression:", "impression"),
            (r"IMP:", "impression"),
            (r"Conclusion:", "impression"),
            (r"Summary:", "impression"),
        ]
    
    def preprocess(self, text: str) -> str:
        """
        Main preprocessing function
        Based on patterns from all provided examples
        """
        if not text or pd.isna(text):
            return ""
        
        text = str(text)
        
        # Basic cleaning (from original medextract.py)
        text = self._basic_clean(text)
        
        # Medical-specific cleaning
        text = self._medical_clean(text)
        
        # Normalize whitespace
        text = self._normalize_whitespace(text)
        
        return text.strip()
    
    def _basic_clean(self, text: str) -> str:
        """Basic text cleaning"""
        # Replace common Unicode issues
        text = (
            text.replace('"', '"')
            .replace("'", "'")
            .replace("'", "'")
            .replace("–", "-")
            .replace("—", "-")
            .replace("…", "...")
        )
        
        # Remove non-printable characters except newlines, tabs, carriage returns
        text = "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\t\r")
        
        return text
    
    def _medical_clean(self, text: str) -> str:
        """Medical document specific cleaning"""
        # Normalize line breaks (from multiple examples)
        text = re.sub(r'\n(?!\.)', ' ', text)  # Single newlines → space
        text = re.sub(r"\.\\n", " \\n ", text)  # Keep paragraph breaks
        
        # Remove excessive newlines
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        
        # Clean up common medical formatting issues
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'([.!?])\s*\n\s*([A-Z])', r'\1 \2', text)  # Join sentences
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace while preserving structure"""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Normalize line endings
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)
        
        # Limit consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def detect_medical_sections(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Detect medical sections in text
        Based on ds_btrads example
        """
        sections: List[Tuple[str, int, int]] = []
        
        for pattern, name in self.medical_sections:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                sections.append((name, match.start(), match.end()))
        
        # Sort by position and calculate end positions
        sections.sort(key=lambda x: x[1])
        
        final_sections: List[Tuple[str, int, int]] = []
        for i, (name, start, _) in enumerate(sections):
            end = sections[i + 1][1] if i < len(sections) - 1 else len(text)
            final_sections.append((name, start, end))
        
        return final_sections
    
    def extract_section(self, text: str, section_name: str) -> Optional[str]:
        """Extract specific medical section"""
        sections = self.detect_medical_sections(text)
        
        for name, start, end in sections:
            if name == section_name:
                return text[start:end].strip()
        
        return None
    
    def chunk_by_sections(self, text: str, max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Chunk text by medical sections with metadata
        Based on smart_medical_chunker from ds_btrads example
        """
        cleaned_text = self.preprocess(text)
        sections = self.detect_medical_sections(cleaned_text)
        chunks = []
        chunk_id = 0
        
        if not sections:
            # No sections detected, use standard chunking
            return self._standard_chunk(cleaned_text, max_chunk_size)
        
        for name, start, end in sections:
            section_text = cleaned_text[start:end]
            
            if len(section_text) <= max_chunk_size:
                # Section fits in one chunk
                chunks.append({
                    "chunk_id": chunk_id,
                    "content": section_text,
                    "section": name,
                    "start_pos": start,
                    "end_pos": end,
                    "source_type": "section_chunk"
                })
                chunk_id += 1
            else:
                # Split large section into smaller chunks
                sub_chunks = self._split_large_section(
                    section_text, max_chunk_size, name, start, end
                )
                for sub_chunk in sub_chunks:
                    sub_chunk["chunk_id"] = chunk_id
                    chunks.append(sub_chunk)
                    chunk_id += 1
        
        return chunks
    
    def _standard_chunk(self, text: str, max_chunk_size: int) -> List[Dict[str, Any]]:
        """Standard text chunking without section awareness"""
        chunks = []
        
        # Simple sentence-based chunking
        sentences = re.split(r'[.!?]+', text)
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) <= max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append({
                        "chunk_id": chunk_id,
                        "content": current_chunk.strip(),
                        "section": "unknown",
                        "start_pos": 0,
                        "end_pos": len(current_chunk),
                        "source_type": "regular_chunk"
                    })
                    chunk_id += 1
                current_chunk = sentence + ". "
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "chunk_id": chunk_id,
                "content": current_chunk.strip(),
                "section": "unknown", 
                "start_pos": 0,
                "end_pos": len(current_chunk),
                "source_type": "regular_chunk"
            })
        
        return chunks
    
    def _split_large_section(
        self, 
        section_text: str, 
        max_chunk_size: int, 
        section_name: str,
        section_start: int,
        section_end: int
    ) -> List[Dict[str, Any]]:
        """Split large medical section into smaller chunks"""
        chunks = []
        
        # Try to split by sentences first
        sentences = re.split(r'[.!?]+', section_text)
        current_chunk = ""
        part_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) <= max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "section": section_name,
                        "section_part": part_index,
                        "start_pos": section_start,
                        "end_pos": section_end,
                        "source_type": "section_subchunk"
                    })
                    part_index += 1
                current_chunk = sentence + ". "
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "section": section_name,
                "section_part": part_index,
                "start_pos": section_start,
                "end_pos": section_end,
                "source_type": "section_subchunk"
            })
        
        return chunks
    
    def extract_key_terms(self, text: str, max_terms: int = 10) -> List[str]:
        """Extract key medical terms for query generation"""
        # Simple keyword extraction based on medical patterns
        medical_keywords = []
        
        # Look for medical conditions, medications, procedures
        patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:syndrome|disease|disorder|condition)\b',
            r'\b\w+(?:statin|mycin|cillin|parin|zole|pine|tide)\b',  # Common drug endings
            r'\bMRI|CT|PET|X-ray|ultrasound|mammography\b',  # Imaging
            r'\b\w+(?:ectomy|oscopy|tomy|plasty|graphy)\b',  # Procedures
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            medical_keywords.extend(matches)
        
        # Remove duplicates and return top terms
        unique_terms = list(set(medical_keywords))
        return unique_terms[:max_terms]
    
    def validate_medical_text(self, text: str) -> Dict[str, Any]:
        """Validate that text appears to be medical content"""
        if not text or len(text.strip()) < 10:
            return {"valid": False, "reason": "Text too short"}
        
        # Check for medical indicators
        medical_indicators = [
            r'\bpatient\b', r'\bdiagnosis\b', r'\btreatment\b', r'\bmedication\b',
            r'\bsymptoms?\b', r'\bhospital\b', r'\bclinic\b', r'\bdoctor\b',
            r'\bnurse\b', r'\btherapy\b', r'\bmedical\b', r'\bclinical\b'
        ]
        
        indicator_count = 0
        for pattern in medical_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                indicator_count += 1
        
        # Require at least 2 medical indicators
        if indicator_count >= 2:
            return {"valid": True, "confidence": min(indicator_count / 5.0, 1.0)}
        else:
            return {"valid": False, "reason": "Insufficient medical content indicators"}