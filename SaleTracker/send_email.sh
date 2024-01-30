#!/bin/bash

# Get email address from user input
read -p "Enter the email address: " email

# Send POST request to Flask endpoint
curl -X POST -H "Content-Type: application/json" -d "{\"email\": \"$email\"}" https://saletracker-56fca67f4822.herokuapp.com/send-email
