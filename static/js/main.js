// Main application JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication status
    const token = localStorage.getItem('token');
    const currentPath = window.location.pathname;
    
    // Redirect to login if not authenticated (except login page)
    if (!token && !currentPath.includes('login')) {
        window.location.href = '/login';
        return;
    }
    
    // If authenticated and on login page, redirect to dashboard
    if (token && currentPath.includes('login')) {
        window.location.href = '/dashboard';
    }
    
    // Logout functionality
    const logoutLinks = document.querySelectorAll('[href="/logout"]');
    logoutLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('token');
            window.location.href = '/login';
        });
    });
    
    // Close flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        const closeBtn = message.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                message.remove();
            });
        }
    });
    
    // Initialize tooltips
    const tooltipTriggers = document.querySelectorAll('[data-tooltip]');
    tooltipTriggers.forEach(trigger => {
        trigger.addEventListener('mouseenter', showTooltip);
        trigger.addEventListener('mouseleave', hideTooltip);
    });
});

function showTooltip(e) {
    const tooltipText = this.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    tooltip.className = 'absolute z-10 bg-gray-800 text-white text-xs rounded py-1 px-2 whitespace-nowrap';
    tooltip.textContent = tooltipText;
    
    const rect = this.getBoundingClientRect();
    tooltip.style.top = `${rect.bottom + window.scrollY + 5}px`;
    tooltip.style.left = `${rect.left + window.scrollX}px`;
    
    tooltip.id = 'current-tooltip';
    document.body.appendChild(tooltip);
}

function hideTooltip() {
    const tooltip = document.getElementById('current-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Toast notification function
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-md shadow-md text-white ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 
        'bg-blue-500'
    }`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// API request helper
async function makeRequest(url, method = 'GET', data = null) {
    const token = localStorage.getItem('token');
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
        method,
        headers
    };
    
    if (data) {
        config.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, config);
        
        if (response.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
            return null;
        }
        
        const result = await response.json();
        
        if (!response.ok) {
            showToast(result.message || 'Request failed', 'error');
            return null;
        }
        
        return result;
    } catch (error) {
        console.error('API request failed:', error);
        showToast('Network error. Please try again.', 'error');
        return null;
    }
}