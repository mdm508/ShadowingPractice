import os
import whisper
from pydub import AudioSegment
from pydub.silence import split_on_silence
from jinja2 import Template


# Function to split mp3 into phrases based on silence
def split_audio_by_phrases(mp3_file, output_folder, silence_thresh=-40, min_silence_len=500, phrase_padding=100):
    audio = AudioSegment.from_mp3(mp3_file)

    # Split on silence based on threshold and minimum silence length
    audio_chunks = split_on_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Export each phrase as a separate mp3
    chunk_files = []
    for i, chunk in enumerate(audio_chunks):
        # Add padding around phrases
        chunk = AudioSegment.silent(duration=phrase_padding) + chunk + AudioSegment.silent(duration=phrase_padding)
        chunk_file = os.path.join(output_folder, f"phrase_{i}.mp3")
        chunk.export(chunk_file, format="mp3")
        chunk_files.append(chunk_file)

    return chunk_files


# Function to transcribe each audio segment
def transcribe_audio(phrase_files):
    model = whisper.load_model("large")  # You can use "small" or "medium" for more accurate results
    transcriptions = []
    for file in phrase_files:
        result = model.transcribe(file, language="zh")
        transcriptions.append(result['text'])
    return transcriptions


def generate_css(output_folder):
    css_content = '''
/* styles.css */
/* styles.css */

body {
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
    background-color: #f5f5f5;
    display: flex;
    height: 100vh;
}

.header {
    position: sticky;
    top: 0;
    width: 50%; /* Adjust width as needed */
    background: #fff;
    border-right: 1px solid #ddd;
    padding: 20px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    z-index: 10;
    display: flex;
    flex-direction: column;
}

#characters-text {
    font-size: 30pt;
    margin-top: 5pt;
    align-text: center;
    white-space: pre-wrap; /* This preserves line breaks and spaces */
}

.container {
    flex: 1;
    overflow: auto;
    padding: 20px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
}

#player-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    background-color: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    overflow-y: auto;
}

#track-list {
    margin-top: 20px;
}

.track-item {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
    cursor: pointer;
    padding: 10px;
    border-radius: 4px;
    background-color: #f9f9f9;
    font-size: 14px;
}

.track-item.current {
    background-color: #007bff;
    color: #fff;
}

.track-button {
    margin-left: 10px;
    background-color: #007bff;
    color: #fff;
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
}

.track-button.loop {
    background-color: #28a745;
}

.track-button.play {
}

audio {
    display: block;
    margin: 10px auto;
}

.play-button {
    margin-right: 10px;
}
    '''
    css_path = os.path.join(output_folder, 'styles.css')

    with open(css_path, "w", encoding="utf-8") as css_file:
        css_file.write(css_content)

    return css_path



def generate_js(output_folder, phrase_files):
    js_template = '''
    // scripts.js

    document.addEventListener('DOMContentLoaded', () => {
        const audioPlayer = document.getElementById('audio-player');
        const trackList = document.getElementById('track-list');
        const loopSwitch = document.getElementById('loop-switch');

        const tracks = [
            {% for file in phrase_files %}
                { src: '{{ file | e }}', title: 'Track {{ loop.index }}' },
            {% endfor %}
        ];

        let currentTrackIndex = 0;
        let looping = false;

        function loadTrackList() {
            tracks.forEach((track, index) => {
                const trackItem = document.createElement('div');
                trackItem.className = 'track-item';
                trackItem.innerHTML = `
                    <button class="track-button play play-button" data-index="${index}">Play</button>
                    ${track.title}
                `;
                trackItem.dataset.index = index;
                trackList.appendChild(trackItem);
            });

            trackList.addEventListener('click', (event) => {
                const button = event.target;
                if (button.classList.contains('play')) {
                    playTrack(parseInt(button.dataset.index));
                }
            });

            loopSwitch.addEventListener('click', () => {
                looping = !looping;
                loopSwitch.textContent = looping ? 'Loop On' : 'Loop Off';
                audioPlayer.loop = looping;
            });
        }

        function playTrack(index) {
            if (index >= 0 && index < tracks.length) {
                currentTrackIndex = index;
                audioPlayer.src = tracks[index].src;
                audioPlayer.play();
                updateTrackList();
            }
        }

        function updateTrackList() {
            document.querySelectorAll('.track-item').forEach((item, index) => {
                item.classList.toggle('current', index === currentTrackIndex);
            });
            const currentItem = document.querySelector('.track-item.current');
            if (currentItem) {
                currentItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }

        document.addEventListener('keydown', (event) => {
            if (event.key === 'ArrowRight') {
                playTrack((currentTrackIndex + 1) % tracks.length);
            } else if (event.key === 'ArrowLeft') {
                playTrack((currentTrackIndex - 1 + tracks.length) % tracks.length);
            } else if (event.key === ' ') {
                event.preventDefault(); // Prevents scrolling when pressing the space bar
                if (audioPlayer.paused) {
                    audioPlayer.play();
                } else {
                    audioPlayer.pause();
                }
            } else if (event.key === 'l') {
                loopSwitch.click();
            }
        });

        loadTrackList();
        playTrack(currentTrackIndex);
    });
    '''
    template = Template(js_template)
    js_content = template.render(phrase_files=phrase_files)

    js_path = os.path.join(output_folder, 'scripts.js')
    with open(js_path, "w", encoding="utf-8") as js_file:
        js_file.write(js_content)

    return js_path



def generate_html(phrase_files, transcriptions, output_folder, output_html, characters_text):
    template = Template('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="styles.css">
        <title>Audio Player</title>
    </head>
    <body>
        <div class="header">
            <audio id="audio-player" controls></audio>
            <button id="loop-switch" class="track-button loop">Loop Off</button>
            <div id="characters-text">{{ characters_text | e }}</div>
        </div>
        <div class="container">
            <div id="player-container">
                <div id="track-list">
                    {% for file, transcription in zipped %}
                        <div class="track-item" data-src="{{ file }}">{{ transcription }}
                            <button class="track-button play play-button" data-index="{{ loop.index0 }}">Play</button>
                        </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        <script src="scripts.js"></script>
    </body>
    </html>
    ''')

    # Adjust paths for HTML to be relative to the folder
    relative_paths = [os.path.basename(file) for file in phrase_files]

    # Use the zip function to pair files and transcriptions
    zipped = zip(relative_paths, transcriptions)

    # Generate CSS and JavaScript files
    generate_css(output_folder)
    generate_js(output_folder, relative_paths)

    # Render the HTML template with zipped values and characters text
    html_content = template.render(zipped=zipped, phrase_files=relative_paths, characters_text=characters_text)

    # Write the HTML to file in the output folder
    html_output_path = os.path.join(output_folder, output_html)
    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_output_path



def main(mp3_file, characters_file):
    # Get the base name of the MP3 file (without extension)
    base_name = os.path.splitext(os.path.basename(mp3_file))[0]

    # Define output folder and files
    output_folder = base_name
    output_html = f"{base_name}.html"

    # Split audio into phrases
    phrase_files = split_audio_by_phrases(mp3_file, output_folder)

    # Transcribe each phrase
    transcriptions = transcribe_audio(phrase_files)

    # Read characters text
    with open(characters_file, "r", encoding="utf-8") as f:
        characters_text = f.read()

    # Generate HTML
    generate_html(phrase_files, transcriptions, output_folder, output_html, characters_text)

    print(f"HTML file generated: {os.path.abspath(os.path.join(output_folder, output_html))}")





if __name__ == "__main__":
    base_name = "01-02"
    mp3_file = f"{base_name}.mp3" #replace with your mp3 file path
    characters_file = f"{base_name}.txt"  # Replace with your characters file path
    main(mp3_file, characters_file)
