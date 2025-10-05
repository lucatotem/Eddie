import React, { useState, useEffect } from 'react';
import './ConfigManager.css';
import { onboardingAPI } from '../services/api';

/**
 * Config manager - shows all saved configs and lets you create new ones
 * Replaces the old RoleSelector that had hardcoded roles
 */
function ConfigManager({ onSelectConfig, onCreateNew }) {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    try {
      setLoading(true);
      const data = await onboardingAPI.listConfigs();
      setConfigs(data);
    } catch (err) {
      setError('Failed to load configs: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (configId, e) => {
    e.stopPropagation(); // Don't trigger the card click
    
    if (!window.confirm('Are you sure you want to delete this config?')) {
      return;
    }

    try {
      await onboardingAPI.deleteConfig(configId);
      // Remove from list
      setConfigs(configs.filter(c => c.id !== configId));
    } catch (err) {
      alert('Failed to delete: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div className="config-manager">
        <h1>Loading onboarding courses...</h1>
      </div>
    );
  }

  if (error) {
    return (
      <div className="config-manager">
        <h1>Error</h1>
        <p className="error">{error}</p>
        <button onClick={loadConfigs}>Try Again</button>
      </div>
    );
  }

  return (
    <div className="config-manager">
      <h1>Onboarding Courses</h1>
      <p className="subtitle">
        {configs.length === 0 
          ? "No courses yet. Create your first one!"
          : "Select a course to view or create a new one"}
      </p>

      <div className="config-grid">
        {/* Create New Card */}
        <div className="config-card create-new" onClick={onCreateNew}>
          <div className="card-emoji">➕</div>
          <h3>Create New Course</h3>
          <p>Set up a custom onboarding course</p>
        </div>

        {/* Existing Configs */}
        {configs.map((config) => (
          <div 
            key={config.id}
            className="config-card"
            style={{ borderLeft: `4px solid ${config.color}` }}
            onClick={() => onSelectConfig(config.id)}
          >
            <div className="card-header">
              <div className="card-emoji">{config.emoji}</div>
              <button 
                className="delete-btn"
                onClick={(e) => handleDelete(config.id, e)}
                title="Delete config"
              >
                🗑️
              </button>
            </div>
            <h3>{config.name}</h3>
            <p className="card-instructions">{config.instructions}</p>
            
            <div className="card-meta">
              <span>{config.linked_pages.length} pages</span>
              {config.settings.folder_recursion && <span>📁 Folders enabled</span>}
              {config.settings.test_at_end && <span>✅ Quiz enabled</span>}
            </div>
            
            <p className="card-date">
              Updated {new Date(config.updated_at).toLocaleDateString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ConfigManager;
