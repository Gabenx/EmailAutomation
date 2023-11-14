# RocketfyProjectEnv

Welcome to my Project! This guide will help you set up a virtual environment and install project dependencies.

## Prerequisites

Make sure you have Python installed on your system.

## Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Gabenx/RocketfyProjectEnv.git

2. **Create a Virtual Environment:**
   Create a virtual environment using the following command in the root folder of your project
   
   ```bash
   python -m venv venv

3. **Activate your virtual enviroment**
   Activate the venv using the following command in the root folder of your project
   
   ```bash
   ./venv/Scripts/Activate
   ```
   If you present the error message "Cannot be loaded because running scripts is disabled on this system" you should:
   - Open PowerShell as an administrator.
   - Run the following command to change the execution policy temporarily <br><br>
     
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope Process
   ```
   if prompted, type 'Y' to confirm and then try to create the virtual enviroment again.
   
4. **Install the dependencies in the requirements.txt file**
   Use the following command to install the dependencies listed in the `requirements.txt` file inside your virtual enviroment

   ```bash
   pip install -r requirements.txt

## Running the Project

For detailed instructions on running the project, please refer to the main Jupyter Notebook:
- [Main.ipynb](src/main.ipynb)
