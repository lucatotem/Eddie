import React, { useState } from 'react';
import ConfigManager from './components/ConfigManager';
import ConfigEditor from './components/ConfigEditor';
import Dashboard from './components/Dashboard';
import './App.css';

/**
 * Main app - handles navigation between config management, editing, and viewing
 * No more hardcoded roles, everything's file-based now!
 */
function App() {
  const [view, setView] = useState('manager'); // 'manager', 'editor', 'dashboard'
  const [selectedConfigId, setSelectedConfigId] = useState(null);
  const [editingConfigId, setEditingConfigId] = useState(null);

  const handleSelectConfig = (configId) => {
    setSelectedConfigId(configId);
    setView('dashboard');
  };

  const handleCreateNew = () => {
    setEditingConfigId(null);
    setView('editor');
  };

  const handleEdit = (configId) => {
    setEditingConfigId(configId);
    setView('editor');
  };

  const handleSaveConfig = () => {
    // After saving, go back to manager
    setView('manager');
    setEditingConfigId(null);
  };

  const handleCancelEdit = () => {
    setView('manager');
    setEditingConfigId(null);
  };

  const handleBackToManager = () => {
    setSelectedConfigId(null);
    setView('manager');
  };

  return (
    <div className="app">
      {view === 'manager' && (
        <ConfigManager 
          onSelectConfig={handleSelectConfig}
          onCreateNew={handleCreateNew}
        />
      )}
      
      {view === 'editor' && (
        <ConfigEditor 
          configId={editingConfigId}
          onSave={handleSaveConfig}
          onCancel={handleCancelEdit}
        />
      )}
      
      {view === 'dashboard' && (
        <Dashboard 
          configId={selectedConfigId}
          onBack={handleBackToManager}
          onEdit={() => handleEdit(selectedConfigId)}
        />
      )}
    </div>
  );
}

export default App;
