import sys
import os
import subprocess

# setting the BASE_PATH to the location of project directory
BASE_PATH = os.getcwd()

# to update the paths accordingly
RESEARCH_PATH = os.path.join(BASE_PATH, 'tensorflow_models', 'research')
SLIM_PATH = os.path.join(RESEARCH_PATH, 'slim')
PROTO_PATH = os.path.join(RESEARCH_PATH, 'object_detection', 'protos')

# adding TensorFlow models research and slim directories to PYTHONPATH
sys.path.append(RESEARCH_PATH)
sys.path.append(SLIM_PATH)

# compiling the Protobuf files
def compile_protos():
    protoc_command = f"protoc {os.path.join(PROTO_PATH, '*.proto')} --python_out=."
    process = subprocess.Popen(protoc_command.split(), stdout=subprocess.PIPE, cwd=RESEARCH_PATH)
    output, error = process.communicate()

    # To check
    if error:
        print(f"Error during protobuf compilation: {error.decode('utf-8')}")
    else:
        print("Protobuf files compiled successfully!")

# Call the function to compile the protobufs
compile_protos()