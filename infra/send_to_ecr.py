import os
import subprocess

# Configuration
AWS_REGION = "us-east-1"
ECR_REPOSITORY_NAME = "fastapi-website-monitor"
IMAGE_TAG = "0.1.0"

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
    login_command = f"aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {AWS_REGION}.dkr.ecr.amazonaws.com"
    run_command(login_command)

    print(f"Ensuring ECR repository '{ECR_REPOSITORY_NAME}' exists...")
    try:
        run_command(f"aws ecr describe-repositories --repository-names {ECR_REPOSITORY_NAME} --region {AWS_REGION}")
    except:
        print(f"Repository '{ECR_REPOSITORY_NAME}' not found. Creating...")
        run_command(f"aws ecr create-repository --repository-name {ECR_REPOSITORY_NAME} --region {AWS_REGION}")

    print("Building Docker image...")
    run_command(f"docker build -t {ECR_REPOSITORY_NAME}:{IMAGE_TAG} .")

    print("Tagging Docker image...")
    ecr_image_uri = f"{AWS_REGION}.dkr.ecr.amazonaws.com/{ECR_REPOSITORY_NAME}:{IMAGE_TAG}"
    run_command(f"docker tag {ECR_REPOSITORY_NAME}:{IMAGE_TAG} {ecr_image_uri}")

    print(f"Pushing Docker image to ECR: {ecr_image_uri}...")
    run_command(f"docker push {ecr_image_uri}")

    print("Docker image pushed successfully to ECR.")

if __name__ == "__main__":
    main()
