import React, { useState, useEffect } from 'react';
import { onboardingAPI } from '../services/api';
import './Quiz.css';

const Quiz = ({ configId, moduleNumber = null, onClose, onComplete }) => {
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadQuiz();
  }, [configId, moduleNumber]);

  // keyboard shortcuts so people can spam A/B/C/D instead of clicking
  // (way faster for taking quizzes, trust me)
  useEffect(() => {
    const handleKeyPress = (event) => {
      // don't do anything if quiz isn't loaded or already submitted
      if (!quiz || submitted) return;

      const key = event.key.toUpperCase();
      const currentQuestionData = quiz.questions[currentQuestion];
      if (!currentQuestionData) return;

      const numOptions = currentQuestionData.options.length;
      let selectedIndex = null;

      // A/B/C/D keys
      if (key >= 'A' && key <= 'D') {
        selectedIndex = key.charCodeAt(0) - 65; // A=0, B=1, C=2, D=3
      }
      // 1/2/3/4 keys also work
      else if (key >= '1' && key <= '4') {
        selectedIndex = parseInt(key) - 1;
      }

      // select it if it's a valid option
      if (selectedIndex !== null && selectedIndex < numOptions) {
        handleAnswerSelect(currentQuestion, selectedIndex);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);  // cleanup!
  }, [quiz, submitted, currentQuestion, answers]);

  const loadQuiz = async () => {
    try {
      setLoading(true);
      setError(null);

      // try to get quiz, or make it auto-generate if it doesn't exist yet
      try {
        const quizData = await onboardingAPI.getQuiz(configId, moduleNumber);
        setQuiz(quizData);
        setAnswers(new Array(quizData.total_questions).fill(null));
        
        // log if we just created it
        if (quizData.generated_now) {
          console.log('Quiz was generated on the fly!');
        }
        
        setLoading(false);
      } catch (err) {
        // Quiz couldn't be generated or loaded
        if (err.response?.status === 404) {
          setError('Course not generated yet. Please generate the course first.');
        } else if (err.response?.status === 500) {
          setError(err.response?.data?.detail || 'Failed to generate quiz. Please try again.');
        } else {
          throw err;
        }
        setLoading(false);
      }
    } catch (err) {
      console.error('Error loading quiz:', err);
      setError(err.response?.data?.detail || 'Failed to load quiz');
      setLoading(false);
    }
  };

  const handleGenerateQuiz = async (numQuestions = 5, difficulty = 'medium') => {
    try {
      setGenerating(true);
      setError(null);

      await onboardingAPI.generateQuiz(configId, {
        moduleNumber,
        numQuestions,
        difficulty
      });

      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const quizData = await onboardingAPI.getQuiz(configId, moduleNumber);
          setQuiz(quizData);
          setAnswers(new Array(quizData.total_questions).fill(null));
          setGenerating(false);
          clearInterval(pollInterval);
        } catch (err) {
          // Still generating, continue polling
        }
      }, 2000);

      // Stop polling after 90 seconds
      setTimeout(() => {
        clearInterval(pollInterval);
        if (generating) {
          setGenerating(false);
          setError('Quiz generation is taking longer than expected. Please refresh.');
        }
      }, 90000);
    } catch (err) {
      console.error('Error generating quiz:', err);
      setError(err.response?.data?.detail || 'Failed to generate quiz');
      setGenerating(false);
    }
  };

  const handleAnswerSelect = (questionIndex, optionIndex) => {
    if (submitted) return; // can't change answers after submitting!

    const newAnswers = [...answers];
    newAnswers[questionIndex] = optionIndex;
    setAnswers(newAnswers);
  };

  const handleSubmit = async () => {
    // make sure they answered everything
    if (answers.some(a => a === null)) {
      alert('Please answer all questions before submitting.');
      return;
    }

    try {
      const results = await onboardingAPI.submitQuiz(configId, answers, moduleNumber);
      setResults(results);
      setSubmitted(true);

      // scroll down to see results
      setTimeout(() => {
        document.querySelector('.quiz-results')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      console.error('Error submitting quiz:', err);
      alert('Failed to submit quiz. Please try again.');
    }
  };

  const handleRetry = () => {
    // reset everything for another attempt
    setAnswers(new Array(quiz.total_questions).fill(null));
    setCurrentQuestion(0);
    setSubmitted(false);
    setResults(null);
  };

  const handleFinish = () => {
    if (onComplete) {
      onComplete(results);
    } else {
      onClose();
    }
  };

  if (loading) {
    return (
      <div className="quiz-container">
        <div className="quiz-loading">
          <div className="spinner"></div>
          <p>Loading quiz...</p>
          <p className="loading-subtext">Checking for existing quiz or generating a new one...</p>
        </div>
      </div>
    );
  }

  if (error && !quiz) {
    return (
      <div className="quiz-container">
        <div className="quiz-error">
          <div className="error-header">
            <h2>⚠️ Quiz Not Available</h2>
            <button onClick={onClose} className="btn-close">×</button>
          </div>

          <div className="error-content">
            <p className="error-message">{error}</p>
            
            {error.includes('Course not generated') ? (
              <div className="error-actions">
                <p>Please generate the course first, then come back for the quiz.</p>
                <button onClick={onClose} className="btn-primary">
                  Go Back to Course
                </button>
              </div>
            ) : (
              <div className="error-actions">
                <p>Would you like to try loading the quiz again?</p>
                <button onClick={loadQuiz} className="btn-primary">
                  Retry Loading Quiz
                </button>
                <button onClick={onClose} className="btn-secondary">
                  Go Back
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!quiz) return null;

  const allAnswered = answers.every(a => a !== null);
  const quizType = moduleNumber !== null ? `Module ${moduleNumber}` : 'Final Assessment';

  return (
    <div className="quiz-container">
      <div className="quiz-header">
        <div>
          <h1>{quiz.quiz_title}</h1>
          <p className="quiz-meta">
            {quiz.total_questions} questions • {quiz.difficulty} difficulty
          </p>
        </div>
        <button onClick={onClose} className="btn-close">×</button>
      </div>

      {!submitted ? (
        <>
          <div className="quiz-progress">
            <div className="progress-info">
              <span>Question {currentQuestion + 1} of {quiz.total_questions}</span>
              <span className="answered-count">
                {answers.filter(a => a !== null).length} answered
              </span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${((currentQuestion + 1) / quiz.total_questions) * 100}%` }}
              ></div>
            </div>
            <div className="keyboard-hint">
              ⌨️ Tip: Press A/B/C/D or 1/2/3/4 to select answers
            </div>
          </div>

          <div className="quiz-body">
            <div className="question-navigation">
              {quiz.questions.map((_, index) => (
                <button
                  key={index}
                  className={`question-nav-btn ${index === currentQuestion ? 'active' : ''} ${answers[index] !== null ? 'answered' : ''}`}
                  onClick={() => setCurrentQuestion(index)}
                >
                  {index + 1}
                </button>
              ))}
            </div>

            <div className="question-card">
              <div className="question-header">
                <span className="question-number">Question {currentQuestion + 1}</span>
                <span className={`difficulty-badge ${quiz.questions[currentQuestion].difficulty}`}>
                  {quiz.questions[currentQuestion].difficulty}
                </span>
              </div>

              <h3 className="question-text">
                {quiz.questions[currentQuestion].question}
              </h3>

              <div className="options-list">
                {quiz.questions[currentQuestion].options.map((option, optionIndex) => (
                  <button
                    key={optionIndex}
                    className={`option-btn ${answers[currentQuestion] === optionIndex ? 'selected' : ''}`}
                    onClick={() => handleAnswerSelect(currentQuestion, optionIndex)}
                  >
                    <span className="option-letter">
                      {String.fromCharCode(65 + optionIndex)}
                    </span>
                    <span className="option-text">{option}</span>
                    {answers[currentQuestion] === optionIndex && (
                      <span className="check-mark">✓</span>
                    )}
                  </button>
                ))}
              </div>

              <div className="question-actions">
                <button
                  onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
                  disabled={currentQuestion === 0}
                  className="btn-secondary"
                >
                  ← Previous
                </button>

                {currentQuestion === quiz.total_questions - 1 ? (
                  <button
                    onClick={handleSubmit}
                    disabled={!allAnswered}
                    className="btn-primary submit-btn"
                  >
                    Submit Quiz →
                  </button>
                ) : (
                  <button
                    onClick={() => setCurrentQuestion(Math.min(quiz.total_questions - 1, currentQuestion + 1))}
                    className="btn-primary"
                  >
                    Next →
                  </button>
                )}
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="quiz-results">
          <div className="results-header">
            <div className={`score-card ${results.passed ? 'passed' : 'failed'}`}>
              <div className="score-circle">
                <svg viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" className="score-bg" />
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    className="score-progress"
                    style={{
                      strokeDasharray: `${(results.score_percentage / 100) * 283} 283`
                    }}
                  />
                </svg>
                <div className="score-text">
                  <span className="score-number">{results.score_percentage}%</span>
                  <span className="score-label">Score</span>
                </div>
              </div>

              <div className="score-details">
                <h2>{results.passed ? '🎉 Congratulations!' : '📚 Keep Learning!'}</h2>
                <p>
                  You got {results.correct_answers} out of {results.total_questions} questions correct
                </p>
                {results.passed ? (
                  <p className="pass-message">Great job! You've passed the quiz.</p>
                ) : (
                  <p className="fail-message">You need 70% to pass. Review the material and try again!</p>
                )}
              </div>
            </div>
          </div>

          <div className="results-breakdown">
            <h3>📊 Question-by-Question Breakdown</h3>

            {results.results.map((result, index) => (
              <div key={index} className={`result-item ${result.is_correct ? 'correct' : 'incorrect'}`}>
                <div className="result-header">
                  <span className="result-number">Question {result.question_number}</span>
                  <span className={`result-badge ${result.is_correct ? 'correct' : 'incorrect'}`}>
                    {result.is_correct ? '✓ Correct' : '✗ Incorrect'}
                  </span>
                </div>

                <p className="result-question">{result.question}</p>

                <div className="result-answers">
                  <div className={`answer-box ${result.is_correct ? '' : 'wrong'}`}>
                    <strong>Your answer:</strong> {result.selected_option}
                  </div>
                  {!result.is_correct && (
                    <div className="answer-box correct">
                      <strong>Correct answer:</strong> {result.correct_option}
                    </div>
                  )}
                </div>

                <div className="result-explanation">
                  <strong>💡 Explanation:</strong>
                  <p>{result.explanation}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="results-actions">
            <button onClick={handleRetry} className="btn-secondary">
              🔄 Retake Quiz
            </button>
            <button onClick={handleFinish} className="btn-primary">
              {results.passed ? '✓ Continue' : '📚 Review Material'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Quiz;
