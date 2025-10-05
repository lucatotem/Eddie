import React, { useState, useEffect } from 'react';
import './ConfigEditor.css';
import { onboardingAPI } from '../services/api';

/**
 * Config editor for creating/editing onboarding courses
 * No more manual Confluence label editing - finally!
 */
function ConfigEditor({ configId, onSave, onCancel }) {
  const [config, setConfig] = useState({
    name: '',
    emoji: '📚',
    color: '#4C9AFF',
    settings: {
      folder_recursion: true,
      test_at_end: true
    },
    instructions: '',
    linked_pages: []
  });
  
  const [pageInput, setPageInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load existing config if editing
  useEffect(() => {
    if (configId) {
      loadConfig();
    }
  }, [configId]);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await onboardingAPI.getConfig(configId);
      setConfig(data);
    } catch (err) {
      setError('Failed to load config: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setError(null);

      if (configId) {
        // Update existing
        await onboardingAPI.updateConfig(configId, config);
      } else {
        // Create new
        await onboardingAPI.createConfig(config);
      }

      if (onSave) onSave();
    } catch (err) {
      setError('Failed to save: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Extract page ID from Confluence URL or use direct ID
  const extractPageId = (input) => {
    const trimmed = input.trim();
    
    // If it's just a number, return it
    if (/^\d+$/.test(trimmed)) {
      return trimmed;
    }
    
    // Try to extract from URL: /pages/123456/Page-Title or /pages/123456
    const urlMatch = trimmed.match(/\/pages\/(\d+)/);
    if (urlMatch) {
      return urlMatch[1];
    }
    
    // If nothing matches, return original (will fail validation later)
    return trimmed;
  };

  const addPage = () => {
    const pageId = extractPageId(pageInput);
    
    if (pageId && !config.linked_pages.includes(pageId)) {
      setConfig({
        ...config,
        linked_pages: [...config.linked_pages, pageId]
      });
      setPageInput('');
      setError(null); // Clear any previous errors
    } else if (config.linked_pages.includes(pageId)) {
      setError('This page is already added!');
    }
  };

  const removePage = (pageId) => {
    setConfig({
      ...config,
      linked_pages: config.linked_pages.filter(id => id !== pageId)
    });
  };

  // Emoji picker - just a few common ones, not trying to reinvent the wheel here
  const emojis = ['📚', '🚀', '💻', '🎓', '👨‍💻', '🔧', '📊', '🎯', '✨', '🌟'];
  const colors = ['#4C9AFF', '#36B37E', '#FF5630', '#FFAB00', '#6554C0', '#00B8D9'];

  if (loading && configId) {
    return <div className="config-editor"><p>Loading...</p></div>;
  }

  return (
    <div className="config-editor">
      <h2>{configId ? 'Edit Onboarding Course' : 'Create New Onboarding Course'}</h2>
      
      {error && <div className="error-message">{error}</div>}

      {/* Basic Info */}
      <div className="form-section">
        <h3>Basic Info</h3>
        
        <label>
          Course Name
          <input
            type="text"
            value={config.name}
            onChange={(e) => setConfig({ ...config, name: e.target.value })}
            placeholder="e.g., Backend Developer Onboarding"
            required
          />
        </label>

        <div className="picker-row">
          <div>
            <label>Emoji</label>
            <div className="emoji-picker">
              {emojis.map(emoji => (
                <button
                  key={emoji}
                  type="button"
                  className={config.emoji === emoji ? 'selected' : ''}
                  onClick={() => setConfig({ ...config, emoji })}
                >
                  {emoji}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label>Card Color</label>
            <div className="color-picker">
              {colors.map(color => (
                <button
                  key={color}
                  type="button"
                  className={config.color === color ? 'selected' : ''}
                  style={{ backgroundColor: color }}
                  onClick={() => setConfig({ ...config, color })}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Settings */}
      <div className="form-section">
        <h3>Settings</h3>
        
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.settings.folder_recursion}
            onChange={(e) => setConfig({
              ...config,
              settings: { ...config.settings, folder_recursion: e.target.checked }
            })}
          />
          <div>
            <strong>Enable Folder Recursion</strong>
            <p>Automatically include all child pages when linking to a parent page</p>
          </div>
        </label>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.settings.test_at_end}
            onChange={(e) => setConfig({
              ...config,
              settings: { ...config.settings, test_at_end: e.target.checked }
            })}
          />
          <div>
            <strong>Quiz at End</strong>
            <p>Show a quiz after completing all modules</p>
          </div>
        </label>
      </div>

      {/* Instructions */}
      <div className="form-section">
        <h3>Instructions</h3>
        <label>
          What should this course teach?
          <textarea
            value={config.instructions}
            onChange={(e) => setConfig({ ...config, instructions: e.target.value })}
            placeholder="Describe what new hires should learn from this course..."
            rows="5"
            required
          />
        </label>
      </div>

      {/* Linked Pages */}
      <div className="form-section">
        <h3>Linked Pages/Folders</h3>
        <p className="hint">
          Paste a Confluence page URL or just the page ID. 
          {config.settings.folder_recursion && " Folders will auto-expand to include all children!"}
        </p>
        <p className="hint" style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>
          💡 <strong>Tip:</strong> Copy the URL from your browser: 
          <code style={{ background: '#f4f5f7', padding: '2px 6px', borderRadius: '3px', margin: '0 4px' }}>
            https://company.atlassian.net/wiki/pages/123456/Title
          </code>
        </p>
        
        <div className="page-adder">
          <input
            type="text"
            value={pageInput}
            onChange={(e) => setPageInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addPage())}
            placeholder="Paste full Confluence URL or page ID (e.g., 123456)..."
          />
          <button type="button" onClick={addPage} disabled={!pageInput.trim()}>
            Add Page
          </button>
        </div>

        {config.linked_pages.length > 0 && (
          <ul className="linked-pages-list">
            {config.linked_pages.map(pageId => (
              <li key={pageId}>
                <span>{pageId}</span>
                <button type="button" onClick={() => removePage(pageId)}>✕</button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Actions */}
      <div className="form-actions">
        <button 
          onClick={handleSave} 
          disabled={loading || !config.name || !config.instructions}
          className="primary"
        >
          {loading ? 'Saving...' : 'Save Course'}
        </button>
        <button onClick={onCancel} type="button">
          Cancel
        </button>
      </div>
    </div>
  );
}

export default ConfigEditor;
