#!/bin/bash

# Deployment script for Customer Feedback Sentiment Analysis System
# This script deploys the infrastructure using AWS CloudFormation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    echo ""
    echo "Installation options:"
    echo "1. sudo snap install aws-cli --classic"
    echo "2. sudo apt install awscli"
    echo "3. Download from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials are not configured. Please run 'aws configure' first."
    echo ""
    echo "You'll need:"
    echo "- AWS Access Key ID"
    echo "- AWS Secret Access Key"
    echo "- Default region (e.g., us-east-1)"
    echo "- Default output format (json)"
    exit 1
fi

# Get AWS account info
print_header "AWS Account Information"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)
print_status "Account ID: $ACCOUNT_ID"
print_status "Region: $REGION"

# Get environment from command line argument
ENVIRONMENT=${1:-dev}

if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Invalid environment. Use: dev, staging, or prod"
    exit 1
fi

print_header "Deploying to environment: $ENVIRONMENT"

# Get notification email
read -p "Enter your email for notifications: " NOTIFICATION_EMAIL

if [[ -z "$NOTIFICATION_EMAIL" ]]; then
    print_warning "No email provided, using default"
    NOTIFICATION_EMAIL="admin@example.com"
fi

# Change to the CloudFormation directory
cd "$(dirname "$0")/backend/infrastructure/cloudformation"

# Validate template
print_status "Validating CloudFormation template..."
if ! aws cloudformation validate-template --template-body file://sentiment-analysis-stack.yaml &> /dev/null; then
    print_error "Template validation failed"
    exit 1
fi
print_status "Template validation successful"

# Deploy the stack
print_status "Deploying CloudFormation stack..."
STACK_NAME="sentiment-analysis-stack-${ENVIRONMENT}"

aws cloudformation create-stack \
    --stack-name "$STACK_NAME" \
    --template-body file://sentiment-analysis-stack.yaml \
    --parameters ParameterKey=Environment,ParameterValue="$ENVIRONMENT" \
                 ParameterKey=S3BucketName,ParameterValue="customer-feedback-sentiment-analysis" \
                 ParameterKey=NotificationEmail,ParameterValue="$NOTIFICATION_EMAIL" \
                 ParameterKey=NegativeSentimentThreshold,ParameterValue=0.3 \
    --capabilities CAPABILITY_IAM

if [ $? -ne 0 ]; then
    print_error "Stack creation failed"
    exit 1
fi

print_status "Stack creation initiated. Waiting for completion..."

# Wait for stack creation
aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME"

if [ $? -ne 0 ]; then
    print_error "Stack creation failed or timed out"
    print_status "Check the AWS Console for details"
    exit 1
fi

# Get stack outputs
print_status "Getting stack outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text)

BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`CustomerFeedbackBucketName`].OutputValue' \
    --output text)

TABLE_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`SentimentAnalysisTableName`].OutputValue' \
    --output text)

print_header "Deployment completed successfully!"
echo ""
echo "Stack Information:"
echo "  Environment: $ENVIRONMENT"
echo "  Stack Name: $STACK_NAME"
echo "  API URL: $API_URL"
echo "  S3 Bucket: $BUCKET_NAME"
echo "  DynamoDB Table: $TABLE_NAME"
echo ""

# Update frontend configuration
print_status "Updating frontend configuration..."
FRONTEND_CONFIG="../../frontend/nuxt.config.js"

if [ -f "$FRONTEND_CONFIG" ]; then
    # Create backup
    cp "$FRONTEND_CONFIG" "${FRONTEND_CONFIG}.backup"
    
    # Update configuration
    sed -i "s|https://your-api-gateway-url.amazonaws.com/dev|$API_URL|g" "$FRONTEND_CONFIG"
    sed -i "s|customer-feedback-sentiment-analysis-dev|$BUCKET_NAME|g" "$FRONTEND_CONFIG"
    
    print_status "Frontend configuration updated"
    print_warning "Restart the frontend development server to apply changes"
else
    print_warning "Frontend configuration file not found at $FRONTEND_CONFIG"
fi

# Create sample data directory if it doesn't exist
SAMPLE_DATA_DIR="../../sample-data"
if [ ! -d "$SAMPLE_DATA_DIR" ]; then
    mkdir -p "$SAMPLE_DATA_DIR"
    print_status "Created sample data directory: $SAMPLE_DATA_DIR"
fi

print_status "Next steps:"
echo "1. Restart the frontend development server:"
echo "   cd ../../frontend && npm run dev"
echo ""
echo "2. Upload sample data to test:"
echo "   aws s3 cp ../../sample-data/customer-feedback-demo.csv s3://$BUCKET_NAME/"
echo ""
echo "3. Test the API endpoints:"
echo "   curl $API_URL/sentiment/summary"
echo "   curl $API_URL/sentiment/results"
echo ""
echo "4. Monitor the logs:"
echo "   aws logs describe-log-groups --log-group-name-prefix /aws/lambda/"
echo ""

print_warning "Remember to:"
echo "- Monitor costs to stay within free tier limits"
echo "- Test the system with sample data"
echo "- Check the notification email for SNS subscription confirmation"
echo "- Update the frontend configuration if needed"
