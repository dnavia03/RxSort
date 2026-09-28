# RxSort

RxSort is an automated pill identification and sorting system developed as a Senior Design project. The goal of the system is to use computer vision, artificial intelligence, and embedded hardware to identify individual medications and sort them into the correct storage location.

The system is being developed using a Raspberry Pi 5 as the main controller.

## System Overview

The current RxSort workflow is:

Physical Pill → Camera → AI Identification → Pill Database → Sort / Reject Decision

A pill is positioned in the camera inspection area where an image is captured. The image is processed by a trained image classification model, which returns a predicted pill class and confidence value. The prediction is then connected to the RxSort medication database.

## Hardware

- Raspberry Pi 5
- Raspberry Pi Camera Module 3
- Pill feeding and sorting mechanism (in development)
- Rotating storage carousel (in development)

## Software

The software is primarily written in Python and is organized into separate components for computer vision, artificial intelligence, database management, testing, and hardware control.

### Computer Vision

The Raspberry Pi Camera Module 3 is controlled using Picamera2.

The vision system currently supports:

- Live camera preview
- Autofocus
- Pill image capture
- Organized image collection for AI training
- Top and bottom pill image datasets

### AI Pill Identification

An initial pill classification model was trained using Google Teachable Machine and exported as a TensorFlow Lite model.

The model currently contains three pill classes:

- Ibuprofen
- Simvastatin
- Amlodipine

The TensorFlow Lite model is executed locally on the Raspberry Pi using LiteRT.

The current AI pipeline is:

Camera Image → Image Preprocessing → TFLite Model → Class Prediction → Database Pill ID

Classification accuracy is still being tested and improved. The current model is a proof-of-concept and is not intended for medical use.

### Medication Database

RxSort uses SQLite to store medication information.

Stored information can include:

- Pill ID
- Medication name
- Brand name
- Strength
- Imprint
- Color
- Shape
- Dosage form
- Physical dimensions

AI predictions are mapped to their corresponding database pill IDs so that medication information can be retrieved after identification.

## Decision Logic

RxSort is designed to make a SORT or REJECT decision after identification.

A pill can be rejected when the identification confidence is below the required threshold or when the system cannot safely identify the medication.

The current confidence threshold used during development is 80%.

## Project Structure

RxSort/
├── ai_interface/
├── database/
├── models/
├── tests/
├── vision/
├── main.py
├── pills_database.csv
└── README.md

The image training dataset is stored locally and is not included in this repository.

## Current Development

Current development is focused on:

- Improving AI pill identification accuracy
- Live camera-based pill identification
- Connecting AI predictions with the medication database
- Developing SORT / REJECT logic
- Integrating the software with the physical sorting mechanism

## Project Status

RxSort is currently under active development as a Senior Design prototype.

The current software demonstrates the foundation for camera-based pill imaging, AI model inference, medication database management, and automated sorting decisions.

## Disclaimer

RxSort is an academic prototype and is not a certified medical device. The current system should not be used to make real-world medication or healthcare decisions.
