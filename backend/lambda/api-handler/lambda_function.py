"""
Lambda function to handle API requests for the sentiment analysis system.
Provides REST API endpoints for querying analysis results and managing the system.
"""

import json
import boto3
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import os
import base64
import uuid
import mimetypes
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

# Environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'sentiment-analysis-results')
S3_BUCKET = os.environ.get('S3_BUCKET', 'customer-feedback-bucket')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')

def convert_decimals_to_floats(obj):
    """
    Recursively convert Decimal values to floats for JSON serialization.
    
    Args:
        obj: Object to convert
        
    Returns:
        Object with Decimals converted to floats
    """
    if isinstance(obj, dict):
        return {k: convert_decimals_to_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_floats(v) for v in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

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

def lambda_handler(event, context):
    """
    Main Lambda handler function for API requests.
    
    Args:
        event: API Gateway event
        context: Lambda context object
        
    Returns:
        dict: API Gateway response
    """
    try:
        logger.info(f"Processing API request: {json.dumps(event)}")
        
        # Extract HTTP method and path
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        body = event.get('body', '{}')
        
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            return create_response(200, {
                'message': 'CORS preflight successful'
            })
        
        # Route requests based on method and path
        if http_method == 'GET':
            # Check if summary is requested via query parameter
            if query_parameters.get('summary') == 'true':
                return get_sentiment_summary(query_parameters)
            # Default to results
            else:
                return get_sentiment_results(query_parameters)
        
        elif http_method == 'POST':
            # Explicit routes for clarity and easier debugging
            content_type = (event.get('headers', {}) or {}).get('content-type', '')
            normalized_path = path.rstrip('/')

            # Bulk upload endpoint: /sentiment/bulk
            if normalized_path.endswith('/sentiment/bulk'):
                if 'multipart/form-data' in content_type:
                    return handle_file_upload(event)
                return create_response(400, {'error': 'Invalid content type', 'message': 'Use multipart/form-data for bulk uploads'})

            # Single feedback endpoint: /sentiment/feedback
            if normalized_path.endswith('/sentiment/feedback'):
                if 'application/json' in content_type or content_type == '':
                    return handle_text_feedback(event)
                return create_response(400, {'error': 'Invalid content type', 'message': 'Use application/json for single feedback'})

            # Backward-compatible behavior on legacy /sentiment POST
            if normalized_path.endswith('/sentiment'):
                if 'multipart/form-data' in content_type:
                    return handle_file_upload(event)
                return handle_text_feedback(event)

            return create_response(404, {'error': 'Not found'})
        
        else:
            return create_response(405, {'error': 'Method not allowed'})
            
    except Exception as e:
        logger.error(f"Error processing API request: {str(e)}")
        return create_response(500, {'error': 'Internal server error', 'message': str(e)})

def get_sentiment_results(query_parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Get sentiment analysis results with optional filtering.
    
    Args:
        query_parameters: Query parameters for filtering
        
    Returns:
        dict: API response with results
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        # Build filter expression
        filter_expression = None
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        # Filter by sentiment
        if 'sentiment' in query_parameters:
            filter_expression = "#sentiment = :sentiment"
            expression_attribute_names['#sentiment'] = 'sentiment'
            expression_attribute_values[':sentiment'] = query_parameters['sentiment']
        
        # Filter by date range
        if 'start_date' in query_parameters:
            start_date = query_parameters['start_date']
            if filter_expression:
                filter_expression += " AND #timestamp >= :start_date"
            else:
                filter_expression = "#timestamp >= :start_date"
            expression_attribute_names['#timestamp'] = 'timestamp'
            expression_attribute_values[':start_date'] = start_date
        
        if 'end_date' in query_parameters:
            end_date = query_parameters['end_date']
            if filter_expression:
                filter_expression += " AND #timestamp <= :end_date"
            else:
                filter_expression = "#timestamp <= :end_date"
            expression_attribute_names['#timestamp'] = 'timestamp'
            expression_attribute_values[':end_date'] = end_date
        
        # Pagination - default to no limit to show all results
        limit = query_parameters.get('limit')
        if limit:
            limit = int(limit)
        last_evaluated_key = None
        
        if 'last_key' in query_parameters:
            last_evaluated_key = json.loads(query_parameters['last_key'])
        
        # Query DynamoDB - scan with sorting by timestamp
        scan_kwargs = {}
        if limit:
            scan_kwargs['Limit'] = limit
        
        if filter_expression:
            scan_kwargs['FilterExpression'] = filter_expression
            scan_kwargs['ExpressionAttributeNames'] = expression_attribute_names
            scan_kwargs['ExpressionAttributeValues'] = expression_attribute_values
        
        if last_evaluated_key:
            scan_kwargs['ExclusiveStartKey'] = last_evaluated_key
        
        response = table.scan(**scan_kwargs)
        
        # Format results and sort by timestamp (latest first)
        results = []
        for item in response['Items']:
            results.append(convert_decimals_to_floats({
                'id': item['id'],
                'object_key': item['object_key'],
                'text': item['text'][:200] + '...' if len(item['text']) > 200 else item['text'],
                'sentiment': item['sentiment'],
                'sentiment_score': item['sentiment_score'],
                'timestamp': item['timestamp'],
                'metadata': item.get('metadata', {})
            }))
        
        # Sort by timestamp descending (latest first)
        # Parse ISO timestamps for proper sorting, handling different formats
        def parse_timestamp(timestamp_str):
            try:
                # Handle timestamps with and without timezone info
                if timestamp_str.endswith('Z'):
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                elif '+' in timestamp_str or timestamp_str.count('-') > 2:
                    return datetime.fromisoformat(timestamp_str)
                else:
                    # Assume UTC if no timezone info
                    return datetime.fromisoformat(timestamp_str + '+00:00')
            except:
                # Fallback to string comparison if parsing fails
                return timestamp_str
        
        results.sort(key=lambda x: parse_timestamp(x['timestamp']), reverse=True)
        
        return create_response(200, {
            'results': results,
            'count': len(results),
            'last_evaluated_key': response.get('LastEvaluatedKey'),
            'scanned_count': response.get('ScannedCount', 0)
        })
        
    except Exception as e:
        logger.error(f"Error getting sentiment results: {str(e)}")
        return create_response(500, {'error': 'Failed to get results', 'message': str(e)})

def get_sentiment_summary(query_parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Get sentiment analysis summary statistics.
    
    Args:
        query_parameters: Query parameters for filtering
        
    Returns:
        dict: API response with summary
    """
    try:
        ny_tz = timezone(timedelta(hours=-5))  # EST (UTC-5)
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        # Get all items for summary calculation
        response = table.scan()
        items = response['Items']
        
        # Calculate summary statistics
        total_count = len(items)
        sentiment_counts = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0, 'MIXED': 0}
        sentiment_scores = {'Positive': 0, 'Negative': 0, 'Neutral': 0, 'Mixed': 0}
        
        for item in items:
            sentiment = item['sentiment']
            sentiment_counts[sentiment] += 1
            
            # Accumulate sentiment scores
            for score_type, score_value in item['sentiment_score'].items():
                sentiment_scores[score_type] += score_value
        
        # Calculate averages
        if total_count > 0:
            for score_type in sentiment_scores:
                sentiment_scores[score_type] = round(sentiment_scores[score_type] / total_count, 3)
        
        # Calculate percentages
        sentiment_percentages = {}
        for sentiment, count in sentiment_counts.items():
            sentiment_percentages[sentiment] = round((count / total_count) * 100, 1) if total_count > 0 else 0
        
        return create_response(200, convert_decimals_to_floats({
            'total_feedback_items': total_count,
            'sentiment_counts': sentiment_counts,
            'sentiment_percentages': sentiment_percentages,
            'average_sentiment_scores': sentiment_scores,
            'generated_at': datetime.now(ny_tz).isoformat()
        }))
        
    except Exception as e:
        logger.error(f"Error getting sentiment summary: {str(e)}")
        return create_response(500, {'error': 'Failed to get summary', 'message': str(e)})

def get_processed_files(query_parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Get list of processed files.
    
    Args:
        query_parameters: Query parameters for filtering
        
    Returns:
        dict: API response with file list
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        # Get unique object keys
        response = table.scan(
            ProjectionExpression='object_key, #timestamp',
            ExpressionAttributeNames={'#timestamp': 'timestamp'}
        )
        
        # Group by object key and get latest timestamp
        file_info = {}
        for item in response['Items']:
            object_key = item['object_key']
            timestamp = item['timestamp']
            
            if object_key not in file_info or timestamp > file_info[object_key]['last_processed']:
                file_info[object_key] = {
                    'object_key': object_key,
                    'last_processed': timestamp
                }
        
        # Convert to list and sort by last processed
        files = list(file_info.values())
        files.sort(key=lambda x: x['last_processed'], reverse=True)
        
        return create_response(200, {
            'files': files,
            'count': len(files)
        })
        
    except Exception as e:
        logger.error(f"Error getting processed files: {str(e)}")
        return create_response(500, {'error': 'Failed to get files', 'message': str(e)})

def get_sentiment_result_by_id(result_id: str) -> Dict[str, Any]:
    """
    Get specific sentiment result by ID.
    
    Args:
        result_id: Result ID
        
    Returns:
        dict: API response with result
    """
    try:
        if not result_id:
            return create_response(400, {'error': 'Result ID is required'})
        
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        response = table.get_item(Key={'id': result_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Result not found'})
        
        item = response['Item']
        
        return create_response(200, {
            'id': item['id'],
            'object_key': item['object_key'],
            'text': item['text'],
            'sentiment': item['sentiment'],
            'sentiment_score': item['sentiment_score'],
            'timestamp': item['timestamp'],
            'metadata': item.get('metadata', {})
        })
        
    except Exception as e:
        logger.error(f"Error getting sentiment result by ID: {str(e)}")
        return create_response(500, {'error': 'Failed to get result', 'message': str(e)})

def handle_file_upload(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle file upload request with multipart form data.
    
    Args:
        event: API Gateway event containing multipart form data
        
    Returns:
        dict: API response
    """
    try:
        logger.info("Processing file upload request")
        
        # Parse multipart form data
        content_type = event.get('headers', {}).get('content-type', '')
        
        if 'multipart/form-data' not in content_type:
            return create_response(400, {
                'error': 'Invalid content type',
                'message': 'Expected multipart/form-data'
            })
        
        # Parse the multipart body
        body = event.get('body', '')
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body).decode('utf-8')
        
        # Extract file from multipart data
        file_data = parse_multipart_data(body, content_type)
        
        if not file_data:
            return create_response(400, {
                'error': 'No file found',
                'message': 'No file was uploaded'
            })
        
        # Generate unique filename with New York timezone
        ny_tz = timezone(timedelta(hours=-5))  # EST (UTC-5)
        file_extension = get_file_extension(file_data['filename'])
        unique_filename = f"uploads/upload_{int(datetime.now(ny_tz).timestamp())}_{uuid.uuid4().hex[:8]}{file_extension}"
        
        # Upload file to S3
        s3_key = upload_file_to_s3(file_data['content'], unique_filename, file_data['content_type'])
        
        logger.info(f"File uploaded to S3: {s3_key}")
        
        return create_response(200, {
            'message': 'File uploaded successfully',
            'file_key': s3_key,
            'filename': file_data['filename'],
            'size': len(file_data['content']),
            'content_type': file_data['content_type']
        })
        
    except Exception as e:
        logger.error(f"Error handling file upload: {str(e)}")
        return create_response(500, {'error': 'Failed to handle upload', 'message': str(e)})

def parse_multipart_data(body: str, content_type: str) -> Optional[Dict[str, Any]]:
    """
    Parse multipart form data to extract file information.
    
    Args:
        body: Request body
        content_type: Content type header
        
    Returns:
        dict: File data or None if parsing fails
    """
    try:
        # Extract boundary from content type
        boundary = None
        for part in content_type.split(';'):
            part = part.strip()
            if part.startswith('boundary='):
                boundary = part.split('=')[1]
                break
        
        if not boundary:
            logger.error("No boundary found in content type")
            return None
        
        # Split body by boundary
        parts = body.split(f'--{boundary}')
        
        for part in parts:
            if 'filename=' in part:
                # Extract filename
                filename_start = part.find('filename="') + 10
                filename_end = part.find('"', filename_start)
                filename = part[filename_start:filename_end]
                
                # Extract content type
                content_type_start = part.find('Content-Type: ') + 14
                content_type_end = part.find('\r\n', content_type_start)
                file_content_type = part[content_type_start:content_type_end]
                
                # Extract file content (skip headers)
                content_start = part.find('\r\n\r\n') + 4
                content = part[content_start:]
                
                # Remove trailing boundary markers
                content = content.rstrip('\r\n--')
                
                return {
                    'filename': filename,
                    'content': content.encode('utf-8'),
                    'content_type': file_content_type
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error parsing multipart data: {str(e)}")
        return None

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: Original filename
        
    Returns:
        str: File extension with dot
    """
    if '.' in filename:
        return '.' + filename.split('.')[-1]
    return ''

def upload_file_to_s3(file_content: bytes, s3_key: str, content_type: str) -> str:
    """
    Upload file content to S3.
    
    Args:
        file_content: File content as bytes
        s3_key: S3 object key
        content_type: MIME type
        
    Returns:
        str: S3 object key
    """
    try:
        ny_tz = timezone(timedelta(hours=-5))  # EST (UTC-5)
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type,
            Metadata={
                'uploaded-by': 'api-handler',
                'upload-timestamp': datetime.now(ny_tz).isoformat()
            }
        )
        
        return s3_key
        
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        raise

def handle_text_feedback(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle single text feedback submission.
    
    Args:
        event: API Gateway event
        
    Returns:
        dict: API Gateway response
    """
    try:
        logger.info("Processing text feedback request")
        
        # Parse JSON body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if 'text' not in body or not body['text'].strip():
            return create_response(400, {
                'error': 'Missing text',
                'message': 'Text field is required'
            })
        
        text = body['text'].strip()
        
        # Validate text length
        if len(text) < 10:
            return create_response(400, {
                'error': 'Text too short',
                'message': 'Feedback text must be at least 10 characters long'
            })
        
        if len(text) > 5000:
            return create_response(400, {
                'error': 'Text too long',
                'message': 'Feedback text must be less than 5000 characters'
            })
        
        # Validate and extract rating
        rating = body.get('rating', 0)
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return create_response(400, {
                'error': 'Invalid rating',
                'message': 'Rating must be an integer between 1 and 5'
            })
        
        # Extract optional fields
        customer_info = body.get('customer_info', {})
        
        # Create feedback data structure
        ny_tz = timezone(timedelta(hours=-5))  # EST (UTC-5)
        feedback_data = [{
            'text': text,
            'metadata': {
                'rating': rating,
                'customer_info': customer_info,
                'source': 'single_feedback',
                'submitted_at': datetime.now(ny_tz).isoformat()
            }
        }]
        
        # Process feedback through sentiment analysis
        results = process_feedback_data(feedback_data)
        
        if not results:
            return create_response(500, {
                'error': 'Processing failed',
                'message': 'Failed to process feedback'
            })
        
        # Get the first (and only) result
        result = results[0]
        
        logger.info(f"Text feedback processed successfully: {result['sentiment']}")
        
        return create_response(200, {
            'message': 'Feedback submitted successfully',
            'feedback_id': result['id'],
            'sentiment': result['sentiment'],
            'confidence': result['confidence'],
            'rating': rating,
            'timestamp': result['timestamp']
        })
        
    except json.JSONDecodeError:
        return create_response(400, {
            'error': 'Invalid JSON',
            'message': 'Request body must be valid JSON'
        })
    except Exception as e:
        logger.error(f"Error processing text feedback: {str(e)}")
        return create_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })

def process_feedback_data(feedback_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process feedback data through sentiment analysis.
    
    Args:
        feedback_data: List of feedback items
        
    Returns:
        List[Dict]: Processed results with sentiment analysis
    """
    try:
        # Import the sentiment analysis function from sentiment processor
        # For now, we'll implement a simplified version here
        results = []
        
        for feedback_item in feedback_data:
            # Extract rating from metadata
            rating = feedback_item.get('metadata', {}).get('rating')
            
            # Analyze sentiment (pass rating if available)
            sentiment_result = analyze_sentiment_simple(feedback_item['text'], rating)
            
            # Generate unique ID
            ny_tz = timezone(timedelta(hours=-5))
            result_id = f"text_feedback_{int(datetime.now(ny_tz).timestamp())}_{uuid.uuid4().hex[:8]}"
            
            # Store in DynamoDB
            store_text_feedback_result(result_id, feedback_item, sentiment_result)
            
            # Add to results
            results.append({
                'id': result_id,
                'text': feedback_item['text'],
                'sentiment': sentiment_result['Sentiment'],
                'confidence': sentiment_result['SentimentScore'],
                'timestamp': datetime.now(ny_tz).isoformat(),
                'metadata': feedback_item.get('metadata', {})
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing feedback data: {str(e)}")
        return []

def analyze_sentiment_simple(text: str, rating: int = None) -> Dict[str, Any]:
    """
    Enhanced sentiment analysis function that considers both text and rating.
    
    Args:
        text: Feedback text
        rating: Numeric rating (1-5 stars)
    """
    try:
        # Simple rule-based sentiment analysis for text
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
            'difficult', 'hard', 'confusing', 'complicated', 'unreliable', 'unhelpful',
            'dont like', 'do not like', 'not good', 'not great', 'not happy',
            'not satisfied', 'not impressed', 'not recommend', 'not worth'
        ]
        
        # Convert to lowercase for comparison
        text_lower = text.lower()
        
        # Count positive and negative words/phrases
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for phrase in negative_words if phrase in text_lower)
        
        # Determine sentiment based on rating and text analysis
        if rating is not None:
            # Get text-based sentiment first
            text_sentiment = None
            if positive_count > negative_count:
                text_sentiment = 'POSITIVE'
            elif negative_count > positive_count:
                text_sentiment = 'NEGATIVE'
            else:
                text_sentiment = 'NEUTRAL'
            
            # Determine rating-based sentiment
            if rating <= 2:
                rating_sentiment = 'NEGATIVE'
                rating_confidence = 0.8
            elif rating == 3:
                rating_sentiment = 'NEUTRAL'
                rating_confidence = 0.7
            else:
                rating_sentiment = 'POSITIVE'
                rating_confidence = 0.8
            
            # Check for conflicts between rating and text
            if rating_sentiment != text_sentiment and abs(positive_count - negative_count) > 1:
                # Strong text sentiment conflicts with rating - trust text more
                if text_sentiment == 'NEGATIVE':
                    sentiment = 'NEGATIVE'
                    confidence = 0.75
                    sentiment_scores = {
                        'Positive': 0.1,
                        'Negative': confidence,
                        'Neutral': 0.1,
                        'Mixed': 0.05
                    }
                elif text_sentiment == 'POSITIVE':
                    sentiment = 'POSITIVE'
                    confidence = 0.75
                    sentiment_scores = {
                        'Positive': confidence,
                        'Negative': 0.1,
                        'Neutral': 0.1,
                        'Mixed': 0.05
                    }
                else:
                    sentiment = 'NEUTRAL'
                    confidence = 0.6
                    sentiment_scores = {
                        'Positive': 0.2,
                        'Negative': 0.2,
                        'Neutral': confidence,
                        'Mixed': 0.0
                    }
            else:
                # Rating and text agree, or weak text signal - trust rating
                sentiment = rating_sentiment
                confidence = rating_confidence
                if rating_sentiment == 'NEGATIVE':
                    sentiment_scores = {
                        'Positive': 0.05,
                        'Negative': confidence,
                        'Neutral': 0.1,
                        'Mixed': 0.0
                    }
                elif rating_sentiment == 'POSITIVE':
                    sentiment_scores = {
                        'Positive': confidence,
                        'Negative': 0.05,
                        'Neutral': 0.1,
                        'Mixed': 0.0
                    }
                else:
                    sentiment_scores = {
                        'Positive': 0.15,
                        'Negative': 0.15,
                        'Neutral': confidence,
                        'Mixed': 0.0
                    }
        else:
            # Fallback to text-based analysis if no rating
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
        return {
            'Sentiment': 'NEUTRAL',
            'SentimentScore': {
                'Positive': 0.33,
                'Negative': 0.33,
                'Neutral': 0.34,
                'Mixed': 0.0
            }
        }

def store_text_feedback_result(result_id: str, feedback_item: Dict[str, Any], 
                              sentiment_result: Dict[str, Any]) -> str:
    """
    Store text feedback result in DynamoDB.
    
    Args:
        result_id: Unique result ID
        feedback_item: Feedback item data
        sentiment_result: Sentiment analysis result
        
    Returns:
        str: Result ID
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        ny_tz = timezone(timedelta(hours=-5))
        
        # Prepare item for DynamoDB (convert floats to Decimals)
        item = {
            'id': result_id,
            'object_key': 'text_feedback',
            'text': feedback_item['text'],
            'sentiment': sentiment_result['Sentiment'],
            'sentiment_score': convert_floats_to_decimals(sentiment_result['SentimentScore']),
            'metadata': convert_floats_to_decimals(feedback_item.get('metadata', {})),
            'timestamp': datetime.now(ny_tz).isoformat(),
            'ttl': int((datetime.now().timestamp() + (365 * 24 * 60 * 60)))  # 1 year TTL
        }
        
        # Store in DynamoDB
        table.put_item(Item=item)
        
        logger.info(f"Stored text feedback result: {result_id}")
        
        # Send SNS notification for negative sentiment
        if sentiment_result['Sentiment'] == 'NEGATIVE':
            send_negative_feedback_alert(result_id, feedback_item['text'], sentiment_result)
        
        return result_id
        
    except Exception as e:
        logger.error(f"Error storing text feedback result: {str(e)}")
        raise

def send_negative_feedback_alert(result_id: str, feedback_text: str, sentiment_result: Dict[str, Any]) -> None:
    """
    Send SNS notification for negative single feedback.
    
    Args:
        result_id: Unique result ID
        feedback_text: The feedback text
        sentiment_result: Sentiment analysis result
    """
    try:
        if not SNS_TOPIC_ARN:
            logger.warning("SNS topic ARN not configured, skipping alert")
            return
        
        # Truncate feedback text for email
        display_text = feedback_text[:200] + "..." if len(feedback_text) > 200 else feedback_text
        
        message = f"""
        Negative sentiment detected in single customer feedback!
        
        Feedback ID: {result_id}
        Sentiment: {sentiment_result['Sentiment']}
        Confidence: {sentiment_result['SentimentScore'].get('Negative', 0):.2f}
        
        Feedback Text:
        "{display_text}"
        
        Timestamp: {datetime.now().isoformat()}
        
        Please review this feedback and take appropriate action.
        """
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Negative Sentiment Alert - Single Feedback ({result_id[:8]})",
            Message=message
        )
        
        logger.info(f"Sent negative sentiment alert for single feedback: {result_id}")
        
    except Exception as e:
        logger.error(f"Error sending negative feedback alert: {str(e)}")

def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create API Gateway response.
    
    Args:
        status_code: HTTP status code
        body: Response body
        
    Returns:
        dict: API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }
