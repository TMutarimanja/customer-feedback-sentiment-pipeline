"""
Lambda function to process customer feedback files and perform sentiment analysis.
Triggered by S3 events when new files are uploaded.
"""

import json
import boto3
import csv
import io
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import os
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

# Environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'sentiment-analysis-results')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
NEGATIVE_SENTIMENT_THRESHOLD = float(os.environ.get('NEGATIVE_SENTIMENT_THRESHOLD', '0.3'))

def lambda_handler(event, context):
    """
    Main Lambda handler function.
    
    Args:
        event: S3 event or EventBridge event containing file information
        context: Lambda context object
        
    Returns:
        dict: Response with processing status
    """
    try:
        logger.info(f"Processing event: {json.dumps(event)}")
        
        processed_files = 0
        
        # Handle S3 events (direct S3 notifications)
        if 'Records' in event:
            for record in event['Records']:
                bucket_name = record['s3']['bucket']['name']
                object_key = record['s3']['object']['key']
                
                logger.info(f"Processing file: {object_key} from bucket: {bucket_name}")
                
                # Process the uploaded file
                result = process_feedback_file(bucket_name, object_key)
                
                logger.info(f"Processing completed for {object_key}: {result}")
                processed_files += 1
        
        # Handle EventBridge events (S3 object created events)
        elif 'detail' in event and event.get('source') == 'aws.s3':
            bucket_name = event['detail']['bucket']['name']
            object_key = event['detail']['object']['key']
            
            logger.info(f"Processing file: {object_key} from bucket: {bucket_name}")
            
            # Process the uploaded file
            result = process_feedback_file(bucket_name, object_key)
            
            logger.info(f"Processing completed for {object_key}: {result}")
            processed_files += 1
        
        else:
            logger.error(f"Unknown event format: {event}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Unknown event format',
                    'message': 'Event must be S3 or EventBridge format'
                })
            }
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'File processing completed successfully',
                'processed_files': processed_files
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to process file',
                'message': str(e)
            })
        }

def process_feedback_file(bucket_name: str, object_key: str) -> Dict[str, Any]:
    """
    Process a customer feedback file and perform sentiment analysis.
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        
    Returns:
        dict: Processing results
    """
    try:
        # Download file from S3
        file_content = download_file_from_s3(bucket_name, object_key)
        
        # Parse file content based on file type
        feedback_data = parse_file_content(object_key, file_content)
        
        # Perform sentiment analysis
        analysis_results = []
        negative_sentiment_count = 0
        
        for feedback_item in feedback_data:
            sentiment_result = analyze_sentiment(feedback_item['text'])
            
            # Store result in DynamoDB
            result_id = store_analysis_result(
                object_key=object_key,
                feedback_item=feedback_item,
                sentiment_result=sentiment_result
            )
            
            analysis_results.append({
                'id': result_id,
                'text': feedback_item['text'],
                'sentiment': sentiment_result['Sentiment'],
                'confidence': sentiment_result['SentimentScore']
            })
            
            # Check for negative sentiment
            if (sentiment_result['Sentiment'] == 'NEGATIVE' and 
                sentiment_result['SentimentScore']['Negative'] > NEGATIVE_SENTIMENT_THRESHOLD):
                negative_sentiment_count += 1
        
        # Send alert if significant negative sentiment detected
        if negative_sentiment_count > 0:
            send_negative_sentiment_alert(object_key, negative_sentiment_count, len(feedback_data))
        
        return {
            'total_feedback_items': len(feedback_data),
            'negative_sentiment_count': negative_sentiment_count,
            'analysis_results': analysis_results
        }
        
    except Exception as e:
        logger.error(f"Error processing file {object_key}: {str(e)}")
        raise

def download_file_from_s3(bucket_name: str, object_key: str) -> str:
    """
    Download file content from S3.
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        
    Returns:
        str: File content
    """
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        logger.error(f"Error downloading file from S3: {str(e)}")
        raise

def parse_file_content(object_key: str, file_content: str) -> List[Dict[str, Any]]:
    """
    Parse file content based on file type.
    
    Args:
        object_key: S3 object key (for file type detection)
        file_content: Raw file content
        
    Returns:
        List[Dict]: Parsed feedback data
    """
    file_extension = object_key.lower().split('.')[-1]
    
    if file_extension == 'csv':
        return parse_csv_content(file_content)
    elif file_extension == 'json':
        return parse_json_content(file_content)
    else:
        # Treat as plain text
        return parse_text_content(file_content)

def parse_csv_content(file_content: str) -> List[Dict[str, Any]]:
    """
    Parse CSV content.
    
    Args:
        file_content: CSV file content
        
    Returns:
        List[Dict]: Parsed feedback data
    """
    feedback_data = []
    
    try:
        csv_reader = csv.DictReader(io.StringIO(file_content))
        
        for row in csv_reader:
            # Look for common column names for feedback text
            text_column = None
            for col in ['feedback', 'text', 'comment', 'review', 'message']:
                if col in row:
                    text_column = col
                    break
            
            if text_column and row[text_column].strip():
                feedback_data.append({
                    'text': row[text_column].strip(),
                    'metadata': {k: v for k, v in row.items() if k != text_column}
                })
                
    except Exception as e:
        logger.error(f"Error parsing CSV content: {str(e)}")
        raise
    
    return feedback_data

def parse_json_content(file_content: str) -> List[Dict[str, Any]]:
    """
    Parse JSON content.
    
    Args:
        file_content: JSON file content
        
    Returns:
        List[Dict]: Parsed feedback data
    """
    try:
        data = json.loads(file_content)
        
        # Handle different JSON structures
        if isinstance(data, list):
            feedback_data = []
            for item in data:
                if isinstance(item, dict):
                    # Look for text field
                    text_field = None
                    for field in ['feedback', 'text', 'comment', 'review', 'message']:
                        if field in item:
                            text_field = field
                            break
                    
                    if text_field and item[text_field].strip():
                        feedback_data.append({
                            'text': item[text_field].strip(),
                            'metadata': {k: v for k, v in item.items() if k != text_field}
                        })
            return feedback_data
            
        elif isinstance(data, dict):
            # Single feedback item
            text_field = None
            for field in ['feedback', 'text', 'comment', 'review', 'message']:
                if field in data:
                    text_field = field
                    break
            
            if text_field and data[text_field].strip():
                return [{
                    'text': data[text_field].strip(),
                    'metadata': {k: v for k, v in data.items() if k != text_field}
                }]
        
        return []
        
    except Exception as e:
        logger.error(f"Error parsing JSON content: {str(e)}")
        raise

def parse_text_content(file_content: str) -> List[Dict[str, Any]]:
    """
    Parse plain text content.
    
    Args:
        file_content: Text file content
        
    Returns:
        List[Dict]: Parsed feedback data
    """
    # Split by lines and treat each non-empty line as feedback
    lines = file_content.strip().split('\n')
    feedback_data = []
    
    for line in lines:
        if line.strip():
            feedback_data.append({
                'text': line.strip(),
                'metadata': {}
            })
    
    return feedback_data

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze sentiment of text using rule-based analysis (free alternative to AWS Comprehend).
    
    Args:
        text: Text to analyze
        
    Returns:
        dict: Sentiment analysis results
    """
    try:
        # Simple rule-based sentiment analysis
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
            'love', 'like', 'best', 'perfect', 'outstanding', 'brilliant', 'superb',
            'delighted', 'pleased', 'satisfied', 'happy', 'impressed', 'recommend',
            'helpful', 'easy', 'fast', 'quick', 'reliable', 'professional', 'friendly'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'dislike',
            'disappointed', 'frustrated', 'angry', 'annoyed', 'upset', 'poor',
            'slow', 'broken', 'crashed', 'failed', 'error', 'problem', 'issue',
            'difficult', 'hard', 'confusing', 'complicated', 'unreliable', 'unhelpful'
        ]
        
        # Convert to lowercase for comparison
        text_lower = text.lower()
        
        # Count positive and negative words
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Determine sentiment based on word counts
        if positive_count > negative_count:
            sentiment = 'POSITIVE'
            confidence = min(0.95, 0.5 + (positive_count - negative_count) * 0.1)
            sentiment_scores = {
                'Positive': confidence,
                'Negative': (1 - confidence) * 0.3,
                'Neutral': (1 - confidence) * 0.5,
                'Mixed': (1 - confidence) * 0.2
            }
        elif negative_count > positive_count:
            sentiment = 'NEGATIVE'
            confidence = min(0.95, 0.5 + (negative_count - positive_count) * 0.1)
            sentiment_scores = {
                'Positive': (1 - confidence) * 0.3,
                'Negative': confidence,
                'Neutral': (1 - confidence) * 0.5,
                'Mixed': (1 - confidence) * 0.2
            }
        else:
            sentiment = 'NEUTRAL'
            sentiment_scores = {
                'Positive': 0.25,
                'Negative': 0.25,
                'Neutral': 0.45,
                'Mixed': 0.05
            }
        
        return {
            'Sentiment': sentiment,
            'SentimentScore': sentiment_scores
        }
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        # Return neutral sentiment as fallback
        return {
            'Sentiment': 'NEUTRAL',
            'SentimentScore': {
                'Positive': 0.33,
                'Negative': 0.33,
                'Neutral': 0.34,
                'Mixed': 0.0
            }
        }

def convert_floats_to_decimals(obj):
    """
    Recursively convert float values to Decimal for DynamoDB compatibility.
    
    Args:
        obj: Object to convert
        
    Returns:
        Object with floats converted to Decimals
    """
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimals(v) for v in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj

def store_analysis_result(object_key: str, feedback_item: Dict[str, Any], 
                         sentiment_result: Dict[str, Any]) -> str:
    """
    Store analysis result in DynamoDB.
    
    Args:
        object_key: S3 object key
        feedback_item: Feedback item data
        sentiment_result: Sentiment analysis result
        
    Returns:
        str: Result ID
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        # Generate unique ID with New York timezone (UTC-5 or UTC-4 depending on DST)
        ny_tz = timezone(timedelta(hours=-5))  # EST (UTC-5), adjust for DST if needed
        result_id = f"{object_key}_{datetime.now(ny_tz).isoformat()}"
        
        # Prepare item for DynamoDB (convert floats to Decimals)
        item = {
            'id': result_id,
            'object_key': object_key,
            'text': feedback_item['text'],
            'sentiment': sentiment_result['Sentiment'],
            'sentiment_score': convert_floats_to_decimals(sentiment_result['SentimentScore']),
            'metadata': convert_floats_to_decimals(feedback_item.get('metadata', {})),
            'timestamp': datetime.now(ny_tz).isoformat(),
            'ttl': int((datetime.now().timestamp() + (365 * 24 * 60 * 60)))  # 1 year TTL
        }
        
        # Store in DynamoDB
        table.put_item(Item=item)
        
        logger.info(f"Stored analysis result: {result_id}")
        return result_id
        
    except Exception as e:
        logger.error(f"Error storing analysis result: {str(e)}")
        raise

def send_negative_sentiment_alert(object_key: str, negative_count: int, total_count: int):
    """
    Send alert for negative sentiment detection.
    
    Args:
        object_key: S3 object key
        negative_count: Number of negative sentiment items
        total_count: Total number of items
    """
    try:
        if not SNS_TOPIC_ARN:
            logger.warning("SNS topic ARN not configured, skipping alert")
            return
        
        message = f"""
        Negative sentiment detected in customer feedback file: {object_key}
        
        Summary:
        - Total feedback items: {total_count}
        - Negative sentiment items: {negative_count}
        - Negative sentiment percentage: {(negative_count/total_count)*100:.1f}%
        
        Please review the feedback and take appropriate action.
        """
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Negative Sentiment Alert - {object_key}",
            Message=message
        )
        
        logger.info(f"Sent negative sentiment alert for {object_key}")
        
    except Exception as e:
        logger.error(f"Error sending negative sentiment alert: {str(e)}")
        # Don't raise exception for alert failures
