import React, { useState } from 'react';
import { Poem, VibeProfile } from '../types';

interface PoemCardProps {
  poem: Poem;
  vibeProfiles: VibeProfile[];
  onAddToVibe: (poemId: string, vibeProfileId: string) => Promise<void>;
  onFindSimilar: (poemId: string) => void;
  isAddingToVibe: boolean;
}

const PoemCard: React.FC<PoemCardProps> = ({
  poem,
  vibeProfiles,
  onAddToVibe,
  onFindSimilar,
  isAddingToVibe,
}) => {
  const [showVibeMenu, setShowVibeMenu] = useState(false);

  const handleAddToVibe = async (vibeProfileId: string) => {
    await onAddToVibe(poem.id, vibeProfileId);
    setShowVibeMenu(false);
  };

  const handleCreateVibe = () => {
    // Simpler: use server page with deferred creation logic
    window.location.href = `/find_similar.html?id=${poem.id}`;
  };

  return (
    <div className="poem-card">
      <div className="poem-title">
        {poem.title || 'Untitled'}
      </div>
      
      <div className="poem-author">
        by {poem.author || 'Unknown'}
      </div>
      
      <div className="poem-text">
        {poem.text}
      </div>
      
      {poem.semantic_tags && poem.semantic_tags.length > 0 && (
        <div className="poem-tags">
          {poem.semantic_tags.map((tag, index) => (
            <span key={index} className="tag">
              {tag}
            </span>
          ))}
        </div>
      )}
      
      {poem.similarity && (
        <div className="similarity-score">
          Similarity: {(poem.similarity * 100).toFixed(1)}%
        </div>
      )}
      
      <div className="actions">
        <button
          className="btn btn-secondary"
          onClick={handleCreateVibe}
        >
          ✨ Create Vibe
        </button>
        
        <div style={{ position: 'relative' }}>
          <button
            className="btn"
            onClick={() => setShowVibeMenu(!showVibeMenu)}
            disabled={isAddingToVibe}
          >
            {isAddingToVibe ? 'Adding...' : '➕ Add to Vibe'}
          </button>
          
          {showVibeMenu && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                background: 'white',
                border: '1px solid #ddd',
                borderRadius: '5px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                zIndex: 1000,
                marginTop: '5px',
              }}
            >
              {vibeProfiles.length === 0 ? (
                <div style={{ padding: '10px', color: '#666' }}>
                  No vibe profiles available
                </div>
              ) : (
                vibeProfiles.map((vibe) => (
                  <button
                    key={vibe.id}
                    onClick={() => handleAddToVibe(vibe.id)}
                    style={{
                      width: '100%',
                      padding: '10px',
                      border: 'none',
                      background: 'none',
                      textAlign: 'left',
                      cursor: 'pointer',
                      borderBottom: '1px solid #eee',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#f8f9fa';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    {vibe.name} ({vibe.size || 0} poems)
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PoemCard;
