from setuptools import setup, find_packages

setup(
    name="cognisgraph",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "networkx>=3.0",
        "numpy>=1.23.5",
        "pandas>=1.3.0",
        "pydantic>=2.5.0",
        "rich>=13.7.0",
        "matplotlib>=3.8.0",
        "pyvis>=0.3.2",
        "graphviz>=0.20.1",
        "scikit-learn>=1.0.0",
        "plotly>=5.13.0",
        "streamlit>=1.44.0",
        "torch>=2.1.0",
        "protobuf>=3.20.3",
        "sentence-transformers>=2.2.2",
        "nltk>=3.6",
        "spacy>=3.7.2",
        "langgraph>=0.0.10",
        "watchdog>=3.0.0",
        "PyPDF2>=3.0.0",
        "pypdf>=5.4.0",
    ],
    python_requires=">=3.8",
    author="bharti26",
    author_email="bhartigoel0812@gmail.com",
    description="A knowledge graph system with XAI features",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/bharti26/cognisgraph",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 