// Mermaid initialization for Sphinx
document.addEventListener('DOMContentLoaded', function() {
    // Get theme from document
    var isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark';
    
    // Wait for any Sphinx theme initialization to complete
    setTimeout(function() {
        if (window.mermaid) {
            // Initialize with chosen theme
            window.mermaid.initialize({ 
                startOnLoad: true,
                theme: isDarkTheme ? 'dark' : 'default',
                flowchart: { useMaxWidth: true },
                sequence: { useMaxWidth: true },
                journey: { useMaxWidth: true },
                gantt: { useMaxWidth: true },
                securityLevel: 'loose'
            });
            
            // Process diagrams
            document.querySelectorAll('pre.mermaid').forEach(function(el) {
                try {
                    // Create a wrapper div with mermaid class
                    var wrapper = document.createElement('div');
                    wrapper.className = 'mermaid';
                    wrapper.innerHTML = el.textContent;
                    
                    // Replace the pre element with the mermaid div
                    el.parentNode.replaceChild(wrapper, el);
                    
                    // Initialize this specific diagram
                    window.mermaid.init(undefined, wrapper);
                } catch (error) {
                    console.error('Mermaid diagram processing error:', error);
                }
            });
        }
    }, 500);
});