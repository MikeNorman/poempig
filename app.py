"""
Flask Web Application for Poem Recommender
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import os
from dotenv import load_dotenv
from src.vibe_profile_manager import VibeProfileManager                                                      

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)


# Initialize recommendation engine (lazy import to avoid heavy deps during simple runs)
try:
    from src.recommendation_engine import ItemRecommendationEngine
    engine = ItemRecommendationEngine()
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
    """Serve the template homepage as the default."""
    return render_template('index.html')

@app.route('/static/<filename>')
def static_files(filename):
    """Serve static files from templates directory"""
    return send_from_directory('templates', filename)

## Removed redundant /old route; / now serves the template homepage

# Removed unused React build serving - we only serve templates now

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
    """Search for items (poems and quotes) based on query."""
    if not engine:
        return jsonify({'error': 'Recommendation engine not available'}), 500

    try:
        data = request.get_json()
        query = data.get('query', '')
        top_k = int(data.get('top_k', 5))
        offset = int(data.get('offset', 0))

        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'}), 400

        # Search for similar items - get all results for pagination
        all_results = engine.search_items(query)

        # Apply offset for pagination
        if offset > 0:
            results = all_results[offset:]
        else:
            results = all_results

        # Limit to requested page size
        results = results[:top_k]

        # Format results to match frontend expectations
        formatted_results = []
        for result in results:
            formatted_results.append({
                'poem': result['item'],  # Frontend expects 'poem' key
                'similarity': result['similarity']
            })

        return jsonify({
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results),
            'total_available': len(all_results)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/item/<item_id>')
def get_item(item_id):
    """Get a specific item by ID."""
    if not engine:
        return jsonify({'error': 'Recommendation engine not available'}), 500

    try:
        item = engine.get_item_by_id(item_id)
        if item:
            return jsonify(item)
        else:
            return jsonify({'error': 'Item not found'}), 404
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
        item_ids = data.get('item_ids', [])
        
        print(f"Creating vibe profile with name: '{name}' and {len(item_ids)} items")
        vibe_profile_id = vibe_manager.create_vibe_profile(name, item_ids)
        print(f"Created vibe profile with ID: {vibe_profile_id}")
        
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
        item_id = data.get('item_id', '')
        vibe_profile_id = data.get('vibe_profile_id', '')
        similarity_score = data.get('similarity_score')
        
        if not item_id or not vibe_profile_id:
            return jsonify({'error': 'Item ID and Vibe Profile ID are required'}), 400
        
        success = vibe_manager.assign_item_to_vibe_profile(item_id, vibe_profile_id, similarity_score)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to add poem to vibe profile'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/find-similar', methods=['POST'])
def find_similar():
    """Find similar items to a single item."""
    if not engine:
        return jsonify({'error': 'Recommendation engine not available'}), 500
    
    try:
        data = request.get_json()
        item_id = data.get('item_id', '')
        top_k = int(data.get('top_k', 5))
        
        if not item_id:
            return jsonify({'error': 'Item ID is required'}), 400
        
        # Get the item first
        item = engine.get_item_by_id(item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        # Find similar items using the item's text
        similar_items = engine.search_items(item.get('text', ''))
        
        # Filter out the original item
        similar_items = [result for result in similar_items if result['item']['id'] != item_id]
        
        return jsonify({
            'item_id': item_id,
            'results': similar_items[:top_k],
            'count': len(similar_items[:top_k])
        })
        
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
        exclude_item_ids = data.get('exclude_item_ids', [])
        
        if not vibe_profile_id:
            return jsonify({'error': 'Vibe Profile ID is required'}), 400
        
        results = vibe_manager.find_similar_to_vibe_profile(vibe_profile_id, top_k, exclude_item_ids)
        
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
        
        print(f"Returning vibe profile: {vibe_profile.get('name', 'NO NAME')} (ID: {vibe_profile_id})")
        return jsonify(vibe_profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/vibe-profiles', methods=['GET'])
def get_vibe_profiles():
    """Get all vibe profiles."""
    if not vibe_manager:
        return jsonify({'error': 'Vibe profile manager not available'}), 500
    
    try:
        profiles = vibe_manager.get_all_vibe_profiles_with_poems()
        return jsonify(profiles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/vibe-profile.html')
def vibe_profile_page():
    """Vibe profile page that handles both existing vibe profiles and new seed items"""
    vibe_profile_id = request.args.get('vibe_profile_id')
    seed_id = request.args.get('seed_id')
    
    if vibe_profile_id:
        # Load existing vibe profile
        try:
            vibe_profile = vibe_manager.get_vibe_profile_with_poems(vibe_profile_id)
            if not vibe_profile:
                return render_template('error.html', 
                                     error_title="Vibe Profile Not Found",
                                     error_message="The requested vibe profile could not be found."), 404
            
            return render_template('vibe_profile.html', vibe_profile=vibe_profile)
        except Exception as e:
            return render_template('error.html', 
                                 error_title="Error Loading Vibe Profile",
                                 error_message=f"An error occurred while loading the vibe profile: {str(e)}"), 500
    elif seed_id:
        # New vibe profile with seed item - no vibe_profile data needed
        return render_template('vibe_profile.html')
    else:
        return render_template('error.html', 
                             error_title="Invalid Request",
                             error_message="No vibe profile ID or seed ID provided."), 400

@app.route('/vibe-profile/<vibe_profile_id>')
def vibe_profile_redirect(vibe_profile_id):
    """Redirect old vibe profile URLs to new format"""
    return redirect(f'/vibe-profile.html?vibe_profile_id={vibe_profile_id}')

@app.route('/delete-vibe-profile/<vibe_profile_id>', methods=['DELETE'])
def delete_vibe_profile(vibe_profile_id):
    """Delete a vibe profile and all its associated items."""
    if not vibe_manager:
        return jsonify({'error': 'Vibe profile manager not available'}), 500
    
    try:
        success = vibe_manager.delete_vibe_profile(vibe_profile_id)
        if success:
            return jsonify({'message': f'Vibe profile {vibe_profile_id} deleted successfully'}), 200
        else:
            return jsonify({'error': f'Failed to delete vibe profile {vibe_profile_id}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error deleting vibe profile: {str(e)}'}), 500

@app.route('/search-keywords', methods=['POST'])
def search_keywords():
    """Search items by keywords in title, author, or text"""
    if not engine:
        return jsonify({'error': 'Recommendation engine not available'}), 500
    
    try:
        data = request.get_json()
        keywords = data.get('keywords', '').strip()
        
        if not keywords:
            return jsonify({'results': []})
        
        # Search for items containing the keywords
        results = engine.search_by_keywords(keywords)
        
        return jsonify({
            'results': results,
            'keywords': keywords
        })
        
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

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
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'  # Default to True for auto-reload
    
    print(f"🚀 Starting Flask app on port {port}")
    print(f"🔧 Debug mode: {debug} (auto-reload enabled)")
    print(f"🌐 Open http://localhost:{port} in your browser")
    print(f"🔄 Code changes will automatically restart the server")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
