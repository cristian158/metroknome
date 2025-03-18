 Changelog

## [Unreleased]
### Enhancements and Fixes
- **Error Handling**: Changed error handling in the audio initialization section to log errors to the console instead of showing a dialog.
- **Constants for Magic Numbers**: Introduced constants for BPM upper limit and time signature limits to improve code readability and maintainability.
- **Thread Management**: Removed unnecessary locking mechanisms in the [start_metronome](cci:1://file:///home/spweedy/TESTS/Metro-knome/MetroKnome.py:148:4-158:37) and [stop_metronome](cci:1://file:///home/spweedy/TESTS/Metro-knome/MetroKnome.py:160:4-165:64) methods.
- **Comment Alignment**: Adjusted the alignment of comments for better clarity and readability.
- **Unused Imports**: Removed any unused imports to clean up the code.
- **General Code Cleanup**: Improved the structure and readability of the code by organizing imports and ensuring consistent formatting.