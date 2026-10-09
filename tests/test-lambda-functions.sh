#!/bin/bash

# Lambda Functions Testing Script
# Tests all 3 Lambda functions in the sentiment analysis system

set -e  # Exit on any error

echo "🧪 Testing Lambda Functions for Sentiment Analysis System"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "info")
            echo -e "${YELLOW}ℹ️  $message${NC}"
            ;;
        "test")
            echo -e "${YELLOW}🧪 $message${NC}"
            ;;
    esac
}

# Create test results directory
mkdir -p test-results

echo ""
print_status "info" "Starting Lambda function tests..."

# Test 1: sentiment-processor-dev
echo ""
print_status "test" "Testing sentiment-processor-dev..."
if aws lambda invoke \
    --function-name sentiment-processor-dev \
    --payload file://test-payloads/processor-test.json \
    --region us-east-1 \
    test-results/processor-response.json 2>/dev/null; then
    
    print_status "success" "sentiment-processor-dev test completed"
    echo "Response saved to: test-results/processor-response.json"
    echo "Response content:"
    cat test-results/processor-response.json | jq . 2>/dev/null || cat test-results/processor-response.json
else
    print_status "error" "sentiment-processor-dev test failed"
fi

# Test 2: sentiment-api-handler-dev
echo ""
print_status "test" "Testing sentiment-api-handler-dev..."
if aws lambda invoke \
    --function-name sentiment-api-handler-dev \
    --payload file://test-payloads/api-test.json \
    --region us-east-1 \
    test-results/api-response.json 2>/dev/null; then
    
    print_status "success" "sentiment-api-handler-dev test completed"
    echo "Response saved to: test-results/api-response.json"
    echo "Response content:"
    cat test-results/api-response.json | jq . 2>/dev/null || cat test-results/api-response.json
else
    print_status "error" "sentiment-api-handler-dev test failed"
fi

# Test 3: sentiment-alert-handler-dev
echo ""
print_status "test" "Testing sentiment-alert-handler-dev..."
if aws lambda invoke \
    --function-name sentiment-alert-handler-dev \
    --payload file://test-payloads/alert-test.json \
    --region us-east-1 \
    test-results/alert-response.json 2>/dev/null; then
    
    print_status "success" "sentiment-alert-handler-dev test completed"
    echo "Response saved to: test-results/alert-response.json"
    echo "Response content:"
    cat test-results/alert-response.json | jq . 2>/dev/null || cat test-results/alert-response.json
else
    print_status "error" "sentiment-alert-handler-dev test failed"
fi

echo ""
print_status "info" "Testing completed! Check test-results/ directory for detailed responses."

# Show function status
echo ""
print_status "info" "Current Lambda function status:"
aws lambda list-functions --region us-east-1 --query 'Functions[?contains(FunctionName, `sentiment`)].{Name:FunctionName,State:State,Runtime:Runtime,LastModified:LastModified}' --output table

echo ""
print_status "info" "For detailed testing instructions, see: docs/lambda-testing-guide.md"
