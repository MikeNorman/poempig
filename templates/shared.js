// Shared JavaScript utilities for all templates
// This file contains common functions to eliminate redundancy

const API_BASE_URL = 'http://localhost:5001';

// Common error handling
function showError(message, containerId = 'results-content') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<div class="error">❌ ${message}</div>`;
    } else {
        console.error('Error:', message);
        alert('Error: ' + message);
    }
}

// Common loading indicator
function showLoading(containerId = 'results-content', message = '🐷 Loading...') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<div class="loading">${message}</div>`;
    }
}

// Common fetch request with error handling
async function makeRequest(url, data, method = 'POST') {
    try {
        const requestOptions = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        // Only add body for POST, PUT, PATCH requests
        if (method !== 'GET' && method !== 'HEAD' && data) {
            requestOptions.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE_URL}${url}`, requestOptions);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Request failed');
        }
        
        return await response.json();
    } catch (error) {
        throw error;
    }
}

// Make makeRequest available globally
window.makeRequest = makeRequest;

// Common poem display function
function displayPoems(poems, containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const {
        showSimilarity = false,
        showTags = false,
        onFindSimilar = null,
        onAddToVibe = null,
        showActions = true
    } = options;
    
    if (poems.length === 0) {
        container.innerHTML = '<div class="no-results">No poems found.</div>';
        return;
    }
    
    let html = '';
    poems.forEach((result, index) => {
        const poem = result.poem || result;
        
        html += `
            <div class="poem-card" data-poem-id="${poem.id}">
                <div class="poem-title">${poem.title || 'Untitled'}</div>
                <div class="poem-author">by ${poem.author || 'Unknown'}</div>
                <div class="poem-text">${poem.text}</div>
                ${showTags && poem.semantic_tags ? `
                    <div class="poem-tags">
                        ${poem.semantic_tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                ` : ''}
                ${showSimilarity && result.similarity ? `
                    <div class="similarity-score">Similarity: ${(result.similarity * 100).toFixed(1)}%</div>
                ` : ''}
                ${showActions ? `
                    <div class="actions">
                        ${onFindSimilar ? `
                            <button class="btn btn-secondary" onclick="window.location.href='/vibe-profile.html?seed_id=${poem.id}'">
                                ✨ Create Vibe
                            </button>
                        ` : ''}
                        ${onAddToVibe ? `
                            <button class="btn" onclick="addToVibeProfile('${poem.id}')">
                                ➕ Add to Vibe
                            </button>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Make displayPoems available globally
window.displayPoems = displayPoems;

// Common add to vibe profile function
async function addToVibeProfile(itemId, vibeProfileId = null) {
    try {
        // If no vibe profile ID provided, show vibe selection column
        if (!vibeProfileId) {
            // Store the item ID for when a vibe is selected
            window.pendingItemId = itemId;
            
            // Show the vibe selection column
            const vibeColumn = document.getElementById('vibe-selection-column');
            if (vibeColumn) {
                vibeColumn.style.display = 'block';
                
                // Update the button text to show it's active
                const selectBtn = document.getElementById('select-vibe-btn');
                if (selectBtn) {
                    selectBtn.textContent = 'Cancel Selection';
                    selectBtn.classList.add('active');
                }
                
                // Load vibe profiles if not already loaded
                const vibeList = document.getElementById('vibe-list');
                if (vibeList.innerHTML.includes('Loading vibes...')) {
                    window.loadVibeProfiles();
                }
            }
            return;
        }
        
        const response = await makeRequest('/add-to-vibe-profile', {
            item_id: itemId,
            vibe_profile_id: vibeProfileId
        });
        
        if (response.success) {
            alert('Poem added to vibe profile successfully!');
            
            // Hide the vibe selection column after successful addition
            const vibeColumn = document.getElementById('vibe-selection-column');
            if (vibeColumn) {
                vibeColumn.style.display = 'none';
            }
            
            // Reset the button
            const selectBtn = document.getElementById('select-vibe-btn');
            if (selectBtn) {
                selectBtn.textContent = 'Select Vibe';
                selectBtn.classList.remove('active');
            }
            
            // Refresh vibe profiles if on a page that displays them
            if (typeof loadVibes === 'function') {
                loadVibes();
            }
        } else {
            showError('Failed to add poem to vibe profile');
        }
    } catch (error) {
        showError('Failed to add poem to vibe profile: ' + error.message);
    }
}

// Make addToVibeProfile available globally
window.addToVibeProfile = addToVibeProfile;

// Common find similar function
async function findSimilarPoems(poemId) {
    try {
        // Load the original poem first
        const poemResponse = await fetch(`${API_BASE_URL}/item/${poemId}`);
        if (!poemResponse.ok) {
            throw new Error('Failed to load poem');
        }
        const poem = await poemResponse.json();
        
        // Create a temporary vibe profile with just this poem
        const response = await makeRequest('/create-vibe-profile', {
            name: `Similar to "${poem.title || 'Untitled'}"`,
            item_ids: [poemId]
        });

        if (response.vibe_profile_id) {
            // Navigate to the vibe profile page
            window.location.href = `/vibe-profile/${response.vibe_profile_id}`;
        } else {
            throw new Error('Failed to create vibe profile');
        }
    } catch (error) {
        showError('Failed to find similar poems: ' + error.message);
    }
}

// Common vibe profile display function
function displayVibeProfiles(vibes, containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const {
        showPoemPreviews = true,
        maxPreviews = 3,
        onClick = null
    } = options;
    
    if (vibes.length === 0) {
        container.innerHTML = '<div class="no-vibes">No vibe profiles found</div>';
        return;
    }
    
    let html = '<div class="vibes-grid">';
    
    vibes.forEach(vibe => {
        const poems = vibe.poems || [];
        const poemsHtml = showPoemPreviews && poems.length > 0 
            ? poems.slice(0, maxPreviews).map(poem => `
                <div class="poem-preview">
                    <div class="poem-preview-title">${poem.title || 'Untitled'}</div>
                    <div class="poem-preview-author">by ${poem.author || 'Unknown'}</div>
                </div>
            `).join('') + (poems.length > maxPreviews ? 
                `<div class="poem-preview more">+${poems.length - maxPreviews} more</div>` : '')
            : '';
        
        const clickHandler = onClick ? `onclick="${onClick}('${vibe.id}')"` : '';
        
        html += `
            <div class="vibe-card" ${clickHandler}>
                <div class="vibe-name">${vibe.name}</div>
                ${poemsHtml ? `<div class="poem-previews">${poemsHtml}</div>` : ''}
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}
