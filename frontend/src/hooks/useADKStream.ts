/**
 * Custom React hook for consuming Server-Sent Events from the ADK backend
 * Replaces the LangGraph SDK's useStream hook
 */

import { useState, useRef, useCallback, useEffect } from 'react';

export interface Message {
  id: string;
  type: 'human' | 'ai';
  content: string;
}

export interface ActivityEvent {
  event: string;
  data: any;
}

export interface StreamState {
  isLoading: boolean;
  messages: Message[];
  activityEvents: ActivityEvent[];
  error: string | null;
}

export interface UseADKStreamProps {
  onMessage?: (message: Message) => void;
  onActivity?: (event: ActivityEvent) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
}

export interface StartStreamOptions {
  question: string;
  effort_level: 'low' | 'medium' | 'high';
  reasoning_model: string;
}

export function useADKStream(props: UseADKStreamProps = {}) {
  const { onMessage, onActivity, onError, onComplete } = props;
  
  const [state, setState] = useState<StreamState>({
    isLoading: false,
    messages: [],
    activityEvents: [],
    error: null,
  });
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  
  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);
  
  const startStream = useCallback(async (options: StartStreamOptions) => {
    try {
      // Clean up any existing connections
      cleanup();
      
      // Add human message immediately
      const humanMessage: Message = {
        type: "human",
        content: options.question,
        id: Date.now().toString(),
      };
      
      setState(prev => ({
        ...prev,
        isLoading: true,
        error: null,
        messages: [humanMessage],
        activityEvents: []
      }));
      
      // Create abort controller for cleanup
      abortControllerRef.current = new AbortController();
      
      // Make POST request to start streaming
      const response = await fetch('/api/adk-research-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
        signal: abortControllerRef.current.signal,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Create EventSource from response body
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body available');
      }
      
      const decoder = new TextDecoder();
      let buffer = '';
      
      const processStream = async () => {
        try {
          while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
              break;
            }
            
            // Decode chunk and add to buffer
            buffer += decoder.decode(value, { stream: true });
            
            // Process complete lines
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer
            
            for (const line of lines) {
              if (line.trim().startsWith('data: ')) {
                try {
                  const jsonStr = line.slice(6).trim();
                  if (jsonStr) {
                    const eventData = JSON.parse(jsonStr);
                    await handleEvent(eventData);
                  }
                } catch (parseError) {
                  console.warn('Failed to parse SSE data:', parseError);
                  console.warn('Problematic line:', line);
                }
              }
            }
          }
        } catch (error) {
          if (error instanceof Error && error.name !== 'AbortError') {
            console.error('Stream processing error:', error);
            handleError(error.message);
          }
        } finally {
          setState(prev => ({ ...prev, isLoading: false }));
        }
      };
      
      processStream();
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      handleError(errorMessage);
    }
  }, [cleanup, onMessage, onActivity, onError, onComplete]);
  
  const handleEvent = useCallback(async (eventData: any) => {
    const { event, data } = eventData;
    
    // Create activity event
    const activityEvent: ActivityEvent = { event, data };
    
    setState(prev => ({
      ...prev,
      activityEvents: [...prev.activityEvents, activityEvent]
    }));
    
    // Call activity callback
    if (onActivity) {
      onActivity(activityEvent);
    }
    
    // Handle specific event types
    switch (event) {
      case 'messages':
        // Skip duplicate human messages to prevent triple display
        if (data.type === 'human') {
          // Check if we already have this human message
          const isDuplicate = state.messages.some(msg => 
            msg.type === 'human' && msg.content === data.content
          );
          if (isDuplicate) {
            break; // Skip adding duplicate human message
          }
        }
        
        const message: Message = {
          id: data.id || `${data.type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          type: data.type || 'ai',
          content: data.content || data.answer || '',
        };
        
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, message]
        }));
        
        if (onMessage) {
          onMessage(message);
        }
        break;
        
      case 'error':
        handleError(data.error || 'Unknown error occurred');
        break;
        
      case '__end__':
        setState(prev => ({ ...prev, isLoading: false }));
        if (onComplete) {
          onComplete();
        }
        break;
        
      default:
        // Handle other events (generate_query, web_research, reflection, finalize_answer)
        break;
    }
  }, [onMessage, onActivity, onComplete]);
  
  const handleError = useCallback((error: string) => {
    setState(prev => ({
      ...prev,
      error,
      isLoading: false
    }));
    
    if (onError) {
      onError(error);
    }
  }, [onError]);
  
  const stopStream = useCallback(() => {
    cleanup();
    setState(prev => ({ ...prev, isLoading: false }));
  }, [cleanup]);
  
  // Cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);
  
  return {
    ...state,
    startStream,
    stopStream,
  };
}