import React, { useState, useEffect } from 'react';
import { onboardingAPI } from '../services/api';
import Quiz from './Quiz';
import './CourseViewer.css';

const CourseViewer = ({ configId, onClose, onStartQuiz }) => {
  const [course, setCourse] = useState(null);
  const [currentModuleIndex, setCurrentModuleIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [processingProgress, setProcessingProgress] = useState(null);
  const [showQuiz, setShowQuiz] = useState(false);
  const [updateStatus, setUpdateStatus] = useState(null);
  const [checkingUpdates, setCheckingUpdates] = useState(false);

  useEffect(() => {
    loadCourse();
    checkForUpdates();
  }, [configId]);

  // Removed automatic polling - user can manually refresh instead
  /*
  // Poll for processing progress when not yet processed
  useEffect(() => {
    if (processingStatus && !processingStatus.processed) {
      const interval = setInterval(async () => {
        try {
          const progress = await onboardingAPI.getProcessingProgress(configId);
          setProcessingProgress(progress);
          
          // If completed, reload the course
          if (progress.status === 'completed') {
            clearInterval(interval);
            loadCourse();
          }
        } catch (err) {
          console.error('Error fetching progress:', err);
        }
      }, 2000); // Poll every 2 seconds

      return () => clearInterval(interval);
    }
  }, [processingStatus, configId]);
  */

  const loadCourse = async () => {
    try {
      setLoading(true);
      setError(null);

      // Check if course is generated
      try {
        const courseData = await onboardingAPI.getGeneratedCourse(configId);
        setCourse(courseData);
        setLoading(false);
      } catch (err) {
        // Course not generated yet, check processing status
        if (err.response?.status === 404) {
          const status = await onboardingAPI.getProcessingStatus(configId);
          setProcessingStatus(status);
          setError('Course not generated yet');
        } else {
          throw err;
        }
        setLoading(false);
      }
    } catch (err) {
      console.error('Error loading course:', err);
      setError(err.response?.data?.detail || 'Failed to load course');
      setLoading(false);
    }
  };

  const handleGenerateCourse = async (numModules = 5) => {
    try {
      setGenerating(true);
      setError(null);
      await onboardingAPI.generateCourse(configId, numModules);
      
      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const courseData = await onboardingAPI.getGeneratedCourse(configId);
          setCourse(courseData);
          setGenerating(false);
          clearInterval(pollInterval);
        } catch (err) {
          // Still generating, continue polling
        }
      }, 3000);

      // Stop polling after 2 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        if (generating) {
          setGenerating(false);
          setError('Course generation is taking longer than expected. Please refresh.');
        }
      }, 120000);
    } catch (err) {
      console.error('Error generating course:', err);
      setError(err.response?.data?.detail || 'Failed to generate course');
      setGenerating(false);
    }
  };

  const checkForUpdates = async () => {
    try {
      setCheckingUpdates(true);
      const status = await onboardingAPI.checkForUpdates(configId);
      setUpdateStatus(status);
      setCheckingUpdates(false);
    } catch (err) {
      console.error('Error checking for updates:', err);
      setCheckingUpdates(false);
    }
  };

  const handleReprocess = async () => {
    try {
      await onboardingAPI.reprocessCourse(configId);
      alert('Course re-processing started. This may take a few moments...');
      // Refresh status after a delay
      setTimeout(() => {
        checkForUpdates();
      }, 5000);
    } catch (err) {
      console.error('Error reprocessing:', err);
      alert('Failed to start re-processing.');
    }
  };

  const handleNextModule = () => {
    if (currentModuleIndex < course.modules.length - 1) {
      setCurrentModuleIndex(currentModuleIndex + 1);
    }
  };

  const handlePreviousModule = () => {
    if (currentModuleIndex > 0) {
      setCurrentModuleIndex(currentModuleIndex - 1);
    }
  };

  const handleModuleSelect = (index) => {
    setCurrentModuleIndex(index);
  };

  if (loading) {
    return (
      <div className="course-viewer">
        <div className="course-loading">
          <div className="spinner"></div>
          <p>Loading course...</p>
        </div>
      </div>
    );
  }

  if (error && !processingStatus) {
    return (
      <div className="course-viewer">
        <div className="course-error">
          <h3>⚠️ Error</h3>
          <p>{error}</p>
          <button onClick={onClose} className="btn-secondary">Close</button>
        </div>
      </div>
    );
  }

  // Course not generated - show generation UI
  if (!course) {
    return (
      <div className="course-viewer">
        <div className="course-generate">
          <div className="generate-header">
            <h2>🎓 Generate AI Course</h2>
            <button onClick={onClose} className="btn-close">×</button>
          </div>

          <div className="generate-content">
            {processingStatus?.processed ? (
              <>
                <div className="status-card success">
                  <h3>✓ Content Processed</h3>
                  <p>{processingStatus.total_pages} pages have been embedded and ready for course generation</p>
                </div>

                <div className="generate-options">
                  <h3>Course Settings</h3>
                  <p>Generate an AI-powered interactive course from your Confluence content:</p>
                  
                  <div className="module-selector">
                    <label>Number of Modules:</label>
                    <select id="num-modules" defaultValue="5">
                      <option value="3">3 modules</option>
                      <option value="5">5 modules (recommended)</option>
                      <option value="7">7 modules</option>
                      <option value="10">10 modules</option>
                    </select>
                  </div>

                  <button 
                    onClick={() => {
                      const numModules = parseInt(document.getElementById('num-modules').value);
                      handleGenerateCourse(numModules);
                    }}
                    disabled={generating}
                    className="btn-primary btn-large"
                  >
                    {generating ? '🔄 Generating Course...' : '✨ Generate Course'}
                  </button>

                  {generating && (
                    <div className="generating-status">
                      <div className="spinner"></div>
                      <p>AI is creating your course modules... This may take 30-60 seconds.</p>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="status-card warning">
                <h3>⏳ Processing Content</h3>
                
                {processingProgress && processingProgress.status === 'running' ? (
                  <div className="progress-details">
                    <div className="progress-bar-container">
                      <div 
                        className="progress-bar-fill" 
                        style={{ width: `${processingProgress.progress_percentage}%` }}
                      ></div>
                      <span className="progress-percentage">{processingProgress.progress_percentage}%</span>
                    </div>
                    
                    <div className="current-step">
                      <strong>Step {processingProgress.current_step}/{processingProgress.total_steps}:</strong> {processingProgress.current_step_name}
                    </div>
                    
                    {processingProgress.steps_log && processingProgress.steps_log.length > 0 && (
                      <div className="progress-log">
                        <h4>Progress Log:</h4>
                        <div className="log-entries">
                          {processingProgress.steps_log.slice(-10).reverse().map((log, idx) => (
                            <div key={idx} className={`log-entry ${log.level || 'info'}`}>
                              <span className="log-time">
                                {new Date(log.timestamp).toLocaleTimeString()}
                              </span>
                              <span className="log-message">{log.details}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p>Your Confluence pages are being processed and embedded. Please wait...</p>
                )}
                
                <button onClick={loadCourse} className="btn-secondary">
                  🔄 Refresh Status
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  const currentModule = course.modules[currentModuleIndex];
  const progress = ((currentModuleIndex + 1) / course.modules.length) * 100;

  return (
    <div className="course-viewer">
      <div className="course-header">
        <div className="course-title">
          <h1>{course.title}</h1>
          <p className="course-description">{course.description}</p>
        </div>
        <button onClick={onClose} className="btn-close">×</button>
      </div>

      {updateStatus && updateStatus.needs_update && (
        <div className="update-banner">
          <div className="update-content">
            <span className="update-icon">🔄</span>
            <div className="update-text">
              <strong>Content Updates Available</strong>
              <p>{updateStatus.reason} - {updateStatus.total_changes} change(s) detected</p>
            </div>
          </div>
          <button onClick={handleReprocess} className="btn-update">
            Re-process Course
          </button>
        </div>
      )}

      <div className="course-progress">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
        <p className="progress-text">
          Module {currentModuleIndex + 1} of {course.modules.length}
        </p>
      </div>

      <div className="course-body">
        <aside className="course-sidebar">
          <h3>Course Modules</h3>
          <nav className="module-list">
            {course.modules.map((module, index) => (
              <button
                key={index}
                className={`module-item ${index === currentModuleIndex ? 'active' : ''} ${index < currentModuleIndex ? 'completed' : ''}`}
                onClick={() => handleModuleSelect(index)}
              >
                <span className="module-number">{module.module_number}</span>
                <span className="module-title">{module.title}</span>
                {index < currentModuleIndex && <span className="check-mark">✓</span>}
              </button>
            ))}
          </nav>
        </aside>

        <main className="course-content">
          <div className="module-header">
            <span className="module-badge">Module {currentModule.module_number}</span>
            <h2>{currentModule.title}</h2>
            <p className="module-description">{currentModule.description}</p>
          </div>

          <div className="module-overview">
            <h3>📋 Overview</h3>
            <p>{currentModule.overview}</p>
          </div>

          <div className="module-main-content">
            <h3>📚 Content</h3>
            <div 
              className="content-markdown"
              dangerouslySetInnerHTML={{ __html: formatMarkdown(currentModule.content) }}
            />
          </div>

          {currentModule.key_points && currentModule.key_points.length > 0 && (
            <div className="module-key-points">
              <h3>🔑 Key Points</h3>
              <ul>
                {currentModule.key_points.map((point, index) => (
                  <li key={index}>{point}</li>
                ))}
              </ul>
            </div>
          )}

          {currentModule.takeaways && currentModule.takeaways.length > 0 && (
            <div className="module-takeaways">
              <h3>💡 Takeaways</h3>
              <ul>
                {currentModule.takeaways.map((takeaway, index) => (
                  <li key={index}>{takeaway}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="module-navigation">
            <button 
              onClick={handlePreviousModule} 
              disabled={currentModuleIndex === 0}
              className="btn-secondary"
            >
              ← Previous
            </button>
            
            {currentModuleIndex === course.modules.length - 1 ? (
              <button 
                onClick={() => setShowQuiz(true)}
                className="btn-primary"
              >
                Take Final Quiz →
              </button>
            ) : (
              <button 
                onClick={handleNextModule}
                className="btn-primary"
              >
                Next Module →
              </button>
            )}
          </div>
        </main>
      </div>

      {showQuiz && (
        <Quiz
          configId={configId}
          moduleNumber={null}
          onClose={() => setShowQuiz(false)}
          onComplete={(results) => {
            setShowQuiz(false);
            if (results.passed && onStartQuiz) {
              onStartQuiz(configId);
            }
          }}
        />
      )}

      <div className="course-footer">
        <div className="source-info">
          <h4>📄 Source Material</h4>
          <p>{course.source_pages?.length || 0} Confluence pages</p>
        </div>
      </div>
    </div>
  );
};

// Simple markdown-to-HTML converter
const formatMarkdown = (text) => {
  if (!text) return '';
  
  let html = text;
  
  // Process tables first (before other replacements)
  html = html.replace(/^\|(.+)\|[ \t]*\n\|[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)+\|[ \t]*\n((?:\|.+\|[ \t]*\n?)+)/gm, (match, headerRow, bodyRows) => {
    // Parse header
    const headers = headerRow.split('|')
      .map(h => h.trim())
      .filter(h => h.length > 0);
    
    // Parse body rows
    const rows = bodyRows.trim().split('\n')
      .map(row => {
        return row.split('|')
          .map(cell => cell.trim())
          .filter(cell => cell.length > 0);
      });
    
    // Build HTML table
    let tableHtml = '<table class="markdown-table">';
    
    // Header
    tableHtml += '<thead><tr>';
    headers.forEach(header => {
      tableHtml += `<th>${header}</th>`;
    });
    tableHtml += '</tr></thead>';
    
    // Body
    tableHtml += '<tbody>';
    rows.forEach(row => {
      tableHtml += '<tr>';
      row.forEach(cell => {
        tableHtml += `<td>${cell}</td>`;
      });
      tableHtml += '</tr>';
    });
    tableHtml += '</tbody></table>';
    
    return tableHtml;
  });
  
  html = html
    // Headers (order matters - process from most # to least)
    .replace(/^##### (.*$)/gim, '<h5>$1</h5>')
    .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Code blocks
    .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>')
    // Inline code
    .replace(/`(.*?)`/g, '<code>$1</code>')
    // Line breaks
    .replace(/\n\n/g, '</p><p>')
    // Lists
    .replace(/^\* (.*$)/gim, '<li>$1</li>')
    .replace(/^- (.*$)/gim, '<li>$1</li>');
  
  // Wrap in paragraph if not already wrapped
  if (!html.startsWith('<')) {
    html = '<p>' + html + '</p>';
  }
  
  return html;
};

export default CourseViewer;
