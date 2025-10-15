"""
Story Parser - NLP-based story analysis and understanding
"""

import spacy
from typing import List, Dict, Tuple, Optional
from collections import Counter
import re
from sqlalchemy.orm import Session

from app.models.story import Story, StoryConcept
from app.services.conceptnet import ConceptNetService
from app.core.config import settings
from app.core.exceptions import NLPModelNotLoadedException, StoryParsingException

# Load spaCy model
try:
    nlp = spacy.load(settings.SPACY_MODEL)
    print(f"✅ Loaded spaCy model: {settings.SPACY_MODEL}")
except:
    nlp = None
    print(f"⚠️  spaCy model '{settings.SPACY_MODEL}' not found.")
    print("Install with: python -m spacy download en_core_web_sm")


class StoryParser:
    """
    Analyze stories using NLP to extract:
    - Concepts (characters, objects, events)
    - Themes
    - Complexity metrics
    - Age appropriateness
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.conceptnet = ConceptNetService(db)
        
        if not nlp:
            raise NLPModelNotLoadedException("spaCy model not loaded")
        
        # Theme keywords for Indian context
        self.theme_keywords = {
            'bravery': ['brave', 'courage', 'hero', 'fearless', 'bold', 'daring'],
            'friendship': ['friend', 'companion', 'together', 'help', 'support', 'trust'],
            'family': ['mother', 'father', 'parent', 'family', 'home', 'brother', 'sister'],
            'honesty': ['truth', 'honest', 'lie', 'trust', 'promise'],
            'kindness': ['kind', 'gentle', 'compassion', 'care', 'generous', 'helpful'],
            'wisdom': ['wise', 'clever', 'smart', 'learn', 'knowledge', 'teach'],
            'perseverance': ['try', 'persist', 'determination', 'never give up', 'keep going'],
            'respect': ['respect', 'elder', 'guru', 'teacher', 'namaste'],
            'celebration': ['celebrate', 'festival', 'joy', 'happiness', 'diwali', 'holi'],
            'adventure': ['journey', 'explore', 'discover', 'travel', 'quest'],
            'nature': ['tree', 'forest', 'river', 'animal', 'bird', 'mountain'],
            'fear': ['scared', 'afraid', 'frightened', 'worry', 'nervous'],
        }
        
        # Concept type mapping
        self.entity_type_map = {
            'PERSON': 'character',
            'ORG': 'organization',
            'GPE': 'location',
            'LOC': 'location',
            'EVENT': 'event',
            'FAC': 'location',
            'PRODUCT': 'object',
            'WORK_OF_ART': 'object',
        }
    
    def parse_story(
        self, 
        story_text: str, 
        title: str,
        enrich_with_conceptnet: bool = True
    ) -> Dict:
        """
        Complete story analysis
        
        Returns:
            Comprehensive analysis including concepts, themes, complexity
        """
        if not story_text or len(story_text.strip()) < settings.MIN_STORY_LENGTH:
            raise StoryParsingException(
                f"Story too short. Minimum {settings.MIN_STORY_LENGTH} characters required."
            )
        
        try:
            doc = nlp(story_text)
            
            # Extract all components
            concepts = self._extract_concepts(doc)
            themes = self._identify_themes(story_text, doc)
            complexity = self._calculate_complexity(doc)
            entities = self._extract_entities(doc)
            
            # Enrich with ConceptNet if online and requested
            if enrich_with_conceptnet:
                concepts = self._enrich_concepts(concepts)
            
            analysis = {
                'title': title,
                'word_count': len([token for token in doc if not token.is_punct]),
                'sentence_count': len(list(doc.sents)),
                'concepts': concepts,
                'themes': themes,
                'complexity': complexity,
                'entities': entities,
                'age_recommendation': self._recommend_age_range(complexity),
                'indian_cultural_elements': self._detect_indian_elements(doc)
            }
            
            return analysis
            
        except Exception as e:
            raise StoryParsingException(
                f"Failed to parse story: {str(e)}",
                {'title': title, 'error': str(e)}
            )
    
    def _extract_concepts(self, doc) -> List[Dict]:
        """Extract key concepts using NER and noun chunks"""
        concepts = []
        seen = set()
        
        # Extract named entities
        for ent in doc.ents:
            if ent.text.lower() in seen:
                continue
            
            concept_type = self.entity_type_map.get(ent.label_, 'other')
            concepts.append({
                'text': ent.text,
                'type': concept_type,
                'label': ent.label_,
                'importance': self._calculate_importance(ent.text, doc)
            })
            seen.add(ent.text.lower())
        
        # Extract important noun chunks
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            if chunk_text in seen or len(chunk_text.split()) > 3:
                continue
            
            if chunk.root.pos_ == 'NOUN' and not chunk.root.is_stop:
                concepts.append({
                    'text': chunk.text,
                    'type': 'concept',
                    'label': 'NOUN_CHUNK',
                    'importance': self._calculate_importance(chunk.text, doc)
                })
                seen.add(chunk_text)
        
        # Sort by importance
        concepts.sort(key=lambda x: x['importance'], reverse=True)
        return concepts[:20]  # Top 20 concepts
    
    def _calculate_importance(self, text: str, doc) -> float:
        """Calculate importance score for a concept (0-1)"""
        text_lower = text.lower()
        
        # Count occurrences
        count = sum(1 for token in doc if text_lower in token.text.lower())
        
        # Normalize by document length
        doc_length = len([t for t in doc if not t.is_punct])
        frequency = count / max(doc_length, 1)
        
        # Boost if in title or first sentence
        boost = 0.0
        first_sent = list(doc.sents)[0].text.lower() if list(doc.sents) else ""
        if text_lower in first_sent:
            boost = 0.2
        
        importance = min(frequency * 10 + boost, 1.0)
        return round(importance, 3)
    
    def _identify_themes(self, text: str, doc) -> List[str]:
        """Identify themes using keyword matching"""
        text_lower = text.lower()
        theme_scores = {}
        
        for theme, keywords in self.theme_keywords.items():
            score = 0
            for keyword in keywords:
                # Count keyword occurrences
                count = len(re.findall(r'\b' + keyword + r'\b', text_lower))
                score += count
            
            if score > 0:
                theme_scores[theme] = score
        
        # Return themes sorted by score
        themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, score in themes if score >= 1][:5]  # Top 5 themes
    
    def _calculate_complexity(self, doc) -> Dict:
        """
        Calculate complexity metrics
        Returns complexity score (1-10) and detailed metrics
        """
        # Word count
        words = [token for token in doc if not token.is_punct and not token.is_space]
        word_count = len(words)
        
        # Sentence count and average length
        sentences = list(doc.sents)
        sent_count = len(sentences)
        avg_sent_length = word_count / max(sent_count, 1)
        
        # Vocabulary complexity (unique words / total words)
        unique_words = len(set(token.text.lower() for token in words if not token.is_stop))
        lexical_diversity = unique_words / max(word_count, 1)
        
        # Average word length
        avg_word_length = sum(len(token.text) for token in words) / max(word_count, 1)
        
        # Syllable estimation (rough)
        avg_syllables = self._estimate_syllables_per_word(words)
        
        # Flesch-Kincaid Grade Level (simplified)
        if sent_count > 0 and word_count > 0:
            fk_grade = (0.39 * avg_sent_length) + (11.8 * avg_syllables) - 15.59
            fk_grade = max(1, min(fk_grade, 12))  # Clamp between 1-12
        else:
            fk_grade = 5
        
        # Calculate overall complexity (1-10 scale)
        complexity_score = self._map_to_complexity_scale(
            fk_grade, avg_sent_length, lexical_diversity, avg_word_length
        )
        
        return {
            'score': complexity_score,
            'flesch_kincaid_grade': round(fk_grade, 1),
            'avg_sentence_length': round(avg_sent_length, 1),
            'lexical_diversity': round(lexical_diversity, 3),
            'avg_word_length': round(avg_word_length, 1),
            'total_words': word_count,
            'total_sentences': sent_count,
        }
    
    def _estimate_syllables_per_word(self, words) -> float:
        """Rough syllable estimation"""
        vowels = 'aeiou'
        syllable_count = 0
        
        for token in words:
            word = token.text.lower()
            word_syllables = 0
            previous_was_vowel = False
            
            for char in word:
                is_vowel = char in vowels
                if is_vowel and not previous_was_vowel:
                    word_syllables += 1
                previous_was_vowel = is_vowel
            
            # Adjust for silent e
            if word.endswith('e'):
                word_syllables -= 1
            
            syllable_count += max(1, word_syllables)
        
        return syllable_count / max(len(words), 1)
    
    def _map_to_complexity_scale(
        self, 
        fk_grade: float, 
        avg_sent_length: float,
        lexical_diversity: float,
        avg_word_length: float
    ) -> int:
        """Map metrics to 1-10 complexity scale"""
        # Weighted combination
        score = (
            (fk_grade / 12) * 0.4 +  # FK grade weight
            (min(avg_sent_length / 20, 1)) * 0.3 +  # Sentence length weight
            (lexical_diversity) * 0.2 +  # Diversity weight
            (min(avg_word_length / 10, 1)) * 0.1  # Word length weight
        )
        
        return max(1, min(10, int(score * 10)))
    
    def _recommend_age_range(self, complexity: Dict) -> str:
        """Recommend age range based on complexity"""
        score = complexity['score']
        
        if score <= 3:
            return '3-5'
        elif score <= 5:
            return '6-8'
        elif score <= 7:
            return '9-12'
        else:
            return '13+'
    
    def _extract_entities(self, doc) -> Dict[str, List[str]]:
        """Extract and categorize entities"""
        entities = {
            'characters': [],
            'locations': [],
            'objects': [],
            'events': [],
        }
        
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                entities['characters'].append(ent.text)
            elif ent.label_ in ['GPE', 'LOC', 'FAC']:
                entities['locations'].append(ent.text)
            elif ent.label_ in ['PRODUCT', 'WORK_OF_ART']:
                entities['objects'].append(ent.text)
            elif ent.label_ == 'EVENT':
                entities['events'].append(ent.text)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def _detect_indian_elements(self, doc) -> List[str]:
        """Detect Indian cultural elements in the story"""
        indian_markers = [
            'diwali', 'holi', 'diya', 'rangoli', 'namaste', 
            'ladoo', 'barfi', 'paneer', 'curry', 'naan',
            'sari', 'kurta', 'dhoti',
            'ram', 'krishna', 'ganesh', 'lakshmi',
            'guru', 'ashram', 'temple', 'mandir',
            'hindi', 'sanskrit', 'tamil', 'bengali'
        ]
        
        text_lower = doc.text.lower()
        found_elements = []
        
        for marker in indian_markers:
            if marker in text_lower:
                found_elements.append(marker)
        
        return found_elements
    
    def _enrich_concepts(self, concepts: List[Dict]) -> List[Dict]:
        """Enrich concepts with ConceptNet data"""
        enriched = []
        
        for concept in concepts:
            try:
                # Get ConceptNet relations for top concepts
                if concept['importance'] >= 0.3:
                    relations = self.conceptnet.get_concept_relations(
                        concept['text'].lower()
                    )
                    if relations:
                        concept['conceptnet_relations'] = relations
            except:
                pass  # Continue even if enrichment fails
            
            enriched.append(concept)
        
        return enriched
    
    def save_story_analysis(self, story_id: int, analysis: Dict):
        """Save parsed concepts to database"""
        try:
            # Get story
            story = self.db.query(Story).filter(Story.id == story_id).first()
            if not story:
                raise StoryParsingException(f"Story with id {story_id} not found")
            
            # Delete existing concepts
            self.db.query(StoryConcept).filter(
                StoryConcept.story_id == story_id
            ).delete()
            
            # Add new concepts
            for concept_data in analysis['concepts'][:15]:  # Top 15
                concept = StoryConcept(
                    story_id=story_id,
                    concept=concept_data['text'],
                    concept_type=concept_data['type'],
                    importance_score=concept_data['importance'],
                    conceptnet_relations=concept_data.get('conceptnet_relations')
                )
                self.db.add(concept)
            
            # Update story metadata
            story.themes = analysis['themes']
            story.complexity_level = analysis['complexity']['score']
            story.age_range = analysis['age_recommendation']
            story.word_count = analysis['word_count']
            story.sentence_count = analysis['sentence_count']
            
            self.db.commit()
            print(f"✅ Saved analysis for story: {story.title}")
            
        except Exception as e:
            self.db.rollback()
            raise StoryParsingException(
                f"Failed to save story analysis: {str(e)}",
                {'story_id': story_id}
            )


# Factory function
def get_story_parser(db: Session) -> StoryParser:
    """Get story parser instance"""
    return StoryParser(db)