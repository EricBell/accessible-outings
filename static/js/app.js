// Accessible Outings Finder - Main JavaScript

// Global app object
const AccessibleOutings = {
    // Configuration
    config: {
        apiBaseUrl: '/api',
        debounceDelay: 300,
        maxRetries: 3
    },
    
    // Utility functions
    utils: {
        // Debounce function for search inputs
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Show loading state
        showLoading: function(element) {
            if (element) {
                element.classList.add('loading');
                const spinner = element.querySelector('.spinner-border');
                if (spinner) {
                    spinner.style.display = 'inline-block';
                }
            }
        },
        
        // Hide loading state
        hideLoading: function(element) {
            if (element) {
                element.classList.remove('loading');
                const spinner = element.querySelector('.spinner-border');
                if (spinner) {
                    spinner.style.display = 'none';
                }
            }
        },
        
        // Show toast notification
        showToast: function(message, type = 'info') {
            const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
            const toast = this.createToast(message, type);
            toastContainer.appendChild(toast);
            
            // Show toast
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
            
            // Remove from DOM after hiding
            toast.addEventListener('hidden.bs.toast', () => {
                toast.remove();
            });
        },
        
        // Create toast container if it doesn't exist
        createToastContainer: function() {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
            return container;
        },
        
        // Create toast element
        createToast: function(message, type) {
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.setAttribute('role', 'alert');
            toast.setAttribute('aria-live', 'assertive');
            toast.setAttribute('aria-atomic', 'true');
            
            const iconMap = {
                success: 'fas fa-check-circle text-success',
                error: 'fas fa-exclamation-circle text-danger',
                warning: 'fas fa-exclamation-triangle text-warning',
                info: 'fas fa-info-circle text-info'
            };
            
            toast.innerHTML = `
                <div class="toast-header">
                    <i class="${iconMap[type] || iconMap.info} me-2"></i>
                    <strong class="me-auto">Notification</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            `;
            
            return toast;
        },
        
        // Format distance
        formatDistance: function(miles) {
            if (miles === null || miles === undefined) return 'Distance unknown';
            return `${miles.toFixed(1)} miles`;
        },
        
        // Format rating stars
        formatRating: function(rating, maxRating = 5) {
            if (!rating) return '';
            
            let stars = '';
            for (let i = 1; i <= maxRating; i++) {
                if (i <= rating) {
                    stars += '<i class="fas fa-star"></i>';
                } else if (i - 0.5 <= rating) {
                    stars += '<i class="fas fa-star-half-alt"></i>';
                } else {
                    stars += '<i class="far fa-star"></i>';
                }
            }
            return stars;
        },
        
        // Validate ZIP code
        validateZipCode: function(zipCode) {
            const zipPattern = /^\d{5}(-\d{4})?$/;
            return zipPattern.test(zipCode.trim());
        }
    },
    
    // API functions
    api: {
        // Generic API request function
        request: async function(endpoint, options = {}) {
            const url = `${AccessibleOutings.config.apiBaseUrl}${endpoint}`;
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                },
            };
            
            const finalOptions = { ...defaultOptions, ...options };
            
            try {
                const response = await fetch(url, finalOptions);
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || `HTTP error! status: ${response.status}`);
                }
                
                return data;
            } catch (error) {
                console.error('API request failed:', error);
                throw error;
            }
        },
        
        // Search venues
        searchVenues: async function(params) {
            const queryString = new URLSearchParams(params).toString();
            return this.request(`/search?${queryString}`);
        },
        
        // Get venue details
        getVenueDetails: async function(venueId) {
            return this.request(`/venue/${venueId}`);
        },
        
        // Add to favorites
        addFavorite: async function(venueId, notes = '', rating = null) {
            return this.request('/favorites', {
                method: 'POST',
                body: JSON.stringify({
                    venue_id: venueId,
                    notes: notes,
                    rating: rating
                })
            });
        },
        
        // Remove from favorites
        removeFavorite: async function(venueId) {
            return this.request(`/favorites/${venueId}`, {
                method: 'DELETE'
            });
        },
        
        // Geocode ZIP code
        geocodeZip: async function(zipCode) {
            return this.request(`/geocode?zip_code=${encodeURIComponent(zipCode)}`);
        }
    },
    
    // Favorites functionality
    favorites: {
        // Toggle favorite status
        toggle: async function(venueId, button) {
            const isFavorited = button.classList.contains('favorited');
            
            try {
                AccessibleOutings.utils.showLoading(button);
                
                let result;
                if (isFavorited) {
                    result = await AccessibleOutings.api.removeFavorite(venueId);
                    button.classList.remove('favorited');
                    button.innerHTML = '<i class="far fa-heart"></i>';
                    button.setAttribute('aria-label', 'Add to favorites');
                } else {
                    result = await AccessibleOutings.api.addFavorite(venueId);
                    button.classList.add('favorited');
                    button.innerHTML = '<i class="fas fa-heart"></i>';
                    button.setAttribute('aria-label', 'Remove from favorites');
                }
                
                AccessibleOutings.utils.showToast(result.message, 'success');
                
            } catch (error) {
                console.error('Error toggling favorite:', error);
                AccessibleOutings.utils.showToast('Failed to update favorites', 'error');
            } finally {
                AccessibleOutings.utils.hideLoading(button);
            }
        },
        
        // Initialize favorite buttons
        initButtons: function() {
            document.querySelectorAll('.favorite-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    const venueId = button.dataset.venueId;
                    if (venueId) {
                        this.toggle(venueId, button);
                    }
                });
            });
        }
    },
    
    // Search functionality
    search: {
        // Initialize search form
        initForm: function() {
            const searchForm = document.getElementById('searchForm');
            if (searchForm) {
                searchForm.addEventListener('submit', this.handleSubmit.bind(this));
            }
            
            // ZIP code auto-formatting
            const zipInput = document.getElementById('zip_code');
            if (zipInput) {
                zipInput.addEventListener('input', this.formatZipCode);
                zipInput.addEventListener('blur', this.validateZipCode);
            }
        },
        
        // Handle form submission
        handleSubmit: function(e) {
            const zipInput = document.getElementById('zip_code');
            const zipCode = zipInput.value.trim();
            
            if (!AccessibleOutings.utils.validateZipCode(zipCode)) {
                e.preventDefault();
                zipInput.focus();
                AccessibleOutings.utils.showToast('Please enter a valid ZIP code', 'error');
                return false;
            }
        },
        
        // Format ZIP code input
        formatZipCode: function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 5) {
                value = value.slice(0, 5) + '-' + value.slice(5, 9);
            }
            e.target.value = value;
        },
        
        // Validate ZIP code on blur
        validateZipCode: function(e) {
            const zipCode = e.target.value.trim();
            const isValid = AccessibleOutings.utils.validateZipCode(zipCode);
            
            if (zipCode && !isValid) {
                e.target.classList.add('is-invalid');
                let feedback = e.target.parentNode.querySelector('.invalid-feedback');
                if (!feedback) {
                    feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    e.target.parentNode.appendChild(feedback);
                }
                feedback.textContent = 'Please enter a valid ZIP code (e.g., 12345 or 12345-6789)';
            } else {
                e.target.classList.remove('is-invalid');
                const feedback = e.target.parentNode.querySelector('.invalid-feedback');
                if (feedback) {
                    feedback.remove();
                }
            }
        }
    },
    
    // Accessibility features
    accessibility: {
        // Initialize accessibility features
        init: function() {
            this.addSkipLink();
            this.enhanceKeyboardNavigation();
            this.addAriaLabels();
        },
        
        // Add skip to main content link
        addSkipLink: function() {
            if (!document.querySelector('.skip-link')) {
                const skipLink = document.createElement('a');
                skipLink.href = '#main';
                skipLink.className = 'skip-link';
                skipLink.textContent = 'Skip to main content';
                document.body.insertBefore(skipLink, document.body.firstChild);
            }
        },
        
        // Enhance keyboard navigation
        enhanceKeyboardNavigation: function() {
            // Add keyboard support for card clicks
            document.querySelectorAll('.venue-card, .category-card').forEach(card => {
                if (!card.hasAttribute('tabindex')) {
                    card.setAttribute('tabindex', '0');
                    card.setAttribute('role', 'button');
                    
                    card.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            const link = card.querySelector('a');
                            if (link) {
                                link.click();
                            }
                        }
                    });
                }
            });
        },
        
        // Add missing ARIA labels
        addAriaLabels: function() {
            // Add labels to buttons without text
            document.querySelectorAll('button:not([aria-label])').forEach(button => {
                const icon = button.querySelector('i');
                if (icon && !button.textContent.trim()) {
                    if (icon.classList.contains('fa-heart')) {
                        button.setAttribute('aria-label', 'Add to favorites');
                    } else if (icon.classList.contains('fa-search')) {
                        button.setAttribute('aria-label', 'Search');
                    }
                }
            });
        }
    },
    
    // Initialize the application
    init: function() {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('Accessible Outings Finder initialized');
            
            // Initialize modules
            this.accessibility.init();
            this.search.initForm();
            this.favorites.initButtons();
            
            // Initialize tooltips
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
            
            // Initialize popovers
            const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
            popoverTriggerList.map(function (popoverTriggerEl) {
                return new bootstrap.Popover(popoverTriggerEl);
            });
            
            // Add main content ID for skip link
            const main = document.querySelector('main');
            if (main && !main.id) {
                main.id = 'main';
            }
        });
    }
};

// Initialize the application
AccessibleOutings.init();

// Export for use in other scripts
window.AccessibleOutings = AccessibleOutings;
