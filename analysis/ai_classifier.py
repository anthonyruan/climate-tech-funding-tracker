"""
AI Classifier Module using OpenAI API
Classifies climate tech sectors and generates summaries
"""
import os
from typing import Dict, List, Optional
import json
from openai import OpenAI
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import OPENAI_API_KEY, NLP_CONFIG, CLIMATE_TECH_CATEGORIES

class AIClassifier:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = NLP_CONFIG.get('model', 'gpt-4o-mini')
        self.temperature = NLP_CONFIG.get('temperature', 0.3)
        self.max_tokens = NLP_CONFIG.get('max_tokens', 1000)
    
    def classify_sector(self, text: str, company_name: Optional[str] = None) -> Dict[str, any]:
        """Classify the climate tech sector of a company/article"""
        
        categories_str = ", ".join(CLIMATE_TECH_CATEGORIES)
        
        prompt = f"""
        Based on the following text about a climate tech company or funding event, 
        classify it into one of these climate tech sectors: {categories_str}
        
        Text: {text[:2000]}  # Limit text length
        
        {f"Company name: {company_name}" if company_name else ""}
        
        Return a JSON object with:
        - "sector": the most appropriate sector from the list
        - "confidence": confidence score between 0 and 1
        - "reasoning": brief explanation (max 50 words)
        
        If the text doesn't clearly fit any category, use "Other" with lower confidence.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in climate technology classification."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate sector
            if result.get('sector') not in CLIMATE_TECH_CATEGORIES:
                result['sector'] = 'Other'
                result['confidence'] = 0.5
            
            return result
            
        except Exception as e:
            print(f"Error in sector classification: {e}")
            return {
                "sector": "Other",
                "confidence": 0.0,
                "reasoning": "Classification failed"
            }
    
    def generate_summary(self, text: str, entities: Optional[Dict] = None) -> Dict[str, str]:
        """Generate a structured summary of the funding event"""
        
        entities_context = ""
        if entities:
            if entities.get('companies'):
                entities_context += f"Companies mentioned: {', '.join(entities['companies'])}\n"
            if entities.get('funding_amount'):
                entities_context += f"Funding amount: {entities['funding_amount']['amount_text']}\n"
            if entities.get('funding_stage'):
                entities_context += f"Funding stage: {entities['funding_stage']}\n"
            if entities.get('investors'):
                investor_names = [inv['name'] for inv in entities['investors']]
                entities_context += f"Investors: {', '.join(investor_names)}\n"
        
        prompt = f"""
        Generate a concise summary of this climate tech funding event.
        
        {entities_context}
        
        Article text: {text[:2000]}
        
        Return a JSON object with:
        - "summary": 2-3 sentence summary of the funding event
        - "key_points": list of 3-5 key points
        - "technology_focus": brief description of the technology/solution
        - "impact_area": environmental impact area (e.g., "carbon reduction", "renewable energy", etc.)
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in climate technology and venture funding."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return {
                "summary": "Summary generation failed",
                "key_points": [],
                "technology_focus": "Unknown",
                "impact_area": "Unknown"
            }
    
    def extract_structured_data(self, text: str) -> Dict[str, any]:
        """Extract structured funding data using AI"""
        
        prompt = f"""
        Extract structured information from this climate tech funding announcement.
        
        Text: {text[:2000]}
        
        Return a JSON object with:
        - "company_name": name of the funded company
        - "company_description": brief description of what the company does
        - "funding_amount": amount raised (as string, e.g., "$10M")
        - "funding_stage": funding round stage
        - "lead_investor": name of lead investor if mentioned
        - "other_investors": list of other investors
        - "use_of_funds": what the funding will be used for
        - "location": company location if mentioned
        - "announcement_date": date if mentioned (ISO format)
        
        For any field not found in the text, use null.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured data from news articles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Lower temperature for more consistent extraction
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error extracting structured data: {e}")
            return {}
    
    def validate_funding_event(self, text: str) -> Dict[str, any]:
        """Validate if the text is about a climate tech funding event"""
        
        prompt = f"""
        Determine if this text is about a climate tech funding event.
        
        Text: {text[:1000]}
        
        Return a JSON object with:
        - "is_funding_event": boolean indicating if this is a funding event
        - "is_climate_tech": boolean indicating if this is related to climate technology
        - "confidence": confidence score between 0 and 1
        - "reasoning": brief explanation
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in identifying climate tech funding news."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error validating funding event: {e}")
            return {
                "is_funding_event": False,
                "is_climate_tech": False,
                "confidence": 0.0,
                "reasoning": "Validation failed"
            }

def main():
    """Test the AI classifier"""
    # Check if API key is set
    if not OPENAI_API_KEY:
        print("Please set OPENAI_API_KEY in your .env file")
        return
    
    classifier = AIClassifier()
    
    # Test text
    test_text = """
    Carbon capture startup Climeworks announced today that it has raised $650 million in funding 
    to scale its direct air capture technology. The Series F round was led by Partners Group and 
    includes participation from existing investors. The company plans to use the funds to build 
    multiple large-scale plants that can remove CO2 directly from the atmosphere, with a goal 
    of achieving megaton-scale removal capacity by 2030.
    """
    
    print("Testing AI Classifier...")
    
    # Test validation
    print("\n1. Validating funding event:")
    validation = classifier.validate_funding_event(test_text)
    print(json.dumps(validation, indent=2))
    
    # Test sector classification
    print("\n2. Classifying sector:")
    sector = classifier.classify_sector(test_text, "Climeworks")
    print(json.dumps(sector, indent=2))
    
    # Test structured extraction
    print("\n3. Extracting structured data:")
    structured = classifier.extract_structured_data(test_text)
    print(json.dumps(structured, indent=2))
    
    # Test summary generation
    print("\n4. Generating summary:")
    summary = classifier.generate_summary(test_text)
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()