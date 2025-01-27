import os
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
AWS_REGION = os.getenv("AWS_REGION")
REPOSITORY_NAME = os.getenv("REPOSITORY_NAME")
IMAGE_TAG = os.getenv("IMAGE_TAG")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

# Verificar se todas as variáveis essenciais estão definidas
if not all([AWS_REGION, REPOSITORY_NAME, IMAGE_TAG, ACCOUNT_ID]):
    raise ValueError("Erro: Uma ou mais variáveis de ambiente não estão definidas! Verifique .env")

def run_command(command):
    """Run a shell command and print output."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode())
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr.decode()}")
        raise

def main():
    print("Authenticating Docker with ECR...")
    login_command = f"aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com"
    try:
        run_command(login_command)
    except Exception as e:
        print(f"Erro ao autenticar no ECR: {e}")
        exit(1)

    print(f"Ensuring ECR repository '{REPOSITORY_NAME}' exists...")
    try:
        run_command(f"aws ecr describe-repositories --repository-names {REPOSITORY_NAME} --region {AWS_REGION}")
    except subprocess.CalledProcessError as e:
        if "RepositoryNotFoundException" in e.stderr.decode():
            print(f"Repository '{REPOSITORY_NAME}' not found. Creating...")
            run_command(f"aws ecr create-repository --repository-name {REPOSITORY_NAME} --region {AWS_REGION}")
        else:
            print(f"Erro inesperado ao verificar repositório: {e.stderr.decode()}")
            exit(1)

    print("Building Docker image...")
    run_command(f"docker build -t {REPOSITORY_NAME}:{IMAGE_TAG} ..")  

    print("Tagging Docker image...")
    ecr_image_uri = f"{ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{REPOSITORY_NAME}:{IMAGE_TAG}"
    run_command(f"docker tag {REPOSITORY_NAME}:{IMAGE_TAG} {ecr_image_uri}")

    print(f"Pushing Docker image to ECR: {ecr_image_uri}...")
    run_command(f"docker push {ecr_image_uri}")

    print("Docker image pushed successfully to ECR.")

if __name__ == "__main__":
    main()
