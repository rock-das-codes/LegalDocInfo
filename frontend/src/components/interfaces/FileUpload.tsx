import { useState } from "react";
import { FileInput, Label, Spinner, Button, TextInput, Alert } from "flowbite-react";
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import ArticleOutlinedIcon from '@mui/icons-material/ArticleOutlined';
import SendIcon from '@mui/icons-material/Send';

import { useMutation, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios, { type AxiosResponse } from 'axios';



export function FileUpload({documentId,setDocumentId}:any) {
  const [fileName, setFileName] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [documentsId, setDocumentsId] = useState<string | null>(null);

  const ALLOWED_FILE_TYPES = ["application/pdf", "text/plain"];

  // --- React Query Mutation ---
  const uploadMutation = useMutation<AxiosResponse<any>, any, File>({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);

      return axios.post("https://fuzzy-trout-94v9gjwqvvj2799v-8000.app.github.dev/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    },
    onSuccess: (response) => {
      console.log("Upload successful!", response.data);
      setDocumentId(response.data.document_id);
      setDocumentsId(response.data.document_id);
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || "An unexpected error occurred.";
      setErrorMessage(`Upload failed: ${errorMsg}`);
    },
  });

  const handleFile = (file: File | null) => {
    if (!file) return;
    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      setErrorMessage("Invalid file type. Please upload a PDF or TXT file.");
      uploadMutation.reset();
      return;
    }
    setErrorMessage("");
    setFileName(file.name);
    uploadMutation.mutate(file);
  };

  // --- Drag & Drop Handlers ---
  const handleDragEnter = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  // --- File Input Change Handler ---
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const renderIdleState = () => (
    <div className="flex w-full max-w-lg flex-col items-center">
      <h1 className="mb-6 text-2xl font-bold text-gray-200">Start by uploading your document</h1>
      {(uploadMutation.isError || errorMessage) && (
        <Alert
          color="failure"
          icon={() => <ErrorOutlineIcon className="h-5 w-5" />}
          className="mb-4"
        >
          <span className="font-medium">Error!</span>{" "}
          {errorMessage || "An error occurred."}
        </Alert>
      )}
      <Label
        htmlFor="dropzone-file"
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        className={`flex h-64 w-full cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed bg-gray-50 transition-colors duration-300 dark:border-gray-600 dark:bg-gray-700
          ${isDragging ? "border-blue-500 bg-blue-100 dark:bg-gray-800" : "border-gray-300 hover:bg-gray-100 dark:hover:border-gray-500 dark:hover:bg-gray-600"}`}
      >
        <div className="flex flex-col items-center justify-center pb-6 pt-5">
          <svg
            className="mb-4 h-8 w-8 text-gray-500 dark:text-gray-400"
            aria-hidden="true"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 20 16"
          >
            <path
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"
            />
          </svg>
          <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
            <span className="font-semibold">Click to upload</span> or drag and
            drop
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            PDF or TXT files only
          </p>
        </div>
        <FileInput
          id="dropzone-file"
          className="hidden"
          onChange={handleFileChange}
          accept=".pdf,.txt"
        />
      </Label>
    </div>
  );

  const renderUploadingState = () => (
    <div className="flex flex-col items-center gap-4 text-white">
      <p className="text-lg">Processing your document...</p>
      <Spinner aria-label="Processing file" size="xl" />
      <p className="text-md text-gray-400">{fileName}</p>
    </div>
  );

  const renderReadyState = () => (
    <div className="flex w-full max-w-2xl flex-col items-center gap-4 text-center">
      <div className="rounded-full bg-green-100 p-3 dark:bg-green-900">
        <ArticleOutlinedIcon className="h-8 w-8 text-green-500 dark:text-green-400" />
      </div>
      <h2 className="text-2xl font-semibold text-white">
        It's ready, let's start!
      </h2>
      <p className="text-md text-gray-400">{fileName}</p>
      <p className="text-xs text-gray-500">Document ID: {documentId}</p>
      <div className="mt-4 flex w-full items-center gap-2">
        <TextInput
          id="chat-input"
          placeholder="Ask something..."
          required
          className="flex-grow"
        />
        <Button>
          <SendIcon className="mr-2 h-5 w-5" />
          Start Chat
        </Button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen w-full items-center justify-center bg-gray-900 p-4">
      {uploadMutation.isLoading && renderUploadingState()}
      {uploadMutation.isSuccess && renderReadyState()}
      {(uploadMutation.isIdle || uploadMutation.isError) && renderIdleState()}
    </div>
  );
}
