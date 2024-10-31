# Images Inferencing

This Python project is designed to extract text, tables, and images from PDF, DOCX, and CSV files. It utilizes AWS S3 for storing extracted images, Hugging Face API for model integrations, and a Streamlit frontend for ease of use.

## Table of Contents
1. [Installation](#installation)
2. [Setup](#setup)
3. [Running the Application](#running-the-application)
4. [Project Structure](#project-structure)
5. [Technologies Used](#technologies-used)

---

## Installation

### 1. Clone the Repository
First, clone the repository using Git:

```bash
git clone https://github.com/damlois/multi-text-extraction.git
cd multiTextExtractor
```

### 2. Install Dependencies
Use the following command to install all required dependencies:

```bash
pip install -r requirements.txt
```

---

## Setup

### 1. Configure AWS Credentials
Set up your AWS credentials to allow access to AWS services by using the AWS CLI. 

```bash
aws configure
```

This command will prompt you to enter your AWS Access Key, Secret Access Key, region, and output format. For more details, refer to [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html).

### 2. Create an S3 Bucket
Create an S3 bucket to store the extracted images:

1. Go to your [AWS S3 Console](https://s3.console.aws.amazon.com/s3).
2. Click on **Create Bucket**.
3. Name your bucket and set the necessary permissions.

### 3. Set up a Hugging Face API Token
Generate a read token from your Hugging Face account to allow the project to access models:

1. Go to your [Hugging Face Account Settings](https://huggingface.co/settings/tokens).
2. Create a **Read Token** (API_KEY) and note it down for later use.

### 4. Create a `.env` File
In the root directory of the project, create a `.env` file with the following variables:

```plaintext
API_KEY=your_huggingface_api_key
BUCKET_NAME=your_s3_bucket_name
```

Replace `your_huggingface_api_key` and `your_s3_bucket_name` with your actual Hugging Face API key and the S3 bucket name.

---

## Running the Application

To run the Streamlit application, use the following command:

```bash
streamlit run main.py
```

This will start the application, and you can access it in your browser at `http://localhost:8501`.

---

## Project Structure

```
MultiTextExtractor/
├── utils/
│   ├── file_type/             # Directory for file-type-specific utilities
│   ├── __init__.py            # Initialization for file_type module
│   ├── display.py             # Result display utilities
│   ├── helpers.py             # Helper functions for file processing
├── venv/                      # Virtual environment directory
├── .env                       # Environment variables file
├── .gitignore                 # Git ignore file
├── main.py                    # Main Streamlit application
├── model.py                   # Model handling and API interactions
├── README.md                  # Project documentation
└── requirements.txt           # Required packages
```

---

## Technologies Used

- **Python**: Core language used in the project.
- **Streamlit**: For building the frontend interface.
- **AWS S3**: Storage for extracted images.
- **Hugging Face**: NLP and machine learning model API.
