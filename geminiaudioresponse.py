import cv2
import time
import speech_recognition as sr
import google.generativeai as genai
import pyttsx3  # For faster speech synthesis
# from playsound import playsound

# Configure Gemini API
genai.configure(api_key="Your API Key")
# Function to upload image to Gemini
def upload_to_gemini(image_path):
    with open(image_path, "rb") as image_file:
        file = genai.upload_file(image_path, mime_type="image/jpeg")
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file

# Function to wait until Gemini file is active
def wait_for_files_active(files):
    print("Waiting for file processing...")
    for file in files:
        gemini_file = genai.get_file(file.name)
        while gemini_file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(5)
            gemini_file = genai.get_file(file.name)
        if gemini_file.state.name != "ACTIVE":
            raise Exception(f"File {gemini_file.name} failed to process")
    print("\nAll files ready.")

# Function to interact with Gemini AI
def get_image_details(image_path=None, user_prompt=None):
    if image_path:
        # Upload image to Gemini
        uploaded_file = upload_to_gemini(image_path)

        # Wait for file to be processed
        wait_for_files_active([uploaded_file])

        # Initialize chat with the uploaded file
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        chat_session = model.start_chat(
            history=[{"role": "user", "parts": [uploaded_file]}]
        )
    else:
        # Initialize chat without an image
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        chat_session = model.start_chat()

    # Use a default or user-provided prompt
    prompt = user_prompt if user_prompt else "Describe the contents of this image."
    response = chat_session.send_message(prompt)
    
    # Limit response to 50 words
    response_text = response.text
    words = response_text.split()
    limited_response = " ".join(words[:50])  # Get only the first 50 words
    return limited_response

# Function to capture image from webcam
def capture_image():
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Could not open camera.")
        return None

    print("Press 'c' to capture the image.")
    while True:
        ret, frame = camera.read()
        if not ret:
            print("Failed to grab frame.")
            break

        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1)
        if key == ord('c'):
            image_path = "captured_image.jpg"
            cv2.imwrite(image_path, frame)
            print("Image captured and saved.")
            break

    camera.release()
    cv2.destroyAllWindows()
    return image_path

# Function to convert speech to text
def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for your command...")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio)
            print("You said: " + command)
            return command.lower()  # Convert command to lowercase
        except sr.UnknownValueError:
            print("Sorry, I could not understand your voice.")
        except sr.WaitTimeoutError:
            print("No voice input detected.")
        return ""  # Return empty string instead of None

# Function to convert text to speech using pyttsx3 (for faster response)
def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# Function to handle image and prompt logic
def handle_image_and_prompt():
    image_path = capture_image()
    if image_path:
        print("What would you like to know about the image? Please speak your query.")
        time.sleep(5)  # Wait for user to think about their query
        user_query = speech_to_text()
        if user_query:
            return image_path, user_query
        else:
            return image_path, "Describe the contents of this image."
    return None, None

# Main function
def main():
    while True:
        print("Say 'capture' to take a picture, 'exit' to quit, or anything else for a simple response.")
        command = speech_to_text()

        # Keep asking for input until a valid command is given
        while not command:
            print("I didn't hear anything. Please say something.")
            text_to_speech("I didn't hear anything. Please say something.")
            command = speech_to_text()

        if command == "exit":
            print("Exiting the program.")
            break

        elif command == "capture":
            image_path, user_query = handle_image_and_prompt()
            if image_path:
                try:
                    print("Sending image and your query to Gemini AI...")
                    response = get_image_details(image_path, user_prompt=user_query)
                    print("AI Response: ", response)
                    text_to_speech(response)
                except Exception as e:
                    print("Error processing image: ", str(e))
                    text_to_speech("Sorry, there was an error processing the image.")

        else:
            print("You said:", command)
            try:
                response = get_image_details(user_prompt=command)  # Send the command as user prompt
                print("AI Response: ", response)
                text_to_speech(response)  # Fast speech response
            except Exception as e:
                print("Error processing request: ", str(e))
                text_to_speech("Sorry, there was an error processing your request.")

if __name__ == "__main__":
    main()