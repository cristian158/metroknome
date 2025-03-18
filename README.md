# MetroKnome

MetroKnome is a GTK-based digital metronome application designed for musicians, music students, and professionals. It offers precise timing and a variety of features to enhance your practice and performance sessions.

Version: 1.1

## Features

- Adjustable BPM (Beats Per Minute) from 1 to 777
- Volume control from 0 to 1
- Customizable time signatures (e.g. 4/4, 3/8, 7/16)
- Visual beat indicator with accent colors
- Start/Stop functionality
- Error handling for invalid inputs

## Requirements

- Python 3.6+
- GTK 3.0
- Pygame

## Installation

1. Install system dependencies:
```bash
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```
2. Install Python packages:
```bash
pip install pygame PyGObject
```
3. Clone the repository:
```bash
git clone https://github.com/cristian158/metroknome.git
cd metroknome
```
4. Run the application:
```bash
python MetroKnome.py
```

## Usage

1. Launch MetroKnome
2. Set your desired tempo (1-777 BPM)
3. Choose your time signature (e.g. 4/4, 3/8)
4. Adjust volume (0.0-1.0)
5. Press the play button to start the metronome
6. The visual indicator will show beat accents in green

## Contributing

We welcome contributions to MetroKnome! If you'd like to contribute, please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgements

- [PyGObject](https://pygobject.readthedocs.io/) for the GTK bindings.
- [Pygame](https://www.pygame.org/) for audio playback.
- All our contributors and users who have provided valuable feedback

## Contact

For support or inquiries, please contact us at support@metroknome.com or visit our [website](https://metroknome.com).
