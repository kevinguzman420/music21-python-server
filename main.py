from flask_cors import CORS
from flask import Flask, request, jsonify
import os
from music21 import midi, instrument, note, stream
import tempfile
import base64

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

# Create the instrument object outside the function
selected_instrument = None


@app.route("/api/test")
def test():
    return jsonify({"message": "Working fine"})


@app.route("/api/generate_music", methods=["POST"])
def generate_music():
    data = request.json
    text = data.get("text")
    instrument_name = data.get("instrument", "Piano")

    print(f"Received text: {text}")
    print(f"Requested instrument: {instrument_name}")

    # Create a music21 stream and add notes based on the text
    s = stream.Stream()

    try:
        # Ensure the instrument name is in the correct format
        instrument_class = getattr(instrument, instrument_name.replace(" ", ""), None)
        if instrument_class is None:
            return jsonify({"error": f"Instrument {instrument_name} not found"}), 400
        inst = instrument_class()
        print(f"Using instrument: {inst}")
    except AttributeError:
        return jsonify({"error": f"Instrument {instrument_name} not found"}), 400

    s.append(inst)

    for char in text:
        if char.isalpha():
            pitch = note.Note()
            pitch.name = chr((ord(char.lower()) - 97) % 7 + 65)
            s.append(pitch)
        elif char.isspace():
            s.append(note.Rest())

    # Save the stream to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".midi") as temp_file:
        mf = midi.translate.music21ObjectToMidiFile(s)
        mf.open(temp_file.name, "wb")
        mf.write()
        mf.close()
        temp_file_path = temp_file.name

    # Read the MIDI file and encode it to base64
    with open(temp_file_path, "rb") as midi_file:
        encoded_midi = base64.b64encode(midi_file.read()).decode("utf-8")

    # Delete the temporary file
    os.unlink(temp_file_path)

    return jsonify({"midi_data": encoded_midi})


if __name__ == "__main__":
    app.run(debug=True)
