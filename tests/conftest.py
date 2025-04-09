import pytest
import nltk
import os

@pytest.fixture(scope='session', autouse=True)
def download_nltk_data():
    """Download necessary NLTK data before running tests."""
    packages_to_download = ['punkt', 'averaged_perceptron_tagger', 'maxent_ne_chunker', 'words']
    print('\nChecking/downloading NLTK data...')
    for pkg_id in packages_to_download:
        try:
            # Attempt to find a known resource within the package to check existence
            # This is still a bit indirect, but avoids relying on specific internal paths like punkt_tab
            if pkg_id == 'punkt':
                nltk.data.find('tokenizers/punkt/PY3/english.pickle')
            elif pkg_id == 'averaged_perceptron_tagger':
                nltk.data.find('taggers/averaged_perceptron_tagger/averaged_perceptron_tagger.pickle')
            elif pkg_id == 'maxent_ne_chunker':
                 nltk.data.find('chunkers/maxent_ne_chunker/PY3/english_ace_multiclass.pickle') # Example resource
            elif pkg_id == 'words':
                 nltk.data.find('corpora/words/en')
            print(f' - {pkg_id}: Found')
        except LookupError:
            print(f' - {pkg_id}: Not found, downloading...')
            nltk.download(pkg_id, quiet=True)
    print('NLTK data checks complete.')

# You can add other global fixtures here if needed 