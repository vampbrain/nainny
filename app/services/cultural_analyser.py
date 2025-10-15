"""
Cultural Analyzer - Detect and analyze Indian cultural elements in stories
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from collections import Counter

from app.models.cultural import CulturalContext, CulturalMapping, IndianFestival
from app.services.conceptnet import ConceptNetService
from app.core.exceptions import CulturalContextNotFoundException


class CulturalAnalyzer:
    """
    Analyze stories for Indian cultural elements
    Detect cultural markers, suggest adaptations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.conceptnet = ConceptNetService(db)
        
        # Load cultural data
        self._load_cultural_data()
    
    def _load_cultural_data(self):
        """Load cultural contexts and mappings from database"""
        self.cultural_contexts = self.db.query(CulturalContext).filter(
            CulturalContext.culture == 'indian'
        ).all()
        
        self.festivals = self.db.query(IndianFestival).all()
        
        self.mappings = self.db.query(CulturalMapping).filter(
            CulturalMapping.target_culture == 'indian'
        ).all()
        
        # Create lookup dictionaries
        self.context_by_name = {
            ctx.name.lower(): ctx for ctx in self.cultural_contexts
        }
        
        self.festival_by_name = {
            fest.name.lower(): fest for fest in self.festivals
        }
        
        print(f"Loaded {len(self.cultural_contexts)} cultural contexts")
        print(f"Loaded {len(self.festivals)} festivals")
        print(f"Loaded {len(self.mappings)} cultural mappings")
    
    def detect_cultural_markers(
        self, 
        text: str, 
        concepts: List[Dict] = None
    ) -> List[Dict]:
        """
        Detect Indian cultural elements in text
        
        Returns:
            List of detected cultural markers with context
        """
        text_lower = text.lower()
        markers = []
        
        # Check festivals
        for festival in self.festivals:
            if festival.name.lower() in text_lower:
                markers.append({
                    'type': 'festival',
                    'name': festival.name,
                    'category': 'festival',
                    'significance': festival.significance,
                    'child_explanation': festival.child_friendly_explanation,
                    'confidence': 1.0
                })
            
            # Check regional names
            for regional_name in festival.regional_names or []:
                if regional_name.lower() in text_lower:
                    markers.append({
                        'type': 'festival',
                        'name': festival.name,
                        'regional_variant': regional_name,
                        'category': 'festival',
                        'confidence': 0.9
                    })
        
        # Check cultural contexts
        for context in self.cultural_contexts:
            if context.name.lower() in text_lower:
                markers.append({
                    'type': 'cultural_element',
                    'name': context.name,
                    'category': context.category,
                    'description': context.description,
                    'sensitivity': context.sensitivity_level,
                    'confidence': 1.0
                })
            
            # Check related concepts
            for related in context.related_concepts or []:
                if related.lower() in text_lower:
                    markers.append({
                        'type': 'cultural_element',
                        'name': context.name,
                        'matched_via': related,
                        'category': context.category,
                        'confidence': 0.7
                    })
        
        # Check concepts if provided
        if concepts:
            for concept in concepts:
                concept_lower = concept['text'].lower()
                if concept_lower in self.context_by_name:
                    ctx = self.context_by_name[concept_lower]
                    markers.append({
                        'type': 'concept_match',
                        'name': ctx.name,
                        'category': ctx.category,
                        'importance': concept.get('importance', 0.5),
                        'confidence': 0.8
                    })
        
        # Remove duplicates
        markers = self._deduplicate_markers(markers)
        
        return markers
    
    def _deduplicate_markers(self, markers: List[Dict]) -> List[Dict]:
        """Remove duplicate markers"""
        seen = set()
        unique_markers = []
        
        for marker in markers:
            key = (marker['name'], marker['category'])
            if key not in seen:
                seen.add(key)
                unique_markers.append(marker)
        
        return unique_markers
    
    def analyze_cultural_fit(
        self, 
        story_text: str,
        story_concepts: List[Dict],
        target_age: str = None
    ) -> Dict:
        """
        Analyze how well story fits Indian cultural context
        
        Returns:
            Analysis with score, strengths, issues, suggestions
        """
        markers = self.detect_cultural_markers(story_text, story_concepts)
        
        # Calculate fit score
        score = self._calculate_cultural_fit_score(markers, story_text)
        
        # Identify strengths
        strengths = self._identify_cultural_strengths(markers)
        
        # Identify potential issues
        issues = self._identify_cultural_issues(markers, target_age)
        
        # Generate suggestions
        suggestions = self._generate_adaptation_suggestions(
            story_text, markers, issues
        )
        
        return {
            'score': score,
            'markers_found': len(markers),
            'markers': markers,
            'strengths': strengths,
            'issues': issues,
            'suggestions': suggestions,
            'overall_assessment': self._get_assessment_text(score)
        }
    
    def _calculate_cultural_fit_score(
        self, 
        markers: List[Dict], 
        text: str
    ) -> float:
        """Calculate cultural fit score (0-1)"""
        if not markers:
            return 0.5  # Neutral if no markers
        
        # Score based on number and confidence of markers
        total_confidence = sum(m.get('confidence', 0.5) for m in markers)
        marker_score = min(total_confidence / 5, 1.0)  # Normalize to 0-1
        
        return round(marker_score, 2)
    
    def _identify_cultural_strengths(self, markers: List[Dict]) -> List[str]:
        """Identify cultural strengths in the story"""
        strengths = []
        
        # Count by category
        categories = Counter(m['category'] for m in markers)
        
        if 'festival' in categories:
            strengths.append(
                f"Story includes {categories['festival']} Indian festival(s)"
            )
        
        if 'value' in categories:
            strengths.append(
                f"Story embodies {categories['value']} Indian cultural value(s)"
            )
        
        if 'food' in categories:
            strengths.append("Story references Indian cuisine and food culture")
        
        if 'custom' in categories:
            strengths.append("Story demonstrates Indian customs and traditions")
        
        return strengths
    
    def _identify_cultural_issues(
        self, 
        markers: List[Dict],
        target_age: str
    ) -> List[Dict]:
        """Identify potential cultural issues"""
        issues = []
        
        # Check sensitivity levels
        for marker in markers:
            if marker.get('sensitivity') == 'caution':
                issues.append({
                    'type': 'sensitivity',
                    'element': marker['name'],
                    'reason': 'This element requires careful handling',
                    'severity': 'medium'
                })
            elif marker.get('sensitivity') == 'avoid':
                issues.append({
                    'type': 'sensitivity',
                    'element': marker['name'],
                    'reason': 'This element should be avoided or recontextualized',
                    'severity': 'high'
                })
        
        # Check age appropriateness
        if target_age:
            for marker in markers:
                marker_age = marker.get('age_appropriate', 'all')
                if marker_age != 'all' and not self._is_age_appropriate(
                    marker_age, target_age
                ):
                    issues.append({
                        'type': 'age_inappropriate',
                        'element': marker['name'],
                        'reason': f'Not suitable for age group {target_age}',
                        'severity': 'high'
                    })
        
        return issues
    
    def _is_age_appropriate(self, marker_age: str, target_age: str) -> bool:
        """Check if marker is appropriate for target age"""
        age_order = ['3-5', '6-8', '9-12', '13+']
        try:
            marker_idx = age_order.index(marker_age)
            target_idx = age_order.index(target_age)
            return target_idx >= marker_idx
        except:
            return True
    
    def _generate_adaptation_suggestions(
        self,
        text: str,
        markers: List[Dict],
        issues: List[Dict]
    ) -> List[Dict]:
        """Generate suggestions for cultural adaptation"""
        suggestions = []
        
        # If no cultural markers, suggest adding some
        if len(markers) < 2:
            suggestions.append({
                'type': 'add_cultural_elements',
                'priority': 'high',
                'suggestion': 'Add more Indian cultural elements to increase relevance',
                'examples': [
                    'Include an Indian festival as backdrop',
                    'Add Indian food references',
                    'Use Indian names for characters'
                ]
            })
        
        # Address each issue
        for issue in issues:
            if issue['severity'] == 'high':
                suggestions.append({
                    'type': 'fix_issue',
                    'priority': 'high',
                    'element': issue['element'],
                    'suggestion': f"Address: {issue['reason']}",
                    'action': 'modify or remove'
                })
        
        # Suggest enhancements
        if 'festival' not in [m['category'] for m in markers]:
            suggestions.append({
                'type': 'enhancement',
                'priority': 'medium',
                'suggestion': 'Consider setting story during an Indian festival',
                'examples': ['Diwali', 'Holi']
            })
        
        return suggestions
    
    def _get_assessment_text(self, score: float) -> str:
        """Get overall assessment text"""
        if score >= 0.8:
            return "Excellent cultural fit with strong Indian context"
        elif score >= 0.6:
            return "Good cultural fit with some Indian elements"
        elif score >= 0.4:
            return "Moderate cultural relevance, could be enhanced"
        elif score >= 0.2:
            return "Limited cultural context, significant adaptation needed"
        else:
            return "Minimal Indian cultural context"
    
    def find_concept_mapping(
        self,
        source_concept: str,
        source_context: str = 'generic'
    ) -> Optional[Dict]:
        """
        Find Indian equivalent for a concept
        
        Args:
            source_concept: Concept to map (e.g., 'Christmas')
            source_context: Context of concept (e.g., 'western', 'generic')
            
        Returns:
            Mapping information or None
        """
        # Check database mappings first
        mapping = self.db.query(CulturalMapping).filter(
            CulturalMapping.source_concept.ilike(f"%{source_concept}%"),
            CulturalMapping.target_culture == 'indian'
        ).first()
        
        if mapping:
            return {
                'source': mapping.source_concept,
                'target': mapping.target_concept,
                'type': mapping.mapping_type,
                'confidence': mapping.confidence_score,
                'explanation': mapping.explanation,
                'examples': mapping.usage_examples,
                'verified': mapping.verified
            }
        
        # Try ConceptNet-based mapping
        try:
            indian_equivalents = self.conceptnet.find_indian_equivalents(source_concept)
            if indian_equivalents:
                return {
                    'source': source_concept,
                    'target': indian_equivalents[0],
                    'type': 'conceptnet_suggested',
                    'confidence': 0.5,
                    'explanation': 'Suggested via ConceptNet semantic relations',
                    'alternatives': indian_equivalents[1:],
                    'verified': False
                }
        except:
            pass
        
        return None
    
    def get_festival_context(self, festival_name: str) -> Optional[Dict]:
        """Get detailed context about an Indian festival"""
        festival = self.db.query(IndianFestival).filter(
            IndianFestival.name.ilike(f"%{festival_name}%")
        ).first()
        
        if not festival:
            return None
        
        return {
            'name': festival.name,
            'regional_names': festival.regional_names,
            'month': festival.month,
            'season': festival.season,
            'significance': festival.significance,
            'story_elements': festival.story_elements,
            'activities': festival.common_activities,
            'foods': festival.traditional_foods,
            'decorations': festival.decorations,
            'child_explanation': festival.child_friendly_explanation,
            'story_hooks': festival.story_hooks,
            'age_appropriate': festival.age_appropriate
        }
    
    def suggest_indian_alternatives(
        self,
        concepts: List[str]
    ) -> Dict[str, List[str]]:
        """
        Suggest Indian alternatives for generic concepts
        
        Args:
            concepts: List of concepts to find alternatives for
            
        Returns:
            Dictionary mapping concepts to Indian alternatives
        """
        alternatives = {}
        
        for concept in concepts:
            mapping = self.find_concept_mapping(concept)
            if mapping:
                alternatives[concept] = {
                    'primary': mapping['target'],
                    'alternatives': mapping.get('alternatives', []),
                    'explanation': mapping['explanation']
                }
            else:
                # Try to find similar concepts in our database
                similar = self._find_similar_cultural_concepts(concept)
                if similar:
                    alternatives[concept] = {
                        'primary': similar[0],
                        'alternatives': similar[1:],
                        'explanation': 'Similar concepts from Indian culture'
                    }
        
        return alternatives
    
    def _find_similar_cultural_concepts(self, concept: str) -> List[str]:
        """Find similar concepts in Indian cultural database"""
        # Search in cultural contexts
        results = self.db.query(CulturalContext).filter(
            CulturalContext.culture == 'indian'
        ).all()
        
        similar = []
        concept_lower = concept.lower()
        
        for ctx in results:
            # Check if concept matches related_concepts
            if ctx.related_concepts:
                for related in ctx.related_concepts:
                    if concept_lower in related.lower() or related.lower() in concept_lower:
                        similar.append(ctx.name)
                        break
        
        return similar[:5]


# Factory function
def get_cultural_analyzer(db: Session) -> CulturalAnalyzer:
    """Get cultural analyzer instance"""
    return CulturalAnalyzer(db)