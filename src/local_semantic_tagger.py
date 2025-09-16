"""
Local Semantic Tagger for Poems

Uses spaCy and custom rules to extract semantic tags without API calls.
"""

import re
from typing import List, Dict, Any
import spacy
from collections import Counter

class LocalSemanticTagger:
    """Analyzes poems and extracts semantic tags using local NLP."""
    
    def __init__(self):
        # Load spaCy model (you'll need to install: python -m spacy download en_core_web_sm)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("⚠️  spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Define semantic patterns
        self.theme_patterns = {
            'love': [
                r'\b(love|heart|beloved|romance|passion|affection|devotion|adore|cherish)\b',
                r'\b(kiss|embrace|touch|caress|intimacy|desire|longing)\b'
            ],
            'nature': [
                r'\b(tree|forest|mountain|river|ocean|sea|sky|star|moon|sun|wind|rain|snow)\b',
                r'\b(flower|bird|animal|wild|natural|earth|garden|field|meadow)\b'
            ],
            'death': [
                r'\b(death|die|dying|grave|burial|funeral|mourn|grief|loss|end|final)\b',
                r'\b(ghost|spirit|soul|heaven|hell|afterlife|eternal|immortal)\b'
            ],
            'time': [
                r'\b(time|moment|hour|day|night|year|age|old|young|past|future|now)\b',
                r'\b(clock|watch|season|spring|summer|autumn|winter|dawn|dusk)\b'
            ],
            'beauty': [
                r'\b(beautiful|beauty|gorgeous|lovely|stunning|magnificent|splendid)\b',
                r'\b(grace|elegance|charm|radiant|brilliant|glorious|divine)\b'
            ],
            'sadness': [
                r'\b(sad|sorrow|tears|cry|weep|mourn|grief|pain|hurt|ache|suffer)\b',
                r'\b(depression|melancholy|despair|hopeless|lonely|empty|broken)\b'
            ],
            'joy': [
                r'\b(joy|happy|happiness|smile|laugh|celebrate|cheer|delight|bliss)\b',
                r'\b(merry|jolly|bright|sunny|cheerful|upbeat|positive|optimistic)\b'
            ],
            'hope': [
                r'\b(hope|hopeful|dream|wish|aspire|believe|faith|trust|confidence)\b',
                r'\b(light|dawn|new|fresh|renew|rebirth|resurrection|salvation)\b'
            ],
            'war': [
                r'\b(war|battle|fight|soldier|army|weapon|sword|gun|bomb|conflict)\b',
                r'\b(victory|defeat|enemy|foe|attack|defend|hero|courage|brave)\b'
            ],
            'peace': [
                r'\b(peace|calm|quiet|serene|tranquil|still|silent|gentle|soft)\b',
                r'\b(harmony|balance|unity|together|brotherhood|sisterhood|community)\b'
            ],
            'family': [
                r'\b(father|mother|parent|child|son|daughter|brother|sister|family)\b',
                r'\b(grandfather|grandmother|uncle|aunt|cousin|relative|ancestor)\b'
            ],
            'home': [
                r'\b(home|house|door|window|room|kitchen|bedroom|hearth|fireplace)\b',
                r'\b(roof|wall|floor|ceiling|garden|yard|fence|gate|threshold)\b'
            ],
            'journey': [
                r'\b(journey|travel|road|path|way|walk|run|move|go|come|depart)\b',
                r'\b(adventure|explore|discover|seek|find|search|quest|mission)\b'
            ],
            'memory': [
                r'\b(memory|remember|forget|recall|nostalgia|past|yesterday|childhood)\b',
                r'\b(dream|nightmare|vision|imagination|fantasy|reality|truth)\b'
            ],
            'spiritual': [
                r'\b(god|divine|holy|sacred|prayer|faith|soul|spirit|angel|heaven)\b',
                r'\b(meditation|contemplation|wisdom|enlightenment|transcendence)\b'
            ]
        }
        
        # Emotional intensity words
        self.intensity_words = {
            'intense': ['fierce', 'wild', 'passionate', 'burning', 'raging', 'storm', 'thunder'],
            'gentle': ['soft', 'gentle', 'tender', 'mild', 'calm', 'quiet', 'whisper'],
            'contemplative': ['think', 'ponder', 'reflect', 'consider', 'meditate', 'wonder']
        }
    
    def analyze_poem(self, poem_text: str, title: str = "", author: str = "") -> List[str]:
        """
        Analyze a poem and extract semantic tags using local NLP.
        
        Args:
            poem_text (str): The poem text
            title (str): Poem title
            author (str): Poem author
            
        Returns:
            List[str]: List of semantic tags
        """
        if not poem_text or len(poem_text.strip()) < 10:
            return []
        
        if not self.nlp:
            return self._fallback_analysis(poem_text)
        
        # Combine title, author, and text for analysis
        full_text = f"{title} {author} {poem_text}".lower()
        
        # Process with spaCy
        doc = self.nlp(full_text)
        
        # Extract tags using pattern matching
        tags = set()
        
        # Check theme patterns
        for theme, patterns in self.theme_patterns.items():
            for pattern in patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    tags.add(theme)
        
        # Check emotional intensity
        for intensity, words in self.intensity_words.items():
            if any(word in full_text for word in words):
                tags.add(intensity)
        
        # Extract key nouns and adjectives for additional themes
        nouns = [token.lemma_ for token in doc if token.pos_ == "NOUN" and len(token.text) > 3]
        adjectives = [token.lemma_ for token in doc if token.pos_ == "ADJ" and len(token.text) > 3]
        
        # Count most common words
        word_counts = Counter(nouns + adjectives)
        common_words = [word for word, count in word_counts.most_common(5) if count > 1]
        
        # Add common words as tags if they're meaningful
        for word in common_words:
            if len(word) > 4 and word not in ['poem', 'poetry', 'verse', 'line', 'word']:
                tags.add(word)
        
        # Only return tags if we found meaningful ones
        if not tags:
            return []
        
        return list(tags)[:10]  # Limit to 10 tags
    
    def _fallback_analysis(self, text: str) -> List[str]:
        """Fallback analysis when spaCy is not available."""
        text_lower = text.lower()
        tags = set()
        
        # Simple keyword matching
        if any(word in text_lower for word in ['love', 'heart', 'beloved']):
            tags.add('love')
        if any(word in text_lower for word in ['nature', 'tree', 'flower', 'bird']):
            tags.add('nature')
        if any(word in text_lower for word in ['death', 'die', 'grave']):
            tags.add('death')
        if any(word in text_lower for word in ['time', 'moment', 'hour']):
            tags.add('time')
        if any(word in text_lower for word in ['beautiful', 'beauty', 'lovely']):
            tags.add('beauty')
        
        return list(tags) if tags else []
    
    def get_search_tags(self, query: str) -> List[str]:
        """
        Convert a search query into semantic tags for searching.
        
        Args:
            query (str): Search query
            
        Returns:
            List[str]: List of semantic tags to search for
        """
        if not self.nlp:
            return [query.lower()]
        
        # Process query with spaCy
        doc = self.nlp(query.lower())
        
        # Extract key terms
        tags = set()
        
        # Check if query matches any theme patterns
        for theme, patterns in self.theme_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    tags.add(theme)
        
        # Extract nouns and adjectives from query
        query_terms = [token.lemma_ for token in doc if token.pos_ in ["NOUN", "ADJ"] and len(token.text) > 2]
        tags.update(query_terms)
        
        # Add synonyms and related terms for better search coverage
        synonyms = self._get_synonyms(query.lower())
        tags.update(synonyms)
        
        # If no tags found, use the original query
        if not tags:
            tags = [query.lower()]
        
        return list(tags)[:10]  # Increased limit to 10 search tags
    
    def _get_synonyms(self, word: str) -> List[str]:
        """Get synonyms and related terms for a word."""
        synonyms = {
            'struggle': ['struggle', 'fight', 'battle', 'conflict', 'challenge', 'difficulty', 'hardship', 'trial', 'effort', 'strive'],
            'love': ['love', 'affection', 'passion', 'romance', 'devotion', 'adoration', 'cherish', 'beloved', 'heart'],
            'death': ['death', 'dying', 'mortality', 'end', 'passing', 'loss', 'grave', 'funeral', 'mourning'],
            'hope': ['hope', 'optimism', 'faith', 'belief', 'expectation', 'aspiration', 'dream', 'wish'],
            'beauty': ['beauty', 'beautiful', 'lovely', 'gorgeous', 'stunning', 'magnificent', 'splendid', 'grace'],
            'sadness': ['sadness', 'sorrow', 'grief', 'melancholy', 'depression', 'despair', 'tears', 'mourning'],
            'joy': ['joy', 'happiness', 'bliss', 'delight', 'cheer', 'celebration', 'smile', 'laugh'],
            'fear': ['fear', 'afraid', 'terror', 'anxiety', 'worry', 'dread', 'panic', 'fright'],
            'anger': ['anger', 'rage', 'fury', 'wrath', 'irritation', 'annoyance', 'hostility', 'resentment'],
            'peace': ['peace', 'calm', 'serenity', 'tranquility', 'harmony', 'stillness', 'quiet', 'composure'],
            'time': ['time', 'moment', 'hour', 'day', 'age', 'past', 'future', 'present', 'eternity'],
            'nature': ['nature', 'natural', 'wild', 'earth', 'forest', 'mountain', 'ocean', 'sky', 'tree'],
            'family': ['family', 'parent', 'child', 'mother', 'father', 'sister', 'brother', 'relative', 'kin'],
            'home': ['home', 'house', 'dwelling', 'abode', 'residence', 'shelter', 'place', 'belonging'],
            'journey': ['journey', 'travel', 'trip', 'voyage', 'path', 'road', 'way', 'adventure', 'quest'],
            'dream': ['dream', 'vision', 'fantasy', 'imagination', 'aspiration', 'goal', 'wish', 'desire'],
            'memory': ['memory', 'remember', 'recollection', 'reminiscence', 'nostalgia', 'past', 'recall'],
            'freedom': ['freedom', 'liberty', 'independence', 'autonomy', 'liberation', 'release', 'escape'],
            'truth': ['truth', 'reality', 'fact', 'honesty', 'sincerity', 'authenticity', 'genuine', 'real'],
            'wisdom': ['wisdom', 'knowledge', 'understanding', 'insight', 'intelligence', 'learning', 'enlightenment'],
            'courage': ['courage', 'bravery', 'valor', 'fearlessness', 'boldness', 'strength', 'heroism']
        }
        
        return synonyms.get(word, [word])
