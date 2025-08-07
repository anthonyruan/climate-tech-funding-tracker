#!/usr/bin/env python3
"""
Demo Setup Script - Add sample data for demonstration
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.append(str(Path(__file__).parent))

from src.db_operations import DatabaseOperations

def create_sample_data():
    """Create sample funding data for demonstration"""
    db = DatabaseOperations()
    
    print("🌱 Setting up demo data for Climate Tech Funding Tracker...")
    
    # Sample companies with climate tech focus
    sample_companies = [
        {
            "name": "SolarFlow Technologies",
            "description": "Next-generation perovskite solar cell manufacturer",
            "sector": "Clean Energy",
            "location": "Palo Alto, CA",
            "funding": {"amount": 45_000_000, "stage": "Series B", "text": "$45M"}
        },
        {
            "name": "CarbonZero Solutions",
            "description": "Direct air capture and carbon storage technology",
            "sector": "Carbon Capture & Removal", 
            "location": "Austin, TX",
            "funding": {"amount": 120_000_000, "stage": "Series C", "text": "$120M"}
        },
        {
            "name": "GreenFuels Corp",
            "description": "Sustainable aviation fuel from agricultural waste",
            "sector": "Alternative Fuels",
            "location": "Seattle, WA", 
            "funding": {"amount": 75_000_000, "stage": "Series B", "text": "$75M"}
        },
        {
            "name": "HydroGen Power",
            "description": "Green hydrogen production and distribution",
            "sector": "Green Hydrogen",
            "location": "Denver, CO",
            "funding": {"amount": 200_000_000, "stage": "Series D", "text": "$200M"}
        },
        {
            "name": "EcoProtein Labs",
            "description": "Lab-grown alternative proteins using fermentation",
            "sector": "Alternative Proteins",
            "location": "Boston, MA",
            "funding": {"amount": 30_000_000, "stage": "Series A", "text": "$30M"}
        },
        {
            "name": "SmartGrid Analytics",
            "description": "AI-powered grid optimization and energy management",
            "sector": "Smart Grid",
            "location": "San Francisco, CA",
            "funding": {"amount": 25_000_000, "stage": "Series A", "text": "$25M"}
        },
        {
            "name": "ClimateAdapt Tech",
            "description": "Climate resilience solutions for agriculture",
            "sector": "Climate Adaptation", 
            "location": "Miami, FL",
            "funding": {"amount": 15_000_000, "stage": "Seed", "text": "$15M"}
        },
        {
            "name": "BatteryNext",
            "description": "Next-gen lithium-sulfur battery technology",
            "sector": "Energy Storage",
            "location": "Detroit, MI",
            "funding": {"amount": 80_000_000, "stage": "Series B", "text": "$80M"}
        }
    ]
    
    # Sample investors
    sample_investors = [
        {"name": "Climate Ventures", "type": "VC", "focus": ["Clean Energy", "Carbon Capture"]},
        {"name": "Green Future Capital", "type": "VC", "focus": ["Energy Storage", "Smart Grid"]},
        {"name": "Breakthrough Energy", "type": "Corporate VC", "focus": ["Climate Tech"]},
        {"name": "Amazon Climate Pledge Fund", "type": "Corporate VC", "focus": ["Sustainability"]},
        {"name": "Tesla Ventures", "type": "Corporate VC", "focus": ["Energy", "Transportation"]},
        {"name": "Sequoia Climate", "type": "VC", "focus": ["Climate Tech", "Clean Energy"]},
        {"name": "Khosla Ventures", "type": "VC", "focus": ["Clean Tech", "Energy"]},
        {"name": "GV (Google Ventures)", "type": "Corporate VC", "focus": ["Technology", "AI"]},
    ]
    
    # Create investors
    investor_ids = {}
    for investor in sample_investors:
        investor_id = db.get_or_create_investor(
            name=investor["name"],
            investor_type=investor["type"],
            focus_areas=investor["focus"]
        )
        investor_ids[investor["name"]] = investor_id
    
    # Create companies and funding events
    base_date = datetime.now() - timedelta(days=180)  # Start 6 months ago
    
    for i, company in enumerate(sample_companies):
        # Create company
        company_id = db.get_or_create_company(
            name=company["name"],
            description=company["description"],
            sector=company["sector"],
            location=company["location"]
        )
        
        # Create funding event
        announcement_date = (base_date + timedelta(days=random.randint(0, 180))).strftime('%Y-%m-%d')
        
        funding_id = db.create_funding_event(
            company_id=company_id,
            amount=company["funding"]["amount"],
            amount_text=company["funding"]["text"],
            funding_stage=company["funding"]["stage"],
            announcement_date=announcement_date,
            source_url=f"https://demo-news.com/funding/{company['name'].lower().replace(' ', '-')}",
            source_name="Demo News",
            title=f"{company['name']} Raises {company['funding']['text']} in {company['funding']['stage']} Funding",
            summary=f"{company['name']} has raised {company['funding']['text']} to expand their {company['description'].lower()}"
        )
        
        # Add random investors
        selected_investors = random.sample(list(investor_ids.keys()), random.randint(2, 4))
        
        for j, investor_name in enumerate(selected_investors):
            is_lead = (j == 0)  # First investor is lead
            db.add_investor_to_funding(
                funding_id,
                investor_ids[investor_name],
                is_lead_investor=is_lead
            )
    
    print(f"✅ Created {len(sample_companies)} demo companies")
    print(f"✅ Created {len(sample_investors)} demo investors") 
    print(f"✅ Created {len(sample_companies)} demo funding events")
    print("\n🚀 Demo data is ready! You can now explore the application.")
    print("💡 Run 'python run_app.py' to start the web interface.")

if __name__ == "__main__":
    create_sample_data()