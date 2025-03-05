// Theme switcher for Mermaid diagrams
document.addEventListener('DOMContentLoaded', function() {
    // Function to apply theme to Mermaid based on current document theme
    function applyMermaidTheme() {
        const isDarkTheme = document.body.getAttribute('data-md-color-scheme') === 'slate';
        
        // Find all Mermaid diagrams
        document.querySelectorAll('.mermaid').forEach(function(diagram) {
            // Set a data attribute we can target with CSS
            diagram.setAttribute('data-theme', isDarkTheme ? 'dark' : 'light');
            
            // If mermaid has already been initialized, re-render with the new theme
            if (typeof mermaid !== 'undefined' && diagram.getAttribute('data-processed') === 'true') {
                try {
                    const graphCode = diagram.textContent;
                    mermaid.render(
                        'mermaid-' + Math.random().toString(36).substr(2, 9),
                        graphCode,
                        function(svgCode) {
                            diagram.innerHTML = svgCode;
                        },
                        diagram
                    );
                } catch (error) {
                    console.error('Error re-rendering mermaid diagram:', error);
                }
            }
        });
    }
    
    // Apply theme on initial load
    setTimeout(applyMermaidTheme, 500);
    
    // Watch for theme changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'data-md-color-scheme') {
                applyMermaidTheme();
            }
        });
    });
    
    // Start observing the document body for theme change
    observer.observe(document.body, { 
        attributes: true,
        attributeFilter: ['data-md-color-scheme']
    });
    
    // Also handle theme toggle button click
    document.querySelectorAll('.md-header__button[data-md-toggle="palette"]').forEach(function(button) {
        button.addEventListener('click', function() {
            // Give the theme a moment to change before updating diagrams
            setTimeout(applyMermaidTheme, 200);
        });
    });
});