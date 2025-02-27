'''

Packages to install

'''
#!pip install PyMuPDF
#!pip install python-dotenv
#!pip install openai
#!pip install azure-ai-inference

import os
import sys
import fitz  # PyMuPDF
import os
 
import base64
from openai import AzureOpenAI  
import os
from dotenv import load_dotenv

import json
import base64
from pydantic import BaseModel
from typing import List



def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
def convert_pdfpages_to_images(pdf_path, output_dir):
    # Open the PDF
    doc = fitz.open(pdf_path)

    # Choose the page number to convert (0-indexed, so 0 is the first page)
    for i in range(len(doc)):
        if i > 1:
            page_number = i 
            page = doc[page_number]

            # Render page to an image (using default zoom factor)
            pix = page.get_pixmap(dpi=300)

            # Save the image as PNG
            output_image_path = os.path.join(output_dir, f"page_{page_number + 1}.png")
            pix.save(output_image_path)

def get_images(output_dir):
    images = []
    for files in os.listdir(output_dir):
        images.append(os.path.join(output_dir,files))
    return images



class FHIRpathform(BaseModel):
    field_name:str
    FHIR_path:str
    explanation:str
    resource_type:str

class FHIRpathoutput(BaseModel):
    results:List[FHIRpathform]

def generate_fhirpath(forms):
    SYSTEM_PROMPT = """You are expert in Health Care Information System with speciality in utilising Fast Healthcare Interoperability Resources"""
    USER_PROMPT = """Given a set of hospital forms used by institutions to track patient claims, coverages, and related information, your task is to:
    Extract all relevant fields from the forms, ensuring completeness and accuracy.
    Map each field to its corresponding FHIR path based on the appropriate FHIR resource (e.g., Claim, Coverage, Patient, etc.).
    Provide a brief explanation for each mapped field, describing its purpose within the form and its significance in the FHIR standard. Also obtain
    the resource type of the FHIR path.
    Ensure that the mapping follows FHIR best practices and aligns with the appropriate resource structures."""

    PROMPT = SYSTEM_PROMPT+USER_PROMPT

    load_dotenv(override=True)
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    subscription_key =  os.environ.get("AZURE_OPENAI_KEY")
    version = os.environ.get("AZURE_OPENAI_API_VERSION")
    # Initialize Azure OpenAI Service client with key-based authentication    
    client = AzureOpenAI(  
        azure_endpoint=endpoint,  
        api_key=subscription_key,  
        api_version=version,
    )
    for images in forms:
        base64_image = encode_image(images)
        #Prepare the chat prompt 
        chat_prompt = [
                {
                    "role":"system",
                    "content":SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": USER_PROMPT,
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ]

        messages = chat_prompt  
            
        # Generate the completion  client.beta.chat.completions.parse
        completion = client.beta.chat.completions.parse(  
            model=deployment,
            messages=messages,
            max_tokens=None,  
            temperature=0,  
            top_p=0,
            response_format=FHIRpathoutput,
            seed=70)

        response = completion.choices[0].message.content

        file_name = f"sample_response_{form_name}_{os.path.basename(images).split(".")[0]}.json"

        with open(file_name, "w") as file:
            json.dump(eval(response), file, indent=4)

        print(f"Saved File {file_name}")
        
if __name__ == "__main__":
    wd = os.getcwd()

    '''
    Change the pdf_name to the form 

    Ensure the working directory (wd) is the root directory of the project
    
    '''
    pdf_name = "ub04_form.pdf"
    pdf_wd = wd+"//Fw_Source_To_Targe_FHIR_Mapping_Research//"+pdf_name
    form_name = pdf_name.split(".")[0]

    output_dir = os.path.join(wd, f"{pdf_name}_image")
    # Set PDF file path
    pdf_path = pdf_wd

    # Specify output directory and ensure it exists
    output_dir = output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Convert PDF pages to images
    forms = convert_pdfpages_to_images(pdf_path, output_dir)

    # Get the images
    images = get_images(output_dir)

    # Generate FHIR path from the image
    generate_fhirpath(images)


