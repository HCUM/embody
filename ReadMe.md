# EMBody: A Data-Centric Toolkit for EMG-Based Interface Prototyping and Experimentation

This repository contains EMBody, a data-centric toolkit for rapid prototyping and experimentation of EMG-based interfaces.

## About
EMBody is a toolkit, which was developed at LMU Munich. It is financially supported by the European Union's Horizon 2020 Programme under ERCEA grant no. 683008 AMPLIFY.

The toolkit consists of a hardware prototype that can record electrical potentials (e.g. via surface electrodes), convert these in a digital representation, and stream them over an available WiFi connection. This is complemented by an accompanying software application, that receives the signal and provides an interpretation of the data.

EMBody's main use case is recording electromyograms (EMG) via surface electrodes. We envision that the toolkit enables creators to rapidly begin their journey into EMG-based interfaces. This repository contains all the necessary resources to build the system from scratch. Please feel free to contact us in case of questions.

## Hardware ressources
* Circuit board layouts and cases: see casing/ and circuits/ for files
* Short assembly description
* Firmware for ESP32 microcontroller: see /esp_firmware

## Software application (embody/)
* python application connecting to the prototype, see /manual for a detailed operation manual.
