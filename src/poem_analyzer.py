"""
Poem Analyzer Module

This module provides functionality to analyze poems and extract features
for recommendation purposes.
"""

import re
import nltk
from textstat import flesch_reading_ease, flesch_kincaid_grade
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

class PoemAnalyzer:
    """Analyzes poems and extracts features for recommendation."""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def analyze_poem(self, poem_text, title="", author=""):
        """
        Analyze a poem and extract various features.
        
        Args:
            poem_text (str): The text of the poem
            title (str): Title of the poem
            author (str): Author of the poem
            
        Returns:
            dict: Dictionary containing analysis results
        """
        # Basic text statistics
        lines = poem_text.strip().split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        analysis = {
            'title': title,
            'author': author,
            'text': poem_text,
            'line_count': len(non_empty_lines),
            'word_count': len(poem_text.split()),
            'char_count': len(poem_text),
            'avg_line_length': np.mean([len(line) for line in non_empty_lines]) if non_empty_lines else 0,
            'readability_score': flesch_reading_ease(poem_text),
            'grade_level': flesch_kincaid_grade(poem_text),
        }
        
        # Extract themes and emotions
        analysis.update(self._extract_themes(poem_text))
        analysis.update(self._extract_rhythm_patterns(poem_text))
        analysis.update(self._extract_literary_devices(poem_text))
        
        return analysis
    
    def _extract_themes(self, text):
        """Extract thematic elements from the poem."""
        # Common poetic themes
        themes = {
            'nature': ['nature', 'tree', 'flower', 'sky', 'mountain', 'river', 'ocean', 'wind', 'rain', 'sun', 'moon', 'star'],
            'love': ['love', 'heart', 'kiss', 'embrace', 'passion', 'romance', 'beloved', 'sweet', 'dear'],
            'death': ['death', 'die', 'grave', 'tomb', 'eternal', 'soul', 'spirit', 'heaven', 'hell'],
            'time': ['time', 'moment', 'hour', 'day', 'night', 'year', 'past', 'future', 'eternity'],
            'sadness': ['sad', 'tear', 'cry', 'pain', 'sorrow', 'grief', 'lonely', 'empty', 'dark'],
            'joy': ['happy', 'joy', 'smile', 'laugh', 'bright', 'light', 'cheer', 'celebrate', 'dance']
        }
        
        text_lower = text.lower()
        theme_scores = {}
        
        for theme, keywords in themes.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            theme_scores[f'theme_{theme}'] = score
        
        return theme_scores
    
    def _extract_rhythm_patterns(self, text):
        """Extract rhythm and meter patterns."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Count syllables (simplified)
        syllable_counts = []
        for line in lines:
            words = line.split()
            syllables = sum(self._count_syllables(word) for word in words)
            syllable_counts.append(syllables)
        
        return {
            'avg_syllables_per_line': np.mean(syllable_counts) if syllable_counts else 0,
            'syllable_variance': np.var(syllable_counts) if syllable_counts else 0,
            'rhythm_consistency': 1 - (np.var(syllable_counts) / (np.mean(syllable_counts) + 1e-6)) if syllable_counts else 0
        }
    
    def _count_syllables(self, word):
        """Simple syllable counter."""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
            
        return max(1, syllable_count)
    
    def _extract_literary_devices(self, text):
        """Extract common literary devices."""
        text_lower = text.lower()
        
        # Alliteration (consecutive words starting with same letter)
        words = word_tokenize(text_lower)
        alliteration_count = 0
        for i in range(len(words) - 1):
            if words[i][0].isalpha() and words[i+1][0].isalpha():
                if words[i][0] == words[i+1][0]:
                    alliteration_count += 1
        
        # Repetition (repeated words)
        word_counts = Counter(words)
        repetition_count = sum(1 for count in word_counts.values() if count > 1)
        
        # Rhyme detection (simplified - last words of lines)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        rhyme_pairs = 0
        for i in range(len(lines) - 1):
            last_word1 = lines[i].split()[-1].lower() if lines[i].split() else ""
            last_word2 = lines[i+1].split()[-1].lower() if lines[i+1].split() else ""
            if self._words_rhyme(last_word1, last_word2):
                rhyme_pairs += 1
        
        return {
            'alliteration_count': alliteration_count,
            'repetition_count': repetition_count,
            'rhyme_pairs': rhyme_pairs,
            'literary_density': (alliteration_count + repetition_count + rhyme_pairs) / max(len(words), 1)
        }
    
    def _words_rhyme(self, word1, word2):
        """Simple rhyme detection based on ending sounds."""
        if len(word1) < 2 or len(word2) < 2:
            return False
        
        # Remove common suffixes
        suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion']
        for suffix in suffixes:
            if word1.endswith(suffix):
                word1 = word1[:-len(suffix)]
            if word2.endswith(suffix):
                word2 = word2[:-len(suffix)]
        
        # Check if last 2-3 characters match
        return word1[-2:] == word2[-2:] or word1[-3:] == word2[-3:]
    
    def create_feature_vector(self, analysis):
        """Create a numerical feature vector from analysis."""
        features = [
            analysis['line_count'],
            analysis['word_count'],
            analysis['char_count'],
            analysis['avg_line_length'],
            analysis['readability_score'],
            analysis['grade_level'],
            analysis['avg_syllables_per_line'],
            analysis['syllable_variance'],
            analysis['rhythm_consistency'],
            analysis['alliteration_count'],
            analysis['repetition_count'],
            analysis['rhyme_pairs'],
            analysis['literary_density'],
        ]
        
        # Add theme scores
        theme_keys = [key for key in analysis.keys() if key.startswith('theme_')]
        for theme_key in sorted(theme_keys):
            features.append(analysis[theme_key])
        
        return np.array(features)
    
    def calculate_similarity(self, poem1_features, poem2_features):
        """Calculate similarity between two poems based on features."""
        # Normalize features
        poem1_norm = poem1_features / (np.linalg.norm(poem1_features) + 1e-6)
        poem2_norm = poem2_features / (np.linalg.norm(poem2_features) + 1e-6)
        
        # Calculate cosine similarity
        similarity = np.dot(poem1_norm, poem2_norm)
        return similarity
