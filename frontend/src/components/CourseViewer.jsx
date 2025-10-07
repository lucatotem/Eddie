import React, { useState, useEffect } from 'react';
import { onboardingAPI } from '../services/api';
import Quiz from './Quiz';
import './CourseViewer.css';

const CourseViewer = ({ configId, onClose, onStartQuiz }) => {
  const [course, setCourse] = useState(null);
  const [currentModuleIndex, setCurrentModuleIndex] = useState(0);
  const [currentFactIndex, setCurrentFactIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [processingProgress, setProcessingProgress] = useState(null);
  const [showQuiz, setShowQuiz] = useState(false);
  const [updateStatus, setUpdateStatus] = useState(null);
  const [checkingUpdates, setCheckingUpdates] = useState(false);
  const [completedFacts, setCompletedFacts] = useState(new Set());

  useEffect(() => {
    loadCourse();
    checkForUpdates();
  }, [configId]);

  // we used to auto-poll but it was annoying, now you just click refresh
  /*
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

      // see if the course exists
      try {
        const courseData = await onboardingAPI.getGeneratedCourse(configId);
        setCourse(courseData);
        setLoading(false);
      } catch (err) {
        // course not ready yet
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
      
      // keep checking until it's done
      const pollInterval = setInterval(async () => {
        try {
          const courseData = await onboardingAPI.getGeneratedCourse(configId);
          setCourse(courseData);
          setGenerating(false);
          clearInterval(pollInterval);
        } catch (err) {
          // still cooking...
        }
      }, 3000);

      // give up after 2 minutes (something probably went wrong)
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
    setCurrentFactIndex(0); // Reset to first fact of new module
  };

  // Build comprehensive facts array for current module
  const buildFactsArray = (module) => {
    if (!module) return [];
    
    const facts = [];
    
    // 1. Add overview as first fact
    if (module.overview) {
      facts.push({
        type: 'overview',
        content: module.overview,
        title: '📋 Overview'
      });
    }
    
    // 2. Add all main facts (if using new structure)
    if (module.facts && Array.isArray(module.facts)) {
      module.facts.forEach((fact, idx) => {
        facts.push({
          type: 'fact',
          content: fact,
          title: `💡 Concept ${idx + 1}`
        });
      });
    }
    // Fallback: if using old "content" structure, split it into chunks
    else if (module.content) {
      const contentChunks = module.content.split('\n\n').filter(c => c.trim());
      contentChunks.forEach((chunk, idx) => {
        facts.push({
          type: 'fact',
          content: chunk,
          title: `📚 Content ${idx + 1}`
        });
      });
    }
    
    // 3. Add each key point as a separate fact
    if (module.key_points && Array.isArray(module.key_points)) {
      module.key_points.forEach((point, idx) => {
        facts.push({
          type: 'key_point',
          content: point,
          title: `🔑 Key Point ${idx + 1}`
        });
      });
    }
    
    // 4. Add each takeaway as a separate fact
    if (module.takeaways && Array.isArray(module.takeaways)) {
      module.takeaways.forEach((takeaway, idx) => {
        facts.push({
          type: 'takeaway',
          content: takeaway,
          title: `💡 Takeaway ${idx + 1}`
        });
      });
    }
    
    return facts;
  };

  const handleNextFact = () => {
    const currentModule = course.modules[currentModuleIndex];
    const facts = buildFactsArray(currentModule);
    
    // Mark current fact as completed
    const factKey = `${currentModuleIndex}-${currentFactIndex}`;
    setCompletedFacts(prev => new Set([...prev, factKey]));
    
    if (currentFactIndex < facts.length - 1) {
      // Move to next fact in current module
      setCurrentFactIndex(currentFactIndex + 1);
    } else if (currentModuleIndex < course.modules.length - 1) {
      // Move to next module
      setCurrentModuleIndex(currentModuleIndex + 1);
      setCurrentFactIndex(0);
    } else {
      // Course complete - show quiz
      setShowQuiz(true);
    }
  };

  const handlePreviousFact = () => {
    if (currentFactIndex > 0) {
      setCurrentFactIndex(currentFactIndex - 1);
    } else if (currentModuleIndex > 0) {
      // Go to last fact of previous module
      setCurrentModuleIndex(currentModuleIndex - 1);
      const prevModule = course.modules[currentModuleIndex - 1];
      const prevFacts = buildFactsArray(prevModule);
      setCurrentFactIndex(prevFacts.length - 1);
    }
  };

  // Randomized encouraging messages for the Next button
  const nextButtonMessages = [
    "Next! ✨",
    "Keep going! 🚀",
    "You got this! 💪",
    "Onwards! 🎯",
    "Let's continue! 🌟",
    "Next up! ⚡",
    "Moving forward! 🎓",
    "Keep learning! 📚",
    "One more! 🔥"
  ];

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
  const currentFacts = buildFactsArray(currentModule);
  const currentFact = currentFacts[currentFactIndex];
  const totalFacts = currentFacts.length;
  const moduleProgress = totalFacts > 0 ? ((currentFactIndex + 1) / totalFacts) * 100 : 0;
  
  // Calculate overall progress across all modules
  let totalFactsInCourse = 0;
  let completedFactsCount = 0;
  course.modules.forEach((mod, modIdx) => {
    const modFacts = buildFactsArray(mod);
    totalFactsInCourse += modFacts.length;
    if (modIdx < currentModuleIndex) {
      completedFactsCount += modFacts.length;
    } else if (modIdx === currentModuleIndex) {
      completedFactsCount += currentFactIndex;
    }
  });
  const overallProgress = totalFactsInCourse > 0 ? (completedFactsCount / totalFactsInCourse) * 100 : 0;
  
  // Random next button message
  const nextMessage = nextButtonMessages[Math.floor(Math.random() * nextButtonMessages.length)];

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
          <div className="progress-fill" style={{ width: `${overallProgress}%` }}></div>
        </div>
        <p className="progress-text">
          Module {currentModuleIndex + 1} of {course.modules.length} • {Math.round(overallProgress)}% Complete
        </p>
      </div>

      <div className="course-body">
        <aside className="course-sidebar">
          <h3>Course Modules</h3>
          <nav className="module-list">
            {course.modules.map((module, index) => {
              const moduleFacts = buildFactsArray(module);
              const isComplete = index < currentModuleIndex;
              return (
                <button
                  key={index}
                  className={`module-item ${index === currentModuleIndex ? 'active' : ''} ${isComplete ? 'completed' : ''}`}
                  onClick={() => handleModuleSelect(index)}
                >
                  <span className="module-number">{module.module_number}</span>
                  <div className="module-info">
                    <span className="module-title">{module.title}</span>
                    <span className="module-facts-count">{moduleFacts.length} facts</span>
                  </div>
                  {isComplete && <span className="check-mark">✓</span>}
                </button>
              );
            })}
          </nav>
        </aside>

        <main className="course-content fact-card-view">
          <div className="module-header">
            <span className="module-badge">Module {currentModule.module_number}</span>
            <h2>{currentModule.title}</h2>
            <div className="module-progress-bar">
              <div className="module-progress-fill" style={{ width: `${moduleProgress}%` }}></div>
              <span className="module-progress-text">
                {currentFactIndex + 1} / {totalFacts}
              </span>
            </div>
          </div>

          {currentFact && (
            <div className="fact-card-container">
              <div className={`fact-card ${currentFact.type}`}>
                <div className="fact-card-header">
                  <h3>{currentFact.title}</h3>
                  <span className="fact-number">{currentFactIndex + 1} of {totalFacts}</span>
                </div>
                <div className="fact-card-content">
                  {currentFact.type === 'fact' ? (
                    <div 
                      className="content-markdown"
                      dangerouslySetInnerHTML={{ __html: formatMarkdown(currentFact.content) }}
                    />
                  ) : (
                    <p className="fact-text">{currentFact.content}</p>
                  )}
                </div>
                {completedFacts.has(`${currentModuleIndex}-${currentFactIndex}`) && (
                  <div className="fact-completed-badge">✓ Completed</div>
                )}
              </div>

              <div className="fact-navigation">
                <button 
                  onClick={handlePreviousFact} 
                  disabled={currentModuleIndex === 0 && currentFactIndex === 0}
                  className="btn-secondary"
                >
                  ← Previous
                </button>
                
                {currentModuleIndex === course.modules.length - 1 && currentFactIndex === totalFacts - 1 ? (
                  <button 
                    onClick={() => setShowQuiz(true)}
                    className="btn-primary btn-quiz"
                  >
                    🎯 Take Final Quiz →
                  </button>
                ) : (
                  <button 
                    onClick={handleNextFact}
                    className="btn-primary btn-next"
                  >
                    {nextMessage}
                  </button>
                )}
              </div>
            </div>
          )}
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
