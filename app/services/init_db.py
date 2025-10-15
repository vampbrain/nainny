"""
Initialize database and seed Indian cultural data
Run this first to set up the system
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import init_db
from app.models.cultural import CulturalContext, IndianFestival, CulturalMapping
from datetime import datetime


def seed_indian_cultural_data():
    """Seed initial Indian cultural data"""
    # ensure schema exists (helpful in test environments)
    init_db()

    print("\n Seeding Indian cultural data...")
    
    # import get_db here to ensure it binds to the current app.core.database
    from app.core.database import get_db

    with get_db() as db:
        # Check if already seeded
        if db.query(CulturalContext).count() > 0:
            print("! Cultural data already exists. Skipping seed.")
            return
        
        # Indian festivals
        festivals = [
            IndianFestival(
                name='Diwali',
                regional_names=['Deepavali', 'Divali'],
                month='October-November',
                season='autumn',
                significance='Festival of lights celebrating victory of light over darkness, good over evil',
                story_elements=['Rama returning to Ayodhya', 'Lakshmi worship', 'lights', 'victory'],
                common_activities=['lighting diyas', 'bursting crackers', 'rangoli', 'sweets distribution'],
                traditional_foods=['ladoo', 'jalebi', 'barfi', 'namak pare'],
                decorations=['diyas', 'rangoli', 'lights', 'flowers'],
                child_friendly_explanation='Diwali is when we light up our homes with lamps and celebrate goodness winning!',
                story_hooks=['hero returns home', 'defeating evil', 'family celebration'],
                age_appropriate='all',
                popularity_score=1.0
            ),
            IndianFestival(
                name='Holi',
                regional_names=['Phagwah', 'Dol Jatra'],
                month='March',
                season='spring',
                significance='Festival of colors celebrating spring, love, and new beginnings',
                story_elements=['Prahlad and Holika', 'Krishna and Radha', 'colors', 'playfulness'],
                common_activities=['playing with colors', 'water balloons', 'dancing', 'singing'],
                traditional_foods=['gujiya', 'thandai', 'malpua'],
                decorations=['colors', 'flowers'],
                child_friendly_explanation='Holi is when we play with colors and celebrate friendship and fun!',
                story_hooks=['playing together', 'friendship', 'mischief', 'celebration'],
                age_appropriate='all',
                popularity_score=0.9
            ),
        ]
        
        db.add_all(festivals)
        print(f" Added {len(festivals)} festivals")
        
        # Cultural contexts
        contexts = [
            # Values
            CulturalContext(
                culture='indian',
                category='value',
                name='Respect for Elders',
                description='Deep cultural value of respecting and seeking blessings from elders',
                related_concepts=['family', 'respect', 'tradition', 'wisdom', 'blessing'],
                sensitivity_level='neutral',
                age_appropriate='all',
                examples=['touching feet for blessings', 'addressing elders with respect'],
                storytelling_notes='Show characters respecting elders, seeking advice from grandparents',
            ),
            CulturalContext(
                culture='indian',
                category='value',
                name='Joint Family',
                description='Extended family living together, emphasizing family bonds',
                related_concepts=['family', 'togetherness', 'grandparents', 'cousins', 'unity'],
                sensitivity_level='neutral',
                age_appropriate='all',
                examples=['multiple generations in one house', 'cousins playing together'],
                storytelling_notes='Include grandparents, uncles, aunts as active characters',
            ),
            
            # Food
            CulturalContext(
                culture='indian',
                category='food',
                name='Ladoo',
                description='Sweet round ball, commonly given as prasad or celebration sweet',
                related_concepts=['sweet', 'celebration', 'festival', 'offering'],
                sensitivity_level='neutral',
                age_appropriate='all',
                examples=['given after prayer', 'distributed at celebrations'],
                storytelling_notes='Can be used as reward, celebration element, or special treat',
            ),
            
            # Customs
            CulturalContext(
                culture='indian',
                category='custom',
                name='Namaste',
                description='Traditional greeting with folded hands',
                related_concepts=['greeting', 'respect', 'tradition'],
                sensitivity_level='neutral',
                age_appropriate='all',
                examples=['greeting elders', 'respectful greeting'],
                storytelling_notes='Use as respectful greeting, especially for elders or teachers',
            ),
            CulturalContext(
                culture='indian',
                category='custom',
                name='Rangoli',
                description='Colorful floor art made with colored powder or flowers',
                related_concepts=['art', 'decoration', 'festival', 'creativity', 'welcome'],
                sensitivity_level='neutral',
                age_appropriate='all',
                examples=['at entrance', 'during festivals'],
                storytelling_notes='Can be used as art activity, festival preparation',
            ),
            
            # Symbols
            CulturalContext(
                culture='indian',
                category='symbol',
                name='Diya',
                description='Small oil lamp, symbol of light and knowledge',
                related_concepts=['light', 'knowledge', 'hope', 'spirituality'],
                sensitivity_level='neutral',
                age_appropriate='all',
                examples=['lit during prayers', 'Diwali decoration'],
                storytelling_notes='Symbol of hope, knowledge defeating ignorance',
            ),
        ]
        
        db.add_all(contexts)
        print(f"Added {len(contexts)} cultural contexts")
        
        # Cultural mappings (generic to Indian)
        mappings = [
            CulturalMapping(
                source_concept='Christmas',
                source_context='western',
                target_concept='Diwali',
                target_culture='indian',
                mapping_type='equivalent',
                confidence_score=0.8,
                explanation='Both are major festivals with lights, family gatherings, gifts, and sweets',
                usage_examples=[
                    {'before': 'decorating Christmas tree', 'after': 'making rangoli and decorating with diyas'},
                    {'before': 'Santa bringing gifts', 'after': 'elders giving gifts and blessings'}
                ],
                verified=True
            ),
            CulturalMapping(
                source_concept='birthday cake',
                source_context='generic',
                target_concept='ladoo or barfi',
                target_culture='indian',
                mapping_type='similar',
                confidence_score=0.7,
                explanation='Traditional Indian sweets often replace cakes in celebrations',
                usage_examples=[
                    {'before': 'cutting birthday cake', 'after': 'distributing ladoos to friends'}
                ],
                verified=True
            ),
            CulturalMapping(
                source_concept='handshake',
                source_context='western',
                target_concept='namaste',
                target_culture='indian',
                mapping_type='equivalent',
                confidence_score=0.9,
                explanation='Both are respectful greetings, namaste is traditional Indian way',
                usage_examples=[
                    {'before': 'shaking hands', 'after': 'folding hands and saying namaste'}
                ],
                verified=True
            ),
        ]
        
        db.add_all(mappings)
        print(f" Added {len(mappings)} cultural mappings")
        
        db.commit()
        print("\n Indian cultural data seeded successfully!\n")


def main():
    """Main initialization function"""
    print("\n" + "="*60)
    print("  Narrative Intelligence System - Database Initialization")
    print("="*60)
    
    # Initialize database
    print("\nInitializing database...")
    init_db()
    
    # Seed cultural data
    seed_indian_cultural_data()
    
    print("="*60)
    print(" Initialization complete!")
    print("="*60)
    print("\nYou can now:")
    print("  1. Run the demo: python scripts/test_offline_demo.py")
    print("  2. Start the API: python -m app.main")
    print("\n")


if __name__ == "__main__":
    main()