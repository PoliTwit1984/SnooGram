import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [configs, setConfigs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [filterType, setFilterType] = useState('top_day');
  const [frequency, setFrequency] = useState(60);
  const [showDropdown, setShowDropdown] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [editForm, setEditForm] = useState({
    filter_type: '',
    frequency: ''
  });
  const [isAdding, setIsAdding] = useState(false);
  const [sendingNow, setSendingNow] = useState(null);

  useEffect(() => {
    fetchConfigs();
    const interval = setInterval(fetchConfigs, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (searchTerm.length > 2) {
      fetch(`http://localhost:8888/api/subreddits/search?q=${searchTerm}`)
        .then(response => response.json())
        .then(data => {
          setSearchResults(data);
          setShowDropdown(true);
        })
        .catch(error => console.error('Error:', error));
    } else {
      setSearchResults([]);
      setShowDropdown(false);
    }
  }, [searchTerm]);

  const fetchConfigs = () => {
    fetch('http://localhost:8888/api/configs')
      .then(response => response.json())
      .then(data => setConfigs(data))
      .catch(error => console.error('Error:', error));
  };

  const handleSubredditSelect = (subreddit) => {
    setSearchTerm(subreddit.name);
    setShowDropdown(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsAdding(true);
    const config = {
      subreddit_name: searchTerm.replace(/^r\//, ''),
      filter_type: filterType,
      frequency: parseInt(frequency)
    };

    try {
      const response = await fetch('http://localhost:8888/api/configs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
      });
      await response.json();
      setSearchTerm('');
      setFilterType('top_day');
      setFrequency(60);
      fetchConfigs();
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsAdding(false);
    }
  };

  const handleDelete = (configId) => {
    fetch(`http://localhost:8888/api/configs/${configId}`, {
      method: 'DELETE',
    })
      .then(() => fetchConfigs())
      .catch(error => console.error('Error:', error));
  };

  const handleToggle = (configId) => {
    fetch(`http://localhost:8888/api/configs/${configId}/toggle`, {
      method: 'POST',
    })
      .then(() => fetchConfigs())
      .catch(error => console.error('Error:', error));
  };

  const handleSendNow = async (configId) => {
    setSendingNow(configId);
    try {
      const response = await fetch(`http://localhost:8888/api/configs/${configId}/send-now`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to send now');
      }
      const data = await response.json();
      console.log('Send now successful:', data);
    } catch (error) {
      console.error('Error sending now:', error);
    } finally {
      setSendingNow(null);
    }
  };

  const handleEdit = (config) => {
    setEditingConfig(config.id);
    setEditForm({
      filter_type: config.filter_type,
      frequency: config.frequency
    });
  };

  const handleCancelEdit = () => {
    setEditingConfig(null);
    setEditForm({
      filter_type: '',
      frequency: ''
    });
  };

  const handleSaveEdit = (configId) => {
    fetch(`http://localhost:8888/api/configs/${configId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(editForm)
    })
      .then(response => response.json())
      .then(() => {
        setEditingConfig(null);
        setEditForm({
          filter_type: '',
          frequency: ''
        });
        fetchConfigs();
      })
      .catch(error => console.error('Error:', error));
  };

  return (
    <div className="App">
      <div className="logo-container">
        <img src="/SnooGramLogo.png" alt="SnooGram Logo" className="app-logo" />
      </div>
      <h1>SnooGram</h1>
      
      <form onSubmit={handleSubmit} className="config-form">
        <div className="form-group">
          <label>Subreddit:</label>
          <div className="search-container">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search or enter subreddit name..."
              disabled={isAdding}
            />
            {showDropdown && searchResults.length > 0 && (
              <div className="dropdown">
                {searchResults.map((subreddit) => (
                  <div
                    key={subreddit.name}
                    className="dropdown-item"
                    onClick={() => handleSubredditSelect(subreddit)}
                  >
                    {subreddit.name} {subreddit.over18 ? '(NSFW)' : ''}
                    <span className="subscribers">
                      {subreddit.subscribers ? subreddit.subscribers.toLocaleString() : '0'} subscribers
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="form-group">
          <label>Filter Type:</label>
          <select 
            value={filterType} 
            onChange={(e) => setFilterType(e.target.value)}
            disabled={isAdding}
          >
            <option value="top_day">Top of Day</option>
            <option value="top_week">Top of Week</option>
            <option value="top_month">Top of Month</option>
            <option value="top_year">Top of Year</option>
          </select>
        </div>

        <div className="form-group">
          <label>Frequency (minutes):</label>
          <input
            type="number"
            value={frequency}
            onChange={(e) => setFrequency(e.target.value)}
            min="1"
            disabled={isAdding}
          />
        </div>

        <button type="submit" disabled={!searchTerm.trim() || isAdding}>
          {isAdding ? (
            <span className="spinner"></span>
          ) : (
            'Add Subreddit'
          )}
        </button>
      </form>

      <div className="configs">
        <h2>Active Configurations</h2>
        <div className="config-list">
          {configs.map(config => (
            <div key={config.id} className="config-item">
              <div className="config-info">
                <h3>r/{config.subreddit_name}</h3>
                {editingConfig === config.id ? (
                  <div className="edit-form">
                    <select
                      value={editForm.filter_type}
                      onChange={(e) => setEditForm({...editForm, filter_type: e.target.value})}
                    >
                      <option value="top_day">Top of Day</option>
                      <option value="top_week">Top of Week</option>
                      <option value="top_month">Top of Month</option>
                      <option value="top_year">Top of Year</option>
                    </select>
                    <input
                      type="number"
                      value={editForm.frequency}
                      onChange={(e) => setEditForm({...editForm, frequency: parseInt(e.target.value)})}
                      min="1"
                    />
                    <div className="edit-actions">
                      <button onClick={() => handleSaveEdit(config.id)}>Save</button>
                      <button onClick={handleCancelEdit}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p>Filter: {config.filter_type}</p>
                    <p>Frequency: {config.frequency} minutes</p>
                    <p>Status: {config.is_active ? 'Active' : 'Inactive'}</p>
                  </>
                )}
              </div>
              <div className="config-actions">
                {!editingConfig && (
                  <>
                    <button onClick={() => handleEdit(config)}>Edit</button>
                    <button onClick={() => handleToggle(config.id)}>
                      {config.is_active ? 'Disable' : 'Enable'}
                    </button>
                    <button 
                      onClick={() => handleSendNow(config.id)}
                      disabled={sendingNow === config.id}
                    >
                      {sendingNow === config.id ? (
                        <span className="spinner"></span>
                      ) : (
                        'Send Now'
                      )}
                    </button>
                    <button onClick={() => handleDelete(config.id)}>Delete</button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
