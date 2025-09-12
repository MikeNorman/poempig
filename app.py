"""
Flask Web Application for Poem Recommender
"""

from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from src.recommendation_engine import PoemRecommendationEngine
from src.vibe_profile_manager import VibeProfileManager                                                      

# Load environment variables
load_dotenv()

app = Flask(__name__)


# Initialize recommendation engine
try:
    engine = PoemRecommendationEngine()
    print("✅ Recommendation engine initialized successfully")                                                      
except Exception as e:
    print(f"❌ Error initializing recommendation engine: {e}")                                                      
    engine = None

# Initialize vibe profile manager
try:
    vibe_manager = VibeProfileManager()
    print("✅ Vibe profile manager initialized successfully")
except Exception as e:
    print(f"❌ Error initializing vibe profile manager: {e}")
    vibe_manager = None

@app.route('/')
def index():
    """Main page with search interface."""
    return render_template('index.html')

@app.route('/find_similar.html')
def find_similar_page():
    """Find similar poems page."""
    return render_template('find_similar.html')

@app.route('/vibes')
def vibes_page():
    """Vibes index page."""
    return render_template('vibes.html')

@app.route('/search', methods=['POST'])
def search():
    """Search for poems based on query."""
    if not engine:
        return jsonify({'error': 'Recommendation engine not available'}), 500                                       
    
    try:
        data = request.get_json()
        query = data.get('query', '')
        top_k = int(data.get('top_k', 5))
        offset = int(data.get('offset', 0))
        
        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'}), 400                                                 
        
        # Search for similar poems
        results = engine.search_poems(query, top_k + offset)
        
        # Apply offset for pagination
        if offset > 0:
            results = results[offset:]
        
        # Limit to requested top_k
        results = results[:top_k]
        
        return jsonify({
            'query': query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommend/theme', methods=['POST'])
def recommend_by_theme():
    """Recommend poems by theme."""
    if not engine:
        return jsonify({'error': 'Recommendation engine not available'}), 500
    
    try:
        data = request.get_json()
        theme = data.get('theme', '')
        top_k = int(data.get('top_k', 5))
        
        if not theme.strip():
            return jsonify({'error': 'Theme cannot be empty'}), 400
        
        results = engine.recommend_by_theme(theme, top_k)
        
        return jsonify({
            'theme': theme,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommend/mood', methods=['POST'])
def recommend_by_mood():
    """Recommend poems by mood."""
    if not engine:
        return jsonify({'error': 'Recommendation engine not available'}), 500
    
    try:
        data = request.get_json()
        mood = data.get('mood', '')
        top_k = int(data.get('top_k', 5))
        
        if not mood.strip():
            return jsonify({'error': 'Mood cannot be empty'}), 400
        
        results = engine.recommend_by_mood(mood, top_k)
        
        return jsonify({
            'mood': mood,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommend/author', methods=['POST'])
def recommend_by_author():
    """Recommend poems by author."""
    if not engine:
        return jsonify({'error': 'Recommendation engine not available'}), 500
    
    try:
        data = request.get_json()
        author = data.get('author', '')
        top_k = int(data.get('top_k', 5))
        
        if not author.strip():
            return jsonify({'error': 'Author cannot be empty'}), 400
        
        results = engine.recommend_by_author(author, top_k)
        
        return jsonify({
            'author': author,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/poem/<poem_id>')
def get_poem(poem_id):
    """Get a specific poem by ID."""
    if not engine:
        return jsonify({'error': 'Recommendation engine not available'}), 500
    
    try:
        poem = engine.get_poem_by_id(poem_id)
        if poem:
            return jsonify(poem)
        else:
            return jsonify({'error': 'Poem not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/find-similar', methods=['POST'])
def find_similar():
    """Find similar poems based on a specific poem ID."""
    if not engine:
        return jsonify({'error': 'Recommendation engine not available'}), 500
    
    try:
        data = request.get_json()
        poem_id = data.get('poem_id', '')
        top_k = int(data.get('top_k', 5))
        exclude_poem_ids = data.get('exclude_poem_ids', [])  # New parameter for exclusion
        
        if not poem_id.strip():
            return jsonify({'error': 'Poem ID cannot be empty'}), 400
        
        results = engine.find_similar_by_poem_id(poem_id, top_k, exclude_poem_ids)
        
        return jsonify({
            'poem_id': poem_id,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create-vibe-profile', methods=['POST'])
def create_vibe_profile():
    """Create a new vibe profile."""
    if not vibe_manager:
        return jsonify({'error': 'Vibe profile manager not available'}), 500
    
    try:
        data = request.get_json()
        name = data.get('name', 'Untitled Vibe Profile')
        poem_ids = data.get('poem_ids', [])
        
        vibe_profile_id = vibe_manager.create_vibe_profile(name, poem_ids)
        
        if vibe_profile_id:
            return jsonify({
                'vibe_profile_id': vibe_profile_id,
                'name': name
            })
        else:
            return jsonify({'error': 'Failed to create vibe profile'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add-to-vibe-profile', methods=['POST'])
def add_to_vibe_profile():
    """Add a poem to a vibe profile."""
    if not vibe_manager:
        return jsonify({'error': 'Vibe profile manager not available'}), 500
    
    try:
        data = request.get_json()
        poem_id = data.get('poem_id', '')
        vibe_profile_id = data.get('vibe_profile_id', '')
        similarity_score = data.get('similarity_score')
        
        if not poem_id or not vibe_profile_id:
            return jsonify({'error': 'Poem ID and Vibe Profile ID are required'}), 400
        
        success = vibe_manager.assign_item_to_vibe_profile(poem_id, vibe_profile_id, similarity_score)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to add poem to vibe profile'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/find-similar-to-vibe-profile', methods=['POST'])
def find_similar_to_vibe_profile():
    """Find poems similar to a vibe profile's centroid."""
    if not vibe_manager:
        return jsonify({'error': 'Vibe profile manager not available'}), 500
    
    try:
        data = request.get_json()
        vibe_profile_id = data.get('vibe_profile_id', '')
        top_k = int(data.get('top_k', 5))
        exclude_poem_ids = data.get('exclude_poem_ids', [])
        
        if not vibe_profile_id:
            return jsonify({'error': 'Vibe Profile ID is required'}), 400
        
        results = vibe_manager.find_similar_to_vibe_profile(vibe_profile_id, top_k, exclude_poem_ids)
        
        return jsonify({
            'vibe_profile_id': vibe_profile_id,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/update-vibe-profile-name', methods=['POST'])
def update_vibe_profile_name():
    """Update the name of a vibe profile."""
    if not vibe_manager:
        return jsonify({'error': 'Vibe profile manager not available'}), 500
    
    try:
        data = request.get_json()
        vibe_profile_id = data.get('vibe_profile_id', '')
        name = data.get('name', '')
        
        if not vibe_profile_id or not name:
            return jsonify({'error': 'Vibe Profile ID and name are required'}), 400
        
        success = vibe_manager.update_vibe_profile_name(vibe_profile_id, name)
        
        if success:
            return jsonify({'success': True, 'name': name})
        else:
            return jsonify({'error': 'Failed to update vibe profile name'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-all-vibe-profiles')
def get_all_vibe_profiles():
    """Get all vibe profiles with their poems."""
    if not vibe_manager:
        return jsonify({'error': 'Vibe profile manager not available'}), 500
    
    try:
        vibes = vibe_manager.get_all_vibe_profiles_with_poems()
        return jsonify({'vibes': vibes, 'count': len(vibes)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-vibe-profile/<vibe_profile_id>')
def get_vibe_profile(vibe_profile_id):
    """Get a single vibe profile with its poems."""
    if not vibe_manager:
        return jsonify({'error': 'Vibe profile manager not available'}), 500
    try:
        vibe_profile = vibe_manager.get_vibe_profile_with_poems(vibe_profile_id)
        
        if not vibe_profile:
            return jsonify({'error': 'Vibe profile not found'}), 404
        
        return jsonify(vibe_profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'engine_available': engine is not None,
        'vibe_manager_available': vibe_manager is not None
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting Flask app on port {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🌐 Open http://localhost:{port} in your browser")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
