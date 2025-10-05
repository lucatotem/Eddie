import React, { useState, useEffect } from 'react';
import { onboardingAPI } from '../services/api';
import './RoleSelector.css';

const RoleSelector = ({ onCourseSelect }) => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
    try {
      setLoading(true);
      const configs = await onboardingAPI.getAllConfigs();
      setCourses(configs);
    } catch (err) {
      console.error('Error loading courses:', err);
      setError('Failed to load onboarding courses. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  // Emoji picker for visual variety (can be customized per course later)
  const getEmojiForCourse = (index) => {
    const emojis = ['�‍💻', '🎨', '📊', '🔍', '🚀', '💡', '⚙️', '📚'];
    return emojis[index % emojis.length];
  };

  const getColorForCourse = (index) => {
    const colors = ['#0052CC', '#6554C0', '#00875A', '#FF5630', '#FF8B00', '#00B8D9'];
    return colors[index % colors.length];
  };

  if (loading) {
    return (
      <div className="role-selector-container">
        <div className="loading">Loading onboarding courses... ⏳</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="role-selector-container">
        <div className="error">
          <p>{error}</p>
          <button onClick={loadCourses}>Try Again</button>
        </div>
      </div>
    );
  }

  return (
    <div className="role-selector-container">
      <div className="header">
        <h1>Welcome to Eddie! 👋</h1>
        <p className="subtitle">
          Choose your onboarding course to get started
        </p>
        <p className="description">
          {courses.length > 0 
            ? `We have ${courses.length} onboarding course${courses.length > 1 ? 's' : ''} ready for you`
            : 'No courses available yet. Ask an admin to create one!'}
        </p>
      </div>

      {courses.length > 0 ? (
        <div className="roles-grid">
          {courses.map((course, index) => (
            <button
              key={course.id}
              className="role-card"
              style={{
                borderColor: getColorForCourse(index),
              }}
              onClick={() => onCourseSelect(course)}
            >
              <div className="role-emoji">{getEmojiForCourse(index)}</div>
              <h3 className="role-title">{course.title}</h3>
              <p className="role-description">
                {course.source_page_ids.length} page{course.source_page_ids.length !== 1 ? 's' : ''} to learn
              </p>
            </button>
          ))}
        </div>
      ) : (
        <div className="no-courses">
          <p>📝 No onboarding courses found</p>
          <p className="help-text">
            To create one, make a Confluence page with instructions and link to your learning materials.
            Then label it with "onboarding-config"
          </p>
        </div>
      )}

      <div className="footer-note">
        <p>Onboarding courses are created and managed in Confluence by your team</p>
      </div>
    </div>
  );
};

export default RoleSelector;
