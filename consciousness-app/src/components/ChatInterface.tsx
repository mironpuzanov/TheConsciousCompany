import { useEffect, useRef, useState } from 'react';
import type { ChatMessage } from '../types/copilot';
import { Button } from './ui/button';
import ReactMarkdown from 'react-markdown';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isTyping: boolean;
  isListening?: boolean;
  onSendMessage?: (text: string) => void;
}

export function ChatInterface({ messages, isTyping, isListening = false, onSendMessage }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [inputText, setInputText] = useState('');

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const getEmotionEmoji = (emotion?: string) => {
    if (!emotion) return '';
    const emojiMap: Record<string, string> = {
      joy: '😊',
      sadness: '😢',
      anger: '😠',
      fear: '😨',
      anxiety: '😰',
      surprise: '😲',
      neutral: '😐',
    };
    return emojiMap[emotion.toLowerCase()] || '';
  };

  const handleSend = () => {
    if (inputText.trim() && onSendMessage) {
      onSendMessage(inputText.trim());
      setInputText('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Listening indicator */}
      {isListening && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-red-700 font-medium">🎤 Listening to microphone...</span>
        </div>
      )}

      {/* Messages container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-zinc-400 text-center space-y-2">
            <p className="text-lg">Ready to chat!</p>
            <p className="text-sm">Speak into your microphone or type a message below</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] rounded-lg px-4 py-3 ${
                  message.type === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-zinc-200 text-zinc-900'
                }`}
              >
                {/* User emotion indicator */}
                {message.type === 'user' && message.emotion && (
                  <div className="text-xs opacity-75 mb-1">
                    {getEmotionEmoji(message.emotion)} {message.emotion}
                  </div>
                )}

                {/* Message text */}
                {message.type === 'ai' ? (
                  <div className="prose prose-sm max-w-none prose-p:my-2 prose-strong:font-bold prose-strong:text-zinc-900">
                    <ReactMarkdown>{message.text}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap break-words">{message.text}</p>
                )}

                {/* Timestamp */}
                <div
                  className={`text-xs mt-1 ${
                    message.type === 'user' ? 'text-blue-100' : 'text-zinc-500'
                  }`}
                >
                  {new Date(message.timestamp * 1000).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-zinc-200 rounded-lg px-4 py-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce delay-75"></div>
                <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce delay-150"></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Text input area */}
      <div className="border-t border-zinc-200 p-4 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message here (or speak into microphone)..."
            className="flex-1 px-4 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <Button
            onClick={handleSend}
            disabled={!inputText.trim()}
            className="bg-blue-500 hover:bg-blue-600 text-white px-6"
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
