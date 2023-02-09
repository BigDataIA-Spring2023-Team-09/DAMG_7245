import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from dotenv import load_dotenv
import boto3
import os
import botocore



st.markdown("<h1 style='text-align: center;'>NEXRAD</h1>", unsafe_allow_html=True)
st.header("")
st.header("Search by Fields")
st.header("")


def copy_to_public_bucket(src_bucket_name, src_object_key, dest_bucket_name, dest_object_key):
    copy_source = {
        'Bucket': src_bucket_name,
        'Key': src_object_key
    }
    s3client.copy_object(Bucket=dest_bucket_name, CopySource=copy_source, Key=dest_object_key)


def generate_download_link(bucket_name, object_key, expiration=3600):
    response = s3client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket_name,
            'Key': object_key
        },
        ExpiresIn=expiration
    )
    return response



def path_from_filename(filename):
   
    details_list =[]
    details_list.append(filename[:4])
    details_list.append(filename[4:8])
    details_list.append(filename[8:10])
    details_list.append(filename[10:12])
    details_list.append(filename)
    file_path = f"{details_list[1]}/{details_list[2]}/{details_list[3]}/{details_list[0]}/{details_list[4]}"
    return file_path


def check_if_file_exists_in_s3_bucket(bucket_name, file_name):
    try:
        s3client.head_object(Bucket=bucket_name, Key=file_name)
        return True

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise


load_dotenv()


s3client = boto3.client('s3', 
                        region_name = 'us-east-1',
                        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                        )


conn = sqlite3.connect("filenames_nexrad.db")
c = conn.cursor()


col1, col2, col3, col4 = st.columns(4, gap="large")


query = c.execute("SELECT DISTINCT Year FROM filenames_nexrad")
year_list = [row[0] for row in query]


with col1:
    year = st.selectbox(
        'Select the Year :',
        (year_list))
    st.write('You selected :', year)


query = "SELECT DISTINCT Month FROM filenames_nexrad where Year = ?"
result = c.execute(query, (year,))
month_list = [row[0] for row in result]

   
with col2:
    month = st.selectbox(
        'Select the Month :',
        (month_list))

    st.write('You selected :', month)


query = "SELECT DISTINCT Day FROM filenames_nexrad where Year = ? and Month = ?"
result = c.execute(query, (year, month))
day_list = [row[0] for row in result]  


with col3:
    day = st.selectbox(
        'Select the Date :',
        (day_list))

    st.write('You selected :', day)


query = "SELECT DISTINCT Station FROM filenames_nexrad where Year = ? and Month = ? and Day = ?"
result = c.execute(query, (year, month, day))
station_list = [row[0] for row in result]  


with col4:

    station = st.selectbox(
        'Select the Station :',
        (station_list))

    st.write('You selected :', station)


st.header("")


result = s3client.list_objects(Bucket='noaa-nexrad-level2', Prefix=f"{year}/{month}/{day}/{station}/")
file_list = []
files = result.get("Contents", [])
for file in files:
    file_list.append(file["Key"].split('/')[-1])


selected_file = st.selectbox("Select link for download", 
            (file_list),  
            key=None, help="select link for download")


nexrad_bucket = 'noaa-nexrad-level2'
selected_object_key = f'{year}/{month}/{day}/{station}/{selected_file}'
user_bucket_name = os.environ.get('USER_BUCKET_NAME')
user_object_key = f'logs/nexrad/{selected_file}'


st.header("")

if st.button('Generate using Filter'):    
    copy_to_public_bucket(nexrad_bucket, selected_object_key, user_bucket_name, user_object_key)
    download_link = generate_download_link(user_bucket_name, user_object_key)
    st.write('Download Link : ', download_link.split("?")[0])


st.header("")
st.header("Search by Filename")
st.header("")


filename = st.text_input('Enter Filename')
st.header("")



if st.button('Generate using Name'):  
    if (filename == ""): 
        st.write("Please enter file name")

    else: 
        selected_object_key = path_from_filename(filename)

        file_exists = check_if_file_exists_in_s3_bucket(nexrad_bucket, selected_object_key)

        try:
            if file_exists:
                copy_to_public_bucket(nexrad_bucket, selected_object_key, user_bucket_name, user_object_key)
                download_link = generate_download_link(user_bucket_name, user_object_key)
                st.write('Download Link : ', download_link.split("?")[0])
            else:
                raise Exception("File Not Found")
        except Exception as e:
            st.write("File Not Found")