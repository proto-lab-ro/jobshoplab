import os
import sys

sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------
project = "JobShopLab"
copyright = "2025, Jonathan Hoss, Felix Schelling, Noah Klarmann"
author = "Jonathan Hoss, Felix Schelling, Noah Klarmann"
release = "0.0.1"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.todo",
    "sphinx_immaterial",
    "sphinxcontrib.mermaid",
]
mermaid_version = "9.1.3"
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- HTML output options ---------------------------------------------------
html_theme = "sphinx_immaterial"
html_static_path = ["_static"]
html_css_files = ["custom.css", "mermaid-dark.css", "mermaid-light.css"]
html_title = "JobShopLab Documentation"

# Theme options
html_theme_options = {
    "repo_url": "https://inf-git.fh-rosenheim.de/proto-lab-2.0/jobshoplab",
    "repo_name": "JobShopLab",
    "icon": {
        "repo": "fontawesome/brands/gitlab",
        "edit": "material/file-edit-outline",
    },
    "features": [
        "navigation.expand",
        "navigation.sections",
        "navigation.top",
        "navigation.footer",
        "search.share",
        "search.suggest",
        "toc.follow",
        "toc.sticky",
        "content.tabs.link",
        "content.code.copy",
        "content.action.edit",
        "content.action.view",
        "content.tooltips",
        "announce.dismiss",
    ],
    "palette": [
        {
            "media": "(prefers-color-scheme: light)",
            "scheme": "default",
            "primary": "deep-orange",
            "accent": "orange",
            "toggle": {"icon": "material/brightness-7", "name": "Switch to dark mode"},
        },
        {
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "primary": "deep-orange",
            "accent": "orange",
            "toggle": {"icon": "material/brightness-4", "name": "Switch to light mode"},
        },
    ],
    "toc_title_is_page_title": True,
    "navigation_with_keys": True,
}

# -- AutoDoc configuration -------------------------------------------------
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
autodoc_member_order = "bysource"
autodoc_class_signature = "separated"

# -- Napoleon configuration -----------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_attr_annotations = True

# -- Intersphinx configuration -------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "gym": ("https://gymnasium.farama.org/", None),
}

# -- Extension configuration ---------------------------------------------
todo_include_todos = True
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 2

# -- Object description options -----------------------------------------
object_description_options = [
    ("py:.*", dict(wrap_signatures_with_css=True)),
    ("cpp:.*", dict(clang_format_style={"BasedOnStyle": "LLVM"})),
]

# -- Search configuration ----------------------------------------------
html_search_language = "en"
html_search_options = {"type": "default"}
html_use_index = True
html_domain_indices = True

# -- Other settings -------------------------------------------------
add_module_names = False
html_show_sourcelink = True
html_copy_source = False
html_last_updated_fmt = "%b %d, %Y"
pygments_style = "friendly"
nitpicky = True

# Configure mermaid options
mermaid_version = "10.6.1"  # Specify exact version
mermaid_init_js = ""  # Using custom initialization in layout.html
mermaid_output_format = "svg"
mermaid_params = [
    "securityLevel=loose",
    "startOnLoad=true"
]

# -- Additional static files -----------------------------------------
html_js_files = [
    "custom.js",
    "https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js",
    "theme-switcher.js"
]
