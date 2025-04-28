 Changelog

## [1.2.0] - [2025-04-29]
### Fixed
- **Time Signature Logic**: Corrected the metronome interval calculation to accurately reflect the selected time signature denominator. The BPM value now consistently represents quarter notes per minute (e.g., 120 BPM in 4/8 time is twice as fast as 120 BPM in 4/4 time).

### Documentation
- **Installation Instructions**: Added note about using PYGAME_DETECT_AVX2=1 environment variable when installing pygame for better performance on AVX2-capable systems.
## [1.1.0] - [2025-03-19]
### Enhancements and Fixes
- **Error Handling**: Changed error handling in the audio initialization section to log errors to the console instead of showing a dialog.
- **Constants for Magic Numbers**: Introduced constants for BPM upper limit and time signature limits to improve code readability and maintainability.
- **Thread Management**: Removed unnecessary locking mechanisms in the [start_metronome] and [stop_metronome] methods.
- **Comment Alignment**: Adjusted the alignment of comments for better clarity and readability.
- **Unused Imports**: Removed any unused imports to clean up the code.
- **General Code Cleanup**: Improved the structure and readability of the code by organizing imports and ensuring consistent formatting.