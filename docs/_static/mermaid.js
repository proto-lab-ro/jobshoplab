// Load Mermaid directly from CDN
document.addEventListener('DOMContentLoaded', function() {
    // Create script element
    var script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
    script.async = true;
    script.onload = function() {
        // Initialize Mermaid once loaded
        if (typeof mermaid !== 'undefined') {
            mermaid.initialize({
                startOnLoad: true,
                theme: 'default',
                flowchart: {
                    htmlLabels: true,
                    useMaxWidth: true
                },
                securityLevel: 'loose'
            });
            
            // Force initialize any mermaid diagrams
            document.querySelectorAll('.mermaid').forEach(function(element) {
                try {
                    mermaid.init(undefined, element);
                } catch (e) {
                    console.error("Mermaid initialization error:", e);
                    element.innerHTML = "<div class='mermaid-error'>Diagram rendering error</div>";
                }
            });
        }
    };
    
    // Add script to document
    document.head.appendChild(script);
});