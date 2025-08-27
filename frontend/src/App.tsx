import React, { useState } from 'react';
import './App.css';
import ChatBot from './components/interfaces/ChatUi';
import { FileUpload } from './components/interfaces/FileUpload';

const Navbar: React.FC = () => (
  <nav className="bg-gray-800 p-4">
    <div className="container mx-auto">
      <span className="text-white text-xl font-bold">docMate</span>
    </div>
  </nav>
);

const LoadingScreen: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-900 text-white">
    <div className="text-center">
      <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-white mx-auto mb-4"></div>
      <p className="text-xl">Loading your document...</p>
    </div>
  </div>
);

const App: React.FC = () => {
  const [documentId, setDocumentId] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className=" ">
        {isLoading ? <LoadingScreen /> : !documentId ? <FileUpload setDocumentId={setDocumentId} setIsLoading={setIsLoading} /> : <ChatBot documentId={documentId} />}
      </main>
    </div>
  );
}

export default App;
