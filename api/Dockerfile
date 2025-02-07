#get the base image from docker
FROM python:3.9

#set the working directory
WORKDIR /usr/src/app

#copy all the requirements into the working directory
COPY requirements.txt ./

#install all the requirements
RUN pip install --no-cache-dir -r requirements.txt

#copy content of local source directory to the working directory
COPY . .

#run the backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]