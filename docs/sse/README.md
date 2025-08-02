# Server-Sent Events (SSE) Documentation

This document provides comprehensive documentation for the Server-Sent Events (SSE) functionality in the Solution Outline Assistant API, enabling real-time communication between the server and clients.

## Table of Contents

- [Overview](#overview)
- [Connection Management](#connection-management)
- [Event Types](#event-types)
- [Usage Examples](#usage-examples)
- [Client Implementation](#client-implementation)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

Server-Sent Events (SSE) provide a way for the server to push real-time updates to connected clients. This is particularly useful for:

- **LLM Response Streaming**: Real-time streaming of LLM-generated content
- **Solution Outline Reviews**: Live streaming of review comments and suggestions
- **Progress Updates**: Real-time progress indicators for long-running operations
- **Notifications**: Instant notifications about system events

### Key Features

- **Real-time Communication**: Instant server-to-client messaging
- **Automatic Reconnection**: Built-in reconnection handling
- **Event Types**: Structured event system with different message types
- **Client Management**: Automatic client registration and cleanup
- **Error Recovery**: Graceful error handling and recovery

## Connection Management

### Establishing a Connection

To establish an SSE connection, make a GET request to the SSE endpoint:

**Endpoint:** `GET /api/v1/sse`

**Query Parameters:**
- `client_type` (optional): Type of client for categorization purposes

**Example:**
```javascript
const eventSource = new EventSource('/api/v1/sse?client_type=web_client');
```

### Connection Response

Upon successful connection, you'll receive:

**Headers:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Cache-Control
```

**Initial Event:**
```
event: connected
data: {"client_id": "550e8400-e29b-41d4-a716-446655440000", "message": "Connected successfully", "timestamp": "2023-01-01T00:00:00Z"}
```

### Connection Lifecycle

1. **Connection Establishment**: Client connects to `/api/v1/sse`
2. **Client Registration**: Server assigns unique client ID and registers client
3. **Event Streaming**: Server sends events to client as they occur
4. **Heartbeat**: Periodic keep-alive messages (if implemented)
5. **Disconnection**: Client disconnects or connection is lost
6. **Cleanup**: Server automatically removes client from registry

### Connection Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `client_type` | string | "generic" | Client type for categorization |

## Event Types

All SSE events follow a structured format with event types and JSON data payloads.

### Standard Event Format

```
event: event_type
data: {"key": "value", "timestamp": "2023-01-01T00:00:00Z"}
```

### Core Event Types

#### 1. Connection Events

**`connected`** - Sent when client successfully connects
```
event: connected
data: {
  "client_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Connected successfully",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**`disconnected`** - Sent before connection closes
```
event: disconnected
data: {
  "message": "Connection closing",
  "reason": "client_disconnect",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

#### 2. LLM Streaming Events

**`llm_start`** - LLM processing begins
```
event: llm_start
data: {
  "message": "Starting LLM processing",
  "prompt_key": "solution_outline_generation",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**`llm_chunk`** - Streaming content chunk
```
event: llm_chunk
data: {
  "content": "This is a chunk of generated content...",
  "chunk_index": 1,
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**`llm_complete`** - LLM processing completed
```
event: llm_complete
data: {
  "message": "LLM processing complete",
  "total_chunks": 15,
  "total_tokens": 1250,
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**`llm_error`** - LLM processing error
```
event: llm_error
data: {
  "message": "LLM processing failed",
  "error": "Connection timeout",
  "error_code": "LLM_TIMEOUT",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

#### 3. Review Events

**`review_start`** - Solution outline review begins
```
event: review_start
data: {
  "message": "Starting solution outline review",
  "solution_outline_id": 123,
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**`review_comment`** - New review comment generated
```
event: review_comment
data: {
  "comment": "Consider adding more details about the database schema design.",
  "section": "Architecture",
  "severity": "medium",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**`review_complete`** - Review process completed
```
event: review_complete
data: {
  "message": "Review completed",
  "total_comments": 8,
  "solution_outline_id": 123,
  "timestamp": "2023-01-01T00:00:00Z"
}
```

#### 4. Progress Events

**`progress_update`** - Progress indicator for long operations
```
event: progress_update
data: {
  "operation": "document_generation",
  "progress": 65,
  "message": "Processing section 3 of 5",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

#### 5. System Events

**`system_notification`** - System-wide notifications
```
event: system_notification
data: {
  "type": "maintenance",
  "message": "System maintenance scheduled for 2023-01-02 02:00 UTC",
  "priority": "low",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**`error`** - General error events
```
event: error
data: {
  "message": "An error occurred",
  "error_code": "GENERAL_ERROR",
  "details": {"context": "additional error context"},
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Usage Examples

### Basic JavaScript Client

```javascript
// Establish SSE connection
const eventSource = new EventSource('/api/v1/sse?client_type=web_client');

// Handle connection events
eventSource.addEventListener('connected', function(event) {
    const data = JSON.parse(event.data);
    console.log('Connected with client ID:', data.client_id);
});

// Handle LLM streaming
eventSource.addEventListener('llm_start', function(event) {
    const data = JSON.parse(event.data);
    console.log('LLM processing started:', data.message);
    // Clear previous content
    document.getElementById('llm-output').innerHTML = '';
});

eventSource.addEventListener('llm_chunk', function(event) {
    const data = JSON.parse(event.data);
    // Append new content chunk
    document.getElementById('llm-output').innerHTML += data.content;
});

eventSource.addEventListener('llm_complete', function(event) {
    const data = JSON.parse(event.data);
    console.log('LLM processing completed:', data.message);
    // Show completion indicator
    document.getElementById('status').textContent = 'Complete';
});

// Handle errors
eventSource.addEventListener('error', function(event) {
    console.error('SSE error:', event);
});

// Handle connection errors
eventSource.onerror = function(event) {
    console.error('Connection error:', event);
    // Implement reconnection logic if needed
};

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    eventSource.close();
});
```

### React Hook Example

```javascript
import { useEffect, useState } from 'react';

function useSSE(url) {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState('connecting');

    useEffect(() => {
        const eventSource = new EventSource(url);

        eventSource.addEventListener('connected', (event) => {
            setConnectionStatus('connected');
            const data = JSON.parse(event.data);
            console.log('Connected:', data.client_id);
        });

        eventSource.addEventListener('llm_chunk', (event) => {
            const chunk = JSON.parse(event.data);
            setData(prevData => (prevData || '') + chunk.content);
        });

        eventSource.addEventListener('error', (event) => {
            const errorData = JSON.parse(event.data);
            setError(errorData.message);
        });

        eventSource.onerror = () => {
            setConnectionStatus('error');
            setError('Connection failed');
        };

        return () => {
            eventSource.close();
        };
    }, [url]);

    return { data, error, connectionStatus };
}

// Usage in component
function LLMStreamingComponent() {
    const { data, error, connectionStatus } = useSSE('/api/v1/sse');

    if (connectionStatus === 'connecting') {
        return <div>Connecting...</div>;
    }

    if (error) {
        return <div>Error: {error}</div>;
    }

    return (
        <div>
            <div>Status: {connectionStatus}</div>
            <div>Content: {data}</div>
        </div>
    );
}
```

### Python Client Example

```python
import requests
import json
import sseclient

def handle_sse_events():
    url = 'http://localhost:8000/api/v1/sse'
    
    try:
        response = requests.get(url, stream=True)
        client = sseclient.SSEClient(response)
        
        for event in client.events():
            if event.event == 'connected':
                data = json.loads(event.data)
                print(f"Connected with client ID: {data['client_id']}")
            
            elif event.event == 'llm_chunk':
                data = json.loads(event.data)
                print(data['content'], end='', flush=True)
            
            elif event.event == 'llm_complete':
                data = json.loads(event.data)
                print(f"\nCompleted: {data['message']}")
            
            elif event.event == 'error':
                data = json.loads(event.data)
                print(f"Error: {data['message']}")
                break
                
    except Exception as e:
        print(f"Connection error: {e}")

# Usage
handle_sse_events()
```

## Client Implementation

### Connection Management

#### Automatic Reconnection

```javascript
class SSEClient {
    constructor(url, options = {}) {
        this.url = url;
        this.options = options;
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectInterval = options.reconnectInterval || 1000;
        this.listeners = new Map();
    }

    connect() {
        this.eventSource = new EventSource(this.url);
        
        this.eventSource.onopen = () => {
            console.log('SSE connection opened');
            this.reconnectAttempts = 0;
        };

        this.eventSource.onerror = (event) => {
            console.error('SSE connection error:', event);
            this.handleReconnection();
        };

        // Add event listeners
        this.listeners.forEach((handler, eventType) => {
            this.eventSource.addEventListener(eventType, handler);
        });
    }

    handleReconnection() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnection attempt ${this.reconnectAttempts}`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectInterval * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    addEventListener(eventType, handler) {
        this.listeners.set(eventType, handler);
        if (this.eventSource) {
            this.eventSource.addEventListener(eventType, handler);
        }
    }

    close() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

// Usage
const sseClient = new SSEClient('/api/v1/sse', {
    maxReconnectAttempts: 10,
    reconnectInterval: 2000
});

sseClient.addEventListener('llm_chunk', (event) => {
    const data = JSON.parse(event.data);
    console.log('Received chunk:', data.content);
});

sseClient.connect();
```

### Event Buffering

```javascript
class BufferedSSEClient extends SSEClient {
    constructor(url, options = {}) {
        super(url, options);
        this.buffer = [];
        this.bufferSize = options.bufferSize || 100;
    }

    addEventListener(eventType, handler) {
        const bufferedHandler = (event) => {
            // Add to buffer
            this.buffer.push({
                type: eventType,
                data: event.data,
                timestamp: new Date().toISOString()
            });

            // Maintain buffer size
            if (this.buffer.length > this.bufferSize) {
                this.buffer.shift();
            }

            // Call original handler
            handler(event);
        };

        super.addEventListener(eventType, bufferedHandler);
    }

    getBuffer() {
        return [...this.buffer];
    }

    clearBuffer() {
        this.buffer = [];
    }
}
```

## Error Handling

### Common Error Scenarios

#### Connection Errors

```javascript
eventSource.onerror = function(event) {
    console.error('Connection error:', event);
    
    // Check connection state
    if (eventSource.readyState === EventSource.CONNECTING) {
        console.log('Reconnecting...');
    } else if (eventSource.readyState === EventSource.CLOSED) {
        console.log('Connection closed');
        // Implement manual reconnection
        setTimeout(() => {
            location.reload(); // Simple reconnection
        }, 5000);
    }
};
```

#### Event Parsing Errors

```javascript
eventSource.addEventListener('llm_chunk', function(event) {
    try {
        const data = JSON.parse(event.data);
        // Process data
        handleLLMChunk(data);
    } catch (error) {
        console.error('Failed to parse event data:', error);
        console.error('Raw data:', event.data);
    }
});
```

#### Server Error Events

```javascript
eventSource.addEventListener('error', function(event) {
    const errorData = JSON.parse(event.data);
    
    switch (errorData.error_code) {
        case 'LLM_TIMEOUT':
            showUserMessage('LLM service is temporarily unavailable. Please try again.');
            break;
        case 'RATE_LIMIT_EXCEEDED':
            showUserMessage('Too many requests. Please wait before trying again.');
            break;
        default:
            showUserMessage('An error occurred: ' + errorData.message);
    }
});
```

### Error Recovery Strategies

#### Exponential Backoff

```javascript
class ReconnectingSSE {
    constructor(url) {
        this.url = url;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
    }

    connect() {
        this.eventSource = new EventSource(this.url);
        
        this.eventSource.onerror = () => {
            this.eventSource.close();
            this.scheduleReconnect();
        };
    }

    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        
        setTimeout(() => {
            console.log(`Reconnection attempt ${this.reconnectAttempts}`);
            this.connect();
        }, this.reconnectDelay);

        // Exponential backoff
        this.reconnectDelay = Math.min(
            this.reconnectDelay * 2,
            this.maxReconnectDelay
        );
    }
}
```

## Best Practices

### Client-Side Best Practices

1. **Always Handle Errors**: Implement proper error handling for connection and parsing errors
2. **Implement Reconnection**: Use automatic reconnection with exponential backoff
3. **Buffer Management**: Implement event buffering for critical applications
4. **Resource Cleanup**: Always close connections when no longer needed
5. **User Feedback**: Provide clear feedback about connection status to users

### Server-Side Considerations

1. **Connection Limits**: Be aware of browser connection limits (typically 6 per domain)
2. **Memory Management**: Server automatically cleans up disconnected clients
3. **Event Ordering**: Events are sent in order, but network conditions may affect delivery
4. **Heartbeat**: Consider implementing periodic heartbeat events for long-lived connections

### Performance Optimization

1. **Event Filtering**: Only send relevant events to specific clients
2. **Compression**: Use gzip compression for event streams
3. **Batching**: Batch small events together when appropriate
4. **Connection Pooling**: Reuse connections when possible

## Troubleshooting

### Common Issues

#### Connection Not Establishing

**Symptoms**: EventSource fails to connect or immediately closes

**Solutions**:
- Check network connectivity
- Verify server is running and accessible
- Check for CORS issues in browser console
- Ensure proper URL format

#### Events Not Received

**Symptoms**: Connection established but no events received

**Solutions**:
- Check server logs for errors
- Verify event generation on server side
- Check for client-side event listener registration
- Ensure proper event format on server

#### Frequent Disconnections

**Symptoms**: Connection drops frequently

**Solutions**:
- Check network stability
- Implement proper reconnection logic
- Verify server-side connection management
- Check for proxy/firewall interference

#### Memory Leaks

**Symptoms**: Browser memory usage increases over time

**Solutions**:
- Properly close EventSource connections
- Remove event listeners when no longer needed
- Implement event buffer size limits
- Clear references to prevent memory retention

### Debugging Tools

#### Browser Developer Tools

```javascript
// Enable SSE debugging
const eventSource = new EventSource('/api/v1/sse');

// Log all events
eventSource.onmessage = function(event) {
    console.log('SSE Event:', {
        type: event.type,
        data: event.data,
        lastEventId: event.lastEventId,
        timestamp: new Date().toISOString()
    });
};

// Monitor connection state
setInterval(() => {
    console.log('SSE State:', {
        readyState: eventSource.readyState,
        url: eventSource.url
    });
}, 5000);
```

#### Server-Side Logging

Check server logs for SSE-related messages:
- Connection establishment/termination
- Event generation and sending
- Error conditions
- Client management operations

### Testing SSE Functionality

#### Manual Testing with curl

```bash
# Test SSE endpoint
curl -N -H "Accept: text/event-stream" http://localhost:8000/api/v1/sse

# Test with client type
curl -N -H "Accept: text/event-stream" "http://localhost:8000/api/v1/sse?client_type=test"
```

#### Automated Testing

```javascript
// Jest test example
test('SSE connection and event handling', (done) => {
    const eventSource = new EventSource('/api/v1/sse');
    
    eventSource.addEventListener('connected', (event) => {
        const data = JSON.parse(event.data);
        expect(data.client_id).toBeDefined();
        expect(data.message).toBe('Connected successfully');
        eventSource.close();
        done();
    });
    
    eventSource.onerror = (error) => {
        eventSource.close();
        done(error);
    };
});
```

## Security Considerations

### Authentication
Currently, SSE connections do not require authentication. In production environments, consider implementing:
- Token-based authentication
- Session validation
- Rate limiting per client

### Data Validation
- Always validate event data on the client side
- Sanitize any content before displaying to users
- Be cautious with eval() or similar functions on event data

### Resource Protection
- Implement connection limits per client
- Monitor for abuse patterns
- Use appropriate timeouts for idle connections

For more information about the API endpoints that work with SSE, see the [API Reference](../api/README.md).