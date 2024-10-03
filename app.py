from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import tempfile
import json

TWILIO_ACCOUNT_SID = 'AC6f3cf799933749b0aa8431cd8a95ce51'
TWILIO_AUTH_TOKEN = 'c1a9ebb390e2fc46213aab60d90ad314'

app = Flask(__name__)

# Directory for storing media files
MEDIA_FOLDER = 'media_files'
if not os.path.exists(MEDIA_FOLDER):
    os.makedirs(MEDIA_FOLDER)

@app.route("/media/<filename>", methods=["GET"])
def serve_media(filename):
    """Serve the PDF file that was stored"""
    return send_from_directory(MEDIA_FOLDER, filename)

@app.route("/whatsapp", methods=["GET", "POST"])
def reply_whatsapp():
    pdf_url = request.values.get('MediaUrl0')
    response = None

    try:
        num_media = int(request.values.get("NumMedia", 0))
    except (ValueError, TypeError):
        print("Invalid request: invalid or missing NumMedia parameter")
        return "Invalid request: invalid or missing NumMedia parameter", 400

    response = MessagingResponse()

    if num_media == 0:
        print("No media file received.")
        msg = response.message("Send us an image or any media file!")
    else:
        media_url = pdf_url
        media_content_type = request.values.get("MediaContentType0")

        print(f"Received media with URL: {media_url}")

        # Check if the media is a PDF
        if media_content_type == 'application/pdf':
            try:
                # Download the PDF using Twilio authentication
                media_response = requests.get(
                    media_url,
                    auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                )

                if media_response.status_code == 200:
                    # Save the PDF file to the media folder
                    media_filename = "downloaded_file.pdf"
                    media_path = os.path.join(MEDIA_FOLDER, media_filename)

                    with open(media_path, 'wb') as f:
                        f.write(media_response.content)

                    print(f"Downloaded PDF saved at: {media_path}")

                    # Notify the user that the PDF was successfully stored
                    msg = response.message("Your PDF has been successfully downloaded and stored.")

                    # Generate a public URL for the PDF and send it back to the user
                    file_url = request.host_url + f"media/{media_filename}"
                    msg = response.message(f"Here is the PDF you uploaded: {file_url}")
                    msg.media(file_url)

                    # Send the PDF via email
                    # Call this after successfully downloading the PDF
                    file_path = media_path
                    send_email_with_attachment(file_path)




                else:
                    print(f"Failed to download media from {media_url}. Status code: {media_response.status_code}")
                    msg = response.message("There was an issue retrieving your PDF. Please try again.")

            except Exception as e:
                print(f"An error occurred while processing the PDF: {e}")
                msg = response.message("There was an error processing your PDF.")
        else:
            msg = response.message("Please send a valid PDF file!")

    return str(response)

def send_email_with_attachment(file_path):
    # The email service URL
    email_url = 'https://eezimeds-email-service.azurewebsites.net/sendEmail/sendAttachment'

    # The form data for the email
    data = {
        'to': 'tafaramutswe@gmail.com',
        'subject': 'Your PDF File',
        'body': 'Please find the attached PDF file you uploaded.'
    }


    files = {
        'file': ('downloaded_file.pdf', open(file_path, 'rb'), 'application/pdf')
    }

    headers = {
        'Content-Type': 'multipart/form-data'  # Adjust as necessary based on the API documentation
    }

    response = requests.post(email_url, data=data, files=files, headers=headers)

    # Handle the response

    if response.status_code == 201:
        print("Email sent successfully!")


    else:
        print(f"Failed to send email. Status code: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    app.run(debug=True)
