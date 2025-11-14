# Emoji Cam

Emoji cam is a facial recognition & emotion detection computer vision pipeline using CNNs & OBS Virtual Cam to log users’ detected emotions.

## Features

- FER pipeline to detect users' faces and then assess their emotions
- GUI for logging into the program and accessing its features (Enabling/disabling the camera, settings, visualization)
- Displays an emoji based on the user's most likely emotion (i.e. happiness level)
- Displays an graph indicating the changes over time in the likelihood of each emotion
- Settings are saved locally and include resolution, polling rate, a toggle for the graph, a toggle for the emoji, etc.
- Implements pyvirtualcam to create a modified OBS Virtual Cam as an webcam output
- Boto3 is used to register & authenticate users in DynamoDB
- Recorded emotions are stored in memory and uploaded as CSVs into an S3 bucket
- Allows for the visualization of stored emotion data for a given time-range
  
## Requirements

- Requires Python 3.11

- Facial Expression Recognition
