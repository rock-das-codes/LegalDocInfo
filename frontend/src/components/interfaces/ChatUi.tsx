import React, { useState, useRef, useEffect } from 'react';
 import {  useMutation } from '@tanstack/react-query'; 
 import axios, { AxiosError } from 'axios';

 interface ApiErrorResponse {
  detail: string;
 }

 interface ChatBotProps {
  documentId: string;
 }

 const BotIcon = () => ( <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center font-bold text-white flex-shrink-0">AI</div> ); 
 const UserIcon = () => ( <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center font-bold text-white flex-shrink-0">You</div> );
  const SendIcon = () => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5"> <line x1="22" y1="2" x2="11" y2="13" /> <polygon points="22 2 15 22 11 13 2 9 22 2" /> </svg> );
   
 interface QuerySuccessResponse { answer: string; source_text: string; };
 
 
  interface Message { from: 'user' | 'bot'; text: string; };
export default function ChatBot({ documentId }: ChatBotProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // --- Mutation ---
  const queryMutation = useMutation<QuerySuccessResponse, AxiosError<ApiErrorResponse>, string>({
    mutationFn: (userMessage: string) => {
      return axios.post<QuerySuccessResponse>(
        'https://legaldocinfo.onrender.com/api/query',
        {
          document_id: documentId,
          query: userMessage, // ✅ match backend
        }
      ).then(res => res.data); // ✅ return data
    },
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { from: 'bot', text: data.answer }]);
    },
    onError: (error) => {
      const errorMsg = error.response?.data?.detail || error.message;
      setMessages((prev) => [...prev, { from: 'bot', text: `Error: ${errorMsg}` }]);
    },
  });

  const handleSendMessage = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const userMessage = inputValue.trim();
    if (!userMessage || queryMutation.isPending) return;

    setMessages((prev) => [...prev, { from: 'user', text: userMessage }]);
    setInputValue('');
    queryMutation.mutate(userMessage);
  };

  return (
    <div className="flex flex-col h-screen flex-grow bg-gray-900 text-white">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex items-start space-x-2 ${msg.from === 'user' ? 'justify-end' : ''}`}>
            {msg.from === 'bot' && <BotIcon />}
            <div className={`px-4 py-2 rounded-xl max-w-xs shadow-md ${msg.from === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-100'}`}>
              {msg.text}
            </div>
            {msg.from === 'user' && <UserIcon />}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSendMessage} className="p-4 flex items-center space-x-2 border-t border-gray-700">
        <input
          type="text"
          className="flex-1 px-4 py-2 rounded-lg bg-gray-800 text-white focus:outline-none"
          placeholder="Ask something..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
        />
        <button type="submit" className="p-2 bg-blue-600 rounded-full hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed" disabled={queryMutation.isPending}>
          <SendIcon />
        </button>
      </form>
    </div>
  );
}
