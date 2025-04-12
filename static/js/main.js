document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const findPathBtn = document.getElementById('find-path-btn');
    const toggleDijkstra = document.getElementById('toggle-dijkstra');
    const toggleAstar = document.getElementById('toggle-astar');
    const tabDijkstra = document.getElementById('tab-dijkstra');
    const tabAstar = document.getElementById('tab-astar');
    const loadingElement = document.getElementById('loading');
    const pathInfo = document.getElementById('path-info');
    const mapElement = document.getElementById('map');
    const distanceValue = document.getElementById('distance-value');
    const algorithmValue = document.getElementById('algorithm-value');
    const nodesValue = document.getElementById('nodes-value');
    
    // Current algorithm state
    let currentAlgorithm = 'dijkstra';
    let lastCalculatedAlgorithm = null;
    
    // Store path data for comparison
    let pathResults = {
        dijkstra: null,
        astar: null
    };
    
    // Event listeners
    if (findPathBtn) {
        findPathBtn.addEventListener('click', calculatePath);
        
        // Add pulse animation to button to draw attention
        setTimeout(() => {
            findPathBtn.classList.add('is-pulse');
            setTimeout(() => {
                findPathBtn.classList.remove('is-pulse');
            }, 2000);
        }, 1000);
    }
    
    // Algorithm selection listeners
    if (toggleDijkstra) {
        toggleDijkstra.addEventListener('click', () => {
            setActiveAlgorithm('dijkstra');
        });
    }
    
    if (toggleAstar) {
        toggleAstar.addEventListener('click', () => {
            setActiveAlgorithm('astar');
        });
    }
    
    if (tabDijkstra) {
        tabDijkstra.addEventListener('click', () => {
            setActiveAlgorithm('dijkstra');
        });
    }
    
    if (tabAstar) {
        tabAstar.addEventListener('click', () => {
            setActiveAlgorithm('astar');
        });
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // Set active algorithm
    function setActiveAlgorithm(algorithm) {
        currentAlgorithm = algorithm;
        
        // Update toggle UI
        if (toggleDijkstra && toggleAstar) {
            if (algorithm === 'dijkstra') {
                toggleDijkstra.querySelector('.algorithm-toggle-inner').classList.add('is-active');
                toggleAstar.querySelector('.algorithm-toggle-inner').classList.remove('is-active');
            } else {
                toggleDijkstra.querySelector('.algorithm-toggle-inner').classList.remove('is-active');
                toggleAstar.querySelector('.algorithm-toggle-inner').classList.add('is-active');
            }
        }
        
        // Update tab UI
        if (tabDijkstra && tabAstar) {
            if (algorithm === 'dijkstra') {
                tabDijkstra.classList.add('is-active');
                tabAstar.classList.remove('is-active');
            } else {
                tabDijkstra.classList.remove('is-active');
                tabAstar.classList.add('is-active');
            }
        }
        
        // Update button color based on algorithm
        if (findPathBtn) {
            if (algorithm === 'dijkstra') {
                findPathBtn.classList.remove('is-danger');
                findPathBtn.classList.add('is-primary');
            } else {
                findPathBtn.classList.remove('is-primary');
                findPathBtn.classList.add('is-danger');
            }
        }
    }
    
    // Calculate path using selected algorithm
    function calculatePath() {
        // Show loading
        if (loadingElement) loadingElement.classList.remove('is-hidden');
        if (pathInfo) pathInfo.classList.add('is-hidden');
        
        // If we already calculated this algorithm, show the existing result
        if (pathResults[currentAlgorithm] && currentAlgorithm === lastCalculatedAlgorithm) {
            showPathResult(pathResults[currentAlgorithm]);
            return;
        }
        
        // Reset UI
        if (mapElement) {
            mapElement.innerHTML = '';
            
            // Show calculating message with animation
            const loadingMessage = document.createElement('div');
            loadingMessage.className = 'has-text-centered initial-map-message';
            loadingMessage.innerHTML = `
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">
                        <p class="is-size-5 mb-2">Calculating optimal route with</p>
                        <p class="is-size-4 has-text-weight-bold">${currentAlgorithm === 'dijkstra' ? 'Dijkstra\'s Algorithm' : 'A* Algorithm'}</p>
                    </div>
                </div>
            `;
            mapElement.appendChild(loadingMessage);
        }
        
        // Add subtle animation to button
        if (findPathBtn) {
            findPathBtn.classList.add('is-loading');
        }
        
        // Send request
        fetch('/find_path', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                algorithm: currentAlgorithm
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Server error');
                });
            }
            return response.json();
        })
        .then(data => {
            // Store result for this algorithm
            pathResults[currentAlgorithm] = data;
            lastCalculatedAlgorithm = currentAlgorithm;
            
            // Display the result
            showPathResult(data);
        })
        .catch(error => {
            // Hide loading
            if (loadingElement) loadingElement.classList.add('is-hidden');
            if (findPathBtn) findPathBtn.classList.remove('is-loading');
            
            // Show error message
            showError(error.message);
            
            // Reset map
            if (mapElement) {
                mapElement.innerHTML = `
                    <div class="has-text-centered initial-map-message">
                        <div class="notification is-danger is-light">
                            <p class="is-size-4 mb-3"><i class="fas fa-exclamation-triangle"></i></p>
                            <p class="is-size-5">Error calculating path</p>
                            <p class="is-size-6 mt-2">${error.message}</p>
                        </div>
                    </div>
                `;
            }
        });
    }
    
    // Show path result
    function showPathResult(data) {
        // Hide loading
        if (loadingElement) loadingElement.classList.add('is-hidden');
        if (findPathBtn) findPathBtn.classList.remove('is-loading');
        
        // Display map
        if (mapElement) {
            mapElement.innerHTML = data.map_html;
            
            // Fix potential CSS issues with Leaflet map
            const mapStyleFix = document.createElement('style');
            mapStyleFix.innerHTML = `
                .leaflet-container {
                    height: 100%;
                    width: 100%;
                }
            `;
            mapElement.appendChild(mapStyleFix);
        }
        
        // Update path info
        if (distanceValue) distanceValue.textContent = data.distance;
        if (algorithmValue) algorithmValue.textContent = data.algorithm;
        if (nodesValue) nodesValue.textContent = data.nodes;
        
        // Show path info with animation
        if (pathInfo) {
            pathInfo.classList.remove('is-hidden');
            pathInfo.style.opacity = '0';
            setTimeout(() => {
                pathInfo.style.opacity = '1';
            }, 10);
        }
        
        // Show success animation on button
        if (findPathBtn) {
            const originalButtonClass = findPathBtn.className;
            const originalButtonText = findPathBtn.innerHTML;
            
            findPathBtn.className = 'button is-success is-medium is-fullwidth';
            findPathBtn.innerHTML = `
                <span class="icon">
                    <i class="fas fa-check"></i>
                </span>
                <span>Path Found</span>
            `;
            
            // Restore button after animation
            setTimeout(() => {
                findPathBtn.className = originalButtonClass;
                findPathBtn.innerHTML = originalButtonText;
            }, 1500);
        }
    }
    
    // Function to show errors
    function showError(message) {
        const notification = document.createElement('div');
        notification.className = 'notification is-danger is-light animate__animated animate__fadeIn';
        
        const deleteButton = document.createElement('button');
        deleteButton.className = 'delete';
        deleteButton.addEventListener('click', () => {
            notification.remove();
        });
        
        notification.appendChild(deleteButton);
        notification.appendChild(document.createTextNode(message));
        
        // Insert in an appropriate location
        if (findPathBtn && findPathBtn.parentNode) {
            findPathBtn.parentNode.insertAdjacentElement('afterend', notification);
        } else {
            const container = document.querySelector('.container');
            if (container) {
                container.insertAdjacentElement('afterbegin', notification);
            }
        }
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('animate__fadeOut');
            setTimeout(() => {
                notification.remove();
            }, 1000);
        }, 5000);
    }
    
    // Trigger path calculation after short delay
    setTimeout(() => {
        if (findPathBtn) findPathBtn.click();
    }, 800);
});
