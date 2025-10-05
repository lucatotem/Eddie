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

  const loadQuiz = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try to get existing quiz
      try {
        const quizData = await onboardingAPI.getQuiz(configId, moduleNumber);
        setQuiz(quizData);
        setAnswers(new Array(quizData.total_questions).fill(null));
        setLoading(false);
      } catch (err) {
        // Quiz not generated yet
        if (err.response?.status === 404) {
          setError('Quiz not generated yet');
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
    if (submitted) return; // Can't change answers after submission

    const newAnswers = [...answers];
    newAnswers[questionIndex] = optionIndex;
    setAnswers(newAnswers);
  };

  const handleSubmit = async () => {
    // Check if all questions are answered
    if (answers.some(a => a === null)) {
      alert('Please answer all questions before submitting.');
      return;
    }

    try {
      const results = await onboardingAPI.submitQuiz(configId, answers, moduleNumber);
      setResults(results);
      setSubmitted(true);

      // Scroll to results
      setTimeout(() => {
        document.querySelector('.quiz-results')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      console.error('Error submitting quiz:', err);
      alert('Failed to submit quiz. Please try again.');
    }
  };

  const handleRetry = () => {
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
        </div>
      </div>
    );
  }

  if (error && !quiz) {
    return (
      <div className="quiz-container">
        <div className="quiz-generate">
          <div className="generate-header">
            <h2>📝 Generate Quiz</h2>
            <button onClick={onClose} className="btn-close">×</button>
          </div>

          <div className="generate-content">
            <p>Create an AI-generated quiz to test your knowledge!</p>

            <div className="quiz-options">
              <div className="option-group">
                <label>Number of Questions:</label>
                <select id="num-questions" defaultValue="5">
                  <option value="3">3 questions</option>
                  <option value="5">5 questions (recommended)</option>
                  <option value="7">7 questions</option>
                  <option value="10">10 questions</option>
                </select>
              </div>

              <div className="option-group">
                <label>Difficulty:</label>
                <select id="difficulty" defaultValue="medium">
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>

              <button
                onClick={() => {
                  const numQuestions = parseInt(document.getElementById('num-questions').value);
                  const difficulty = document.getElementById('difficulty').value;
                  handleGenerateQuiz(numQuestions, difficulty);
                }}
                disabled={generating}
                className="btn-primary btn-large"
              >
                {generating ? '🔄 Generating Quiz...' : '✨ Generate Quiz'}
              </button>

              {generating && (
                <div className="generating-status">
                  <div className="spinner"></div>
                  <p>AI is creating your quiz questions... This may take 20-30 seconds.</p>
                </div>
              )}
            </div>
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
