#!/bin/bash

# Deployment script for Customer Feedback Sentiment Analysis System
# This script deploys the infrastructure using AWS SAM

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    print_error "AWS SAM CLI is not installed. Please install it first."
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials are not configured. Please run 'aws configure' first."
    exit 1
fi

# Get environment from command line argument
ENVIRONMENT=${1:-dev}

if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Invalid environment. Use: dev, staging, or prod"
    exit 1
fi

print_status "Deploying to environment: $ENVIRONMENT"

# Change to the SAM directory
cd "$(dirname "$0")/sam"

# Build the SAM application
print_status "Building SAM application..."
sam build

if [ $? -ne 0 ]; then
    print_error "SAM build failed"
    exit 1
fi

# Deploy the application
print_status "Deploying SAM application..."
sam deploy --config-env $ENVIRONMENT

if [ $? -ne 0 ]; then
    print_error "SAM deployment failed"
    exit 1
fi

# Get stack outputs
print_status "Getting stack outputs..."
STACK_NAME="sentiment-analysis-stack"
if [ "$ENVIRONMENT" != "dev" ]; then
    STACK_NAME="${STACK_NAME}-${ENVIRONMENT}"
fi

# Get outputs
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`CustomerFeedbackBucketName`].OutputValue' \
    --output text)

API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text)

print_status "Deployment completed successfully!"
echo ""
echo "Stack Information:"
echo "  Environment: $ENVIRONMENT"
echo "  Stack Name: $STACK_NAME"
echo "  S3 Bucket: $BUCKET_NAME"
echo "  API URL: $API_URL"
echo ""

# Create sample data directory if it doesn't exist
SAMPLE_DATA_DIR="../../sample-data"
if [ ! -d "$SAMPLE_DATA_DIR" ]; then
    mkdir -p "$SAMPLE_DATA_DIR"
    print_status "Created sample data directory: $SAMPLE_DATA_DIR"
fi

# Create sample feedback file
SAMPLE_FILE="$SAMPLE_DATA_DIR/sample-feedback.csv"
if [ ! -f "$SAMPLE_FILE" ]; then
    cat > "$SAMPLE_FILE" << EOF
feedback,rating,source
"The app is amazing and easy to use!",5,mobile
"I love the new features, great job!",5,web
"The customer service was terrible and unhelpful.",1,support
"This is the worst banking app I've ever used.",1,mobile
"The interface is confusing and hard to navigate.",2,web
"Good app overall, but could be better.",3,mobile
"Excellent service and fast response times.",5,support
"I'm satisfied with the current features.",4,web
"The app crashes frequently and loses my data.",1,mobile
"Great improvements in the latest update!",5,web
EOF
    print_status "Created sample feedback file: $SAMPLE_FILE"
fi

print_status "Next steps:"
echo "1. Upload sample feedback file to S3:"
echo "   aws s3 cp $SAMPLE_FILE s3://$BUCKET_NAME/"
echo ""
echo "2. Check the API endpoints:"
echo "   curl $API_URL/sentiment/summary"
echo "   curl $API_URL/sentiment/results"
echo ""
echo "3. Monitor the logs:"
echo "   sam logs -n SentimentProcessorFunction --stack-name $STACK_NAME --tail"
echo ""
echo "4. Set up QuickSight dashboard using the DynamoDB table"
echo ""

print_warning "Remember to:"
echo "- Update the notification email in the stack parameters"
echo "- Configure QuickSight with the provided IAM role"
echo "- Test the system with sample data"
echo "- Monitor costs to stay within free tier limits"
