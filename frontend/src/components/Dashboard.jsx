import React, { useState, useEffect } from 'react';
import { onboardingAPI } from '../services/api';
import './Dashboard.css';

/**
 * Dashboard - now loads config from file instead of Confluence
 * Respects the settings for folder recursion and quiz toggling
 */
const Dashboard = ({ configId, onBack, onEdit }) => {
  const [config, setConfig] = useState(null);
  const [courseData, setCourseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizResults, setQuizResults] = useState(null);

  useEffect(() => {
    loadConfig();
    loadCourseData();
  }, [configId]);

  const loadConfig = async () => {
    try {
      const configData = await onboardingAPI.getConfig(configId);
      setConfig(configData);
    } catch (err) {
      console.error('Error loading config:', err);
    }
  };

  const loadCourseData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await onboardingAPI.getCourse(configId);
      setCourseData(data);
      
      // Log for debugging
      console.log('Course data loaded:', {
        configId,
        pageCount: data.source_pages?.length || 0,
        pages: data.source_pages
      });
      
    } catch (err) {
      console.error('Error loading course:', err);
      
      // More specific error messages
      if (err.response?.status === 404) {
        setError('Config not found. It may have been deleted.');
      } else if (err.response?.status === 401 || err.response?.status === 403) {
        setError('Confluence authentication failed. Check your API token in backend/.env');
      } else if (err.message.includes('Network Error')) {
        setError('Cannot connect to backend. Is it running on http://localhost:8000?');
      } else {
        setError(`Failed to load course: ${err.response?.data?.detail || err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGetSummary = async () => {
    try {
      const summaryData = await onboardingAPI.getCourseSummary(configId);
      setSummary(summaryData);
    } catch (err) {
      console.error('Error getting summary:', err);
      alert('Failed to generate summary. Check the console for details.');
    }
  };

  const handleGenerateQuiz = async () => {
    try {
      const quizData = await onboardingAPI.generateCourseQuiz(configId, 5);
      setQuiz(quizData);
      setQuizAnswers({});
      setQuizResults(null);
    } catch (err) {
      console.error('Error generating quiz:', err);
      alert('Failed to generate quiz.');
    }
  };

  const handleQuizSubmit = () => {
    if (!quiz) return;
    
    let correct = 0;
    quiz.questions.forEach((q, idx) => {
      if (quizAnswers[idx] === q.correct_answer) {
        correct++;
      }
    });
    
    setQuizResults({
      correct,
      total: quiz.questions.length,
      percentage: Math.round((correct / quiz.questions.length) * 100)
    });
  };

  const stripHTML = (html) => {
    // Quick and dirty HTML stripper for previews
    const tmp = document.createElement('DIV');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading">Loading course content... ⏳</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="error">{error}</div>
        <button onClick={onBack}>Go Back</button>
      </div>
    );
  }

  if (!courseData || !config) {
    return null;
  }

  // Check if quiz should be shown based on settings
  const showQuiz = config.settings?.test_at_end !== false;

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div>
          <h2>{config.emoji} {courseData.config.title}</h2>
          <p className="page-count">
            {courseData.source_pages.length} learning module{courseData.source_pages.length !== 1 ? 's' : ''}
            {config.settings.folder_recursion && ' (with folder expansion)'}
          </p>
        </div>
        <div className="header-actions">
          <button onClick={onEdit} className="edit-button">
            ✏️ Edit Config
          </button>
          <button onClick={onBack} className="back-button">
            ← Back to Courses
          </button>
        </div>
      </div>

      {/* Instructions from admin */}
      <div className="instructions-box">
        <h3>📋 Course Instructions</h3>
        <div 
          className="instructions-content"
          dangerouslySetInnerHTML={{ __html: courseData.config.instructions }}
        />
      </div>

      {/* Course actions */}
      <div className="course-actions">
        <button onClick={handleGetSummary} className="action-button summary-button">
          📝 Get Course Summary
        </button>
        {showQuiz && (
          <button onClick={handleGenerateQuiz} className="action-button quiz-button">
            ✅ Take Course Quiz
          </button>
        )}
      </div>

      {/* Summary display */}
      {summary && (
        <div className="summary-box">
          <h4>AI Summary:</h4>
          <p>{summary.summary}</p>
          <ul className="key-points">
            {summary.key_points.map((point, idx) => (
              <li key={idx}>{point}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Learning modules */}
      <div className="modules-section">
        <h3>📚 Learning Modules</h3>
        <p className="modules-hint">
          {config.settings.folder_recursion 
            ? "Folders are automatically expanded to include all child pages!"
            : "Linked pages are shown individually (folder expansion is off)"}
        </p>
        {courseData.source_pages.length === 0 ? (
          <div className="no-content">
            <p>❌ No pages could be loaded from Confluence</p>
            <p className="help-text" style={{ color: '#FF5630', marginTop: '1rem' }}>
              <strong>Possible reasons:</strong>
            </p>
            <ul style={{ textAlign: 'left', maxWidth: '500px', margin: '1rem auto', color: '#6B778C' }}>
              <li>Page IDs are incorrect (check the numbers)</li>
              <li>You don't have access to these pages in Confluence</li>
              <li>Confluence API token is invalid or expired</li>
              <li>Pages have been deleted from Confluence</li>
            </ul>
            <p className="help-text" style={{ marginTop: '1rem' }}>
              <strong>To fix:</strong>
            </p>
            <ol style={{ textAlign: 'left', maxWidth: '500px', margin: '0.5rem auto', color: '#6B778C' }}>
              <li>Run <code style={{ background: '#f4f5f7', padding: '2px 6px' }}>.\test-confluence.ps1</code> to test your connection</li>
              <li>Open a page in Confluence and copy its URL</li>
              <li>Click "✏️ Edit Config" and paste the full URL (we'll extract the ID)</li>
            </ol>
            <div style={{ marginTop: '1.5rem' }}>
              <button onClick={onEdit} className="action-button" style={{ background: '#FF5630' }}>
                ✏️ Edit Config & Fix Pages
              </button>
            </div>
          </div>
        ) : (
          <div className="pages-list">
            {courseData.source_pages.map((page) => (
              <div key={page.id} className="page-card">
                <h4>{page.title}</h4>
                <p className="page-preview">
                  {stripHTML(page.body).substring(0, 200)}...
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quiz section */}
      {quiz && (
        <div className="quiz-section">
          <h3>✅ Knowledge Check</h3>
          {quiz.questions.map((q, idx) => (
            <div 
              key={idx} 
              className="quiz-question"
              style={{
                backgroundColor: quizResults && (quizAnswers[idx] === q.correct_answer ? '#E3FCEF' : '#FFEBE6')
              }}
            >
              <h4>Question {idx + 1}: {q.question}</h4>
              {q.options.map((option, optIdx) => (
                <div key={optIdx} className="quiz-option">
                  <label>
                    <input 
                      type="radio" 
                      name={`question-${idx}`}
                      value={optIdx}
                      onChange={() => setQuizAnswers({...quizAnswers, [idx]: optIdx})}
                      disabled={quizResults !== null}
                    />
                    {option}
                  </label>
                </div>
              ))}
              {quizResults && (
                <div className="quiz-explanation">
                  <strong>Explanation:</strong> {q.explanation}
                </div>
              )}
            </div>
          ))}

          {!quizResults ? (
            <button onClick={handleQuizSubmit} className="submit-quiz-button">
              Submit Quiz
            </button>
          ) : (
            <div className="quiz-results">
              <h2>🎉 Results</h2>
              <p className="score">
                {quizResults.correct} / {quizResults.total} ({quizResults.percentage}%)
              </p>
              <p>
                {quizResults.percentage >= 80 ? 
                  "Great job! You're ready to move forward!" : 
                  "Keep learning! Review the materials and try again."}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
